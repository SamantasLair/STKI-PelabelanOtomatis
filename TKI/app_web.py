import os
import sys
import re
import sqlite3
from TKI.database import DBConnection, execute_query
import json
import numpy as np
import pandas as pd
import math
import threading
from functools import lru_cache
from flask import Flask, render_template, jsonify, request, redirect

# Konfigurasi Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
ONNX_DIR = os.path.join(ROOT_DIR, "STKI", "onnx_model")
ONNX_FILE = os.path.join(ONNX_DIR, "multi_label_model.onnx")
DB_PATH = os.path.join(ROOT_DIR, "academic_metadata.db")
DB_REAL_PATH = os.path.join(ROOT_DIR, "academic_demo_real.db")
MEMORY_DIR = os.path.join(ROOT_DIR, "_memory")

app = Flask(__name__, 
            template_folder=os.path.join(ROOT_DIR, "_UIUX"), 
            static_folder=os.path.join(ROOT_DIR, "_UIUX"),
            static_url_path="/")

# State Sistem Aktif (Default)
DB_DIR = os.path.join(ROOT_DIR, "_databases")
os.makedirs(DB_DIR, exist_ok=True)

def get_available_domains():
    domains = []
    master_path = os.path.join(DB_DIR, "stki_master.db")
    if os.path.exists(master_path):
        try:
            conn = DBConnection(master_path)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tb_docs_%'")
            for row in c.fetchall():
                domains.append(row[0].replace('tb_docs_', ''))
            conn.close()
        except:
            pass
    if not domains:
        domains = ["default"]
    return domains

def get_active_domain():
    state_file = os.path.join(DB_DIR, "active_db.txt")
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                target = f.read().strip()
                if target in get_available_domains():
                    return target
        except:
            pass
    return get_available_domains()[0]


def set_active_domain(target):
    state_file = os.path.join(DB_DIR, "active_db.txt")
    try:
        with open(state_file, 'w') as f:
            f.write(target)
    except Exception as e:
        print(f"Error saving state: {e}")

active_domain = get_active_domain()
MASTER_DB_PATH = os.path.join(DB_DIR, "stki_master.db")
if not os.path.exists(MASTER_DB_PATH):
    open(MASTER_DB_PATH, 'a').close()

# Taksonomi Dinamis (Diload dari SQLite)
# TAXONOMY_FILE deprecated

# In-Memory Semantic Caching
DB_EMBEDDING_CACHE = {}

# Global State for Taxonomy Generation Progress
TAXONOMY_PROGRESS = {
    "status": "idle",
    "stage": "",
    "current": 0,
    "total": 0
}

@app.route("/api/taxonomy/progress", methods=["GET"])
def get_taxonomy_progress():
    return jsonify(TAXONOMY_PROGRESS)

@app.before_request
def sync_global_db_state():
    global active_domain, TAXONOMY, DB_EMBEDDING_CACHE
    current_domain = get_active_domain()
    if 'active_domain' not in globals() or active_domain != current_domain:
        active_domain = current_domain
        TAXONOMY = load_taxonomy(active_domain)
        DB_EMBEDDING_CACHE = {}

def get_db_embedding(active_domain, doc_id, emb_str):
    cache_key = (active_domain, doc_id)
    if cache_key not in DB_EMBEDDING_CACHE:
        DB_EMBEDDING_CACHE[cache_key] = np.array(json.loads(emb_str))
    return DB_EMBEDDING_CACHE[cache_key]

def load_taxonomy(domain):
    tax = {"Layer_1_Domain": [], "Layer_2_Detail": [], "threshold_l1": 0.50, "threshold_l2": 0.55, "metrics": None}
    try:
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS tb_tax_{domain} (id INTEGER PRIMARY KEY AUTOINCREMENT, layer TEXT, name TEXT UNIQUE)")
        c.execute(f"CREATE TABLE IF NOT EXISTS tb_set_{domain} (key TEXT PRIMARY KEY, value TEXT)")
        conn.commit()
        
        c.execute(f"SELECT name FROM tb_tax_{domain} WHERE layer='Layer_1_Domain'")
        tax["Layer_1_Domain"] = [row[0] for row in c.fetchall()]
        
        c.execute(f"SELECT name FROM tb_tax_{domain} WHERE layer='Layer_2_Detail'")
        tax["Layer_2_Detail"] = [row[0] for row in c.fetchall()]
        
        c.execute(f"SELECT key, value FROM tb_set_{domain}")
        for k, v in c.fetchall():
            if k in ["threshold_l1", "threshold_l2"]:
                tax[k] = float(v)
            elif k == "last_metrics":
                try: tax["metrics"] = json.loads(v)
                except: pass
        conn.close()
    except Exception as e:
        print(f"Error loading taxonomy DB: {e}")
        
    if not tax["Layer_1_Domain"]: tax["Layer_1_Domain"] = ["Umum"]
    if not tax["Layer_2_Detail"]: tax["Layer_2_Detail"] = ["Tidak Terklasifikasi"]
    return tax

def save_setting(db_path, key, value):
    try:
        conn = DBConnection(db_path, timeout=15)
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS tb_set_{active_domain} (key TEXT PRIMARY KEY, value TEXT)")
        c.execute(f"INSERT OR REPLACE INTO tb_set_{active_domain} (key, value) VALUES (?, ?)", (key, str(value)))
        conn.commit()
        conn.close()
        global TAXONOMY
        try:
            TAXONOMY[key] = float(value)
        except:
            TAXONOMY[key] = value
    except Exception as e:
        print(f"Error saving setting: {e}")

def save_taxonomy(db_type, taxonomy_dict):
    try:
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS tb_tax_{db_type} (id INTEGER PRIMARY KEY AUTOINCREMENT, layer TEXT, name TEXT UNIQUE)")
        c.execute(f"DELETE FROM tb_tax_{db_type}")
        
        for l1 in taxonomy_dict.get("Layer_1_Domain", []):
            try:
                c.execute(f"INSERT INTO tb_tax_{db_type} (layer, name) VALUES (?, ?)", ("Layer_1_Domain", l1))
            except sqlite3.IntegrityError:
                pass
                
        for l2 in taxonomy_dict.get("Layer_2_Detail", []):
            try:
                c.execute(f"INSERT INTO tb_tax_{db_type} (layer, name) VALUES (?, ?)", ("Layer_2_Detail", l2))
            except sqlite3.IntegrityError:
                pass
                
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error saving taxonomy DB: {e}")

TAXONOMY = load_taxonomy(active_domain)

import datetime
import traceback

ERROR_LOG_FILE = os.path.join(ROOT_DIR, "_memory", "system_error.log")

def log_error(system_name, error_msg, exc=None):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [SYSTEM: {system_name}] ERROR: {error_msg}\n"
    if exc:
        log_entry += f"TRACE:\n{traceback.format_exc()}\n"
    try:
        # Buat folder _memory jika belum ada
        os.makedirs(os.path.dirname(ERROR_LOG_FILE), exist_ok=True)
        with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except:
        pass

# Inisialisasi ONNX Engine
import onnxruntime as ort
from tokenizers import Tokenizer

session = None
tokenizer = None
v_null = None

def extract_key_sentences(text, num_sentences=5):
    raw_sentences = re.split(r'(?<=[.!?])\s+|\n+', text)
    sentences = []
    seen = set()
    for s in raw_sentences:
        s_clean = s.strip()
        if len(s_clean) > 15 and s_clean.lower() not in seen:
            sentences.append(s_clean)
            seen.add(s_clean.lower())
    if len(sentences) <= num_sentences:
        return text
    words_per_sentence = [set(re.findall(r'\b\w+\b', s.lower())) for s in sentences]
    num_s = len(sentences)
    sim_matrix = np.zeros((num_s, num_s))
    for i in range(num_s):
        for j in range(i + 1, num_s):
            w_i, w_j = words_per_sentence[i], words_per_sentence[j]
            if not w_i or not w_j:
                continue
            intersect = len(w_i.intersection(w_j))
            if intersect == 0:
                continue
            denom = np.log(len(w_i)) + np.log(len(w_j)) + 1.0
            sim_matrix[i, j] = intersect / denom
            sim_matrix[j, i] = sim_matrix[i, j]
    scores = np.ones(num_s)
    damping = 0.85
    row_sums = sim_matrix.sum(axis=1)
    for idx in range(num_s):
        if row_sums[idx] > 0:
            sim_matrix[idx, :] /= row_sums[idx]
        else:
            sim_matrix[idx, :] = 0.0
    for _ in range(15):
        new_scores = (1.0 - damping) + damping * np.dot(sim_matrix.T, scores)
        if np.allclose(scores, new_scores, atol=1e-4):
            scores = new_scores
            break
        scores = new_scores
    top_indices = np.argsort(scores)[::-1][:num_sentences]
    return " ".join([sentences[idx] for idx in sorted(top_indices)])

@lru_cache(maxsize=2000)
def get_onnx_embedding(text):
    if session is None or tokenizer is None:
        return np.zeros(384)
    distilled_text = extract_key_sentences(text, num_sentences=5)
    
    # Encode with tokenizers (fast rust implementation)
    encoded = tokenizer.encode(distilled_text.lower())
    input_ids = np.array([encoded.ids], dtype=np.int64)
    attention_mask = np.array([encoded.attention_mask], dtype=np.int64)
    
    outputs = session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
    
    # [FIXED] Ekstraksi Embedding Menggunakan Mean Pooling (Standard Sentence-Transformers)
    # Karena model yang di-export adalah base_model (feature extractor), outputnya adalah last_hidden_state (1, seq_len, hidden_size)
    last_hidden_state = outputs[0]
    attention_mask_expanded = np.expand_dims(attention_mask, axis=-1)
    sum_embeddings = np.sum(last_hidden_state * attention_mask_expanded, axis=1)
    sum_mask = np.clip(np.sum(attention_mask_expanded, axis=1), a_min=1e-9, a_max=None)
    sentence_embedding = (sum_embeddings / sum_mask)[0]
    
    return sentence_embedding


def init_onnx_engine():
    global session, tokenizer
    if not os.path.exists(ONNX_FILE):
        return False
    try:
        session = ort.InferenceSession(ONNX_FILE, providers=['CPUExecutionProvider'])
        tokenizer = Tokenizer.from_file(os.path.join(ONNX_DIR, "tokenizer.json"))
        tokenizer.enable_padding(length=256)
        tokenizer.enable_truncation(max_length=256)
        return True
    except Exception as e:
        print(f"Error loading ONNX engine: {e}")
        return False

onnx_ready = init_onnx_engine()


def get_cosine_similarity(v1, v2):
    # [FIXED] Pure Cosine Similarity
    # Pemusnahan v_null thresholding yang terbukti memicu Collapse Thresholding
    # di mana seluruh dokumen mendapatkan kemiripan sama persis (contoh: 86.3%).
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(np.dot(v1, v2) / (norm_v1 * norm_v2))

def has_keyword(text_lower, keyword):
    if len(keyword) <= 5:
        pattern = rf"\b{re.escape(keyword)}\b"
        return bool(re.search(pattern, text_lower))
    else:
        return keyword in text_lower


# Class BM25 untuk Leksikal Retrieval
class BM25:
    def __init__(self, corpus, b=0.75, k1=1.5):
        self.b = b
        self.k1 = k1
        self.corpus_size = len(corpus)
        self.avgdl = sum(len(d) for d in corpus) / self.corpus_size if self.corpus_size > 0 else 1.0
        self.doc_freqs = []
        self.idf = {}
        self.doc_lens = []
        
        for doc in corpus:
            words = doc.lower().split()
            self.doc_lens.append(len(words))
            freqs = {}
            for w in words:
                freqs[w] = freqs.get(w, 0) + 1
            self.doc_freqs.append(freqs)
            
            for w in freqs:
                self.idf[w] = self.idf.get(w, 0) + 1
                
        for w, df in self.idf.items():
            self.idf[w] = np.log((self.corpus_size - df + 0.5) / (df + 0.5) + 1.0)
            
    def get_score(self, query_words, doc_idx):
        score = 0.0
        doc_freq = self.doc_freqs[doc_idx]
        doc_len = self.doc_lens[doc_idx]
        for w in query_words:
            if w in doc_freq:
                freq = doc_freq[w]
                idf_val = self.idf.get(w, 0.0)
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / self.avgdl))
                score += idf_val * (numerator / denominator)
        return score

# State Thread Relabeling Ulang
relabel_progress = {"status": "idle", "current": 0, "total": 0, "percentage": 0}

def async_relabel_task(db_path, tax_layer1, tax_layer2):
    global relabel_progress
    try:
        relabel_progress["status"] = "running"
        conn = DBConnection(db_path, timeout=15)
        cursor = conn.cursor()
        cursor.execute(f"SELECT id, content FROM tb_docs_{active_domain}")
        rows = cursor.fetchall()
        
        if not rows:
            relabel_progress["status"] = "failed"
            conn.close()
            return
            
        total = len(rows)
        relabel_progress["total"] = total
        
        for idx, (doc_id, content) in enumerate(rows):
            emb = get_onnx_embedding(content)
            text_lower = content.lower()
            
            # 1. Predict Layer 2
            l2_raw_sims = []
            for label in tax_layer2:
                lbl_vector = get_onnx_embedding(label)
                sim = get_cosine_similarity(emb, lbl_vector)
                l2_raw_sims.append(sim)
                
            # [FIXED] SOFT LEXICAL GATEKEEPER dengan Stop-Word/IDF Penalty
            stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta", "domain", "adalah", "merupakan", "yaitu", "yakni", "tentang", "terkait", "hal", "pasal", "undang", "nomor", "tahun", "ayat", "huruf", "angka", "bahwa", "oleh", "karena", "sebab", "tersebut", "tidak", "bisa", "akan", "dapat", "menjadi"}
            for i, label in enumerate(tax_layer2):
                text_words = set(text_lower.split())
                label_words = set(label.lower().split())
                
                # Hitung bobot irisan, abaikan stop words
                overlap_weight = 0.0
                for w in text_words.intersection(label_words):
                    if w not in stop_words:
                        overlap_weight += 1.0
                    else:
                        overlap_weight += 0.05 # Penalti drastis untuk stop word
                
                if overlap_weight > 0.5:
                    # Tidak mem-boost secara agresif untuk mencegah saturasi 100%
                    # Hanya menjaga nilai Base Cosine Similarity murni
                    l2_raw_sims[i] = l2_raw_sims[i] * 1.0 
                else:
                    # Penalti bagi yang tidak ada irisan signifikan
                    l2_raw_sims[i] = l2_raw_sims[i] * 0.80
            
            # Ambil threshold dinamis
            dyn_t2 = float(TAXONOMY.get("threshold_l2", 0.55))
            for i in range(len(l2_raw_sims)):
                if l2_raw_sims[i] < dyn_t2: 
                    l2_raw_sims[i] = 0.0
            
            assigned_l2 = []
            for i, sim in enumerate(l2_raw_sims):
                if sim > 0.0:
                    assigned_l2.append(tax_layer2[i])
                    
            if not assigned_l2:
                assigned_l2 = ["Tidak Terklasifikasi"]

            # 2. Predict Layer 1
            l1_raw_sims = []
            for label in tax_layer1:
                lbl_vector = get_onnx_embedding(label)
                sim = get_cosine_similarity(emb, lbl_vector)
                l1_raw_sims.append(sim)
                
            # Dynamic Keyword Boost
            # [FIXED] Menghapus Propagasi Layer 2 ke Layer 1 (+0.10)
            # Prediksi Layer 1 harus independen berdasar Dense Vector.
            
            # [FIXED] SOFT LEXICAL GATEKEEPER dengan Stop-Word/IDF Penalty
            stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta", "domain", "adalah", "merupakan", "yaitu", "yakni", "tentang", "terkait", "hal", "pasal", "undang", "nomor", "tahun", "ayat", "huruf", "angka", "bahwa", "oleh", "karena", "sebab", "tersebut", "tidak", "bisa", "akan", "dapat", "menjadi"}
            for i, label in enumerate(tax_layer1):
                text_words = set(text_lower.split())
                label_words = set(label.lower().split())
                
                overlap_weight = 0.0
                for w in text_words.intersection(label_words):
                    if w not in stop_words:
                        overlap_weight += 1.0
                    else:
                        overlap_weight += 0.05
                        
                if overlap_weight > 0.5:
                    l1_raw_sims[i] = l1_raw_sims[i] * 1.0
                else:
                    l1_raw_sims[i] = l1_raw_sims[i] * 0.80
            
            # Ambil threshold dinamis
            dyn_t1 = float(TAXONOMY.get("threshold_l1", 0.50))
            for i in range(len(l1_raw_sims)):
                if l1_raw_sims[i] < dyn_t1: 
                    l1_raw_sims[i] = 0.0
                
            assigned_l1 = []
            for i, sim in enumerate(l1_raw_sims):
                if sim > 0.0:
                    assigned_l1.append(tax_layer1[i])
                    
            if not assigned_l1:
                assigned_l1 = ["Tidak Terklasifikasi"]
            
            predicted_labels = list(set(assigned_l1 + assigned_l2))
            cursor.execute(f"UPDATE tb_docs_{active_domain} SET labels = ? WHERE id = ?", (json.dumps(predicted_labels), doc_id))
            
            relabel_progress["current"] = idx + 1
            relabel_progress["percentage"] = int(((idx + 1) / total) * 100)
            
        conn.commit()
        conn.close()
        relabel_progress["status"] = "success"
    except Exception as e:
        print(f"Error in async relabeling: {e}")
        relabel_progress["status"] = "failed"

# --- FLASK ENDPOINTS ---

@app.route("/")
def index():
    return redirect("/stki")

@app.route("/stki")
def stki_view():
    return render_template("stki/index.html")

@app.route("/ds")
def ds_view():
    return render_template("ds/index.html")

@app.route("/api/documents", methods=["GET"])
def get_documents():
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        filter_type = request.args.get('filter', 'all')
        
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        cursor = conn.cursor()
        
        import time
        t_start = time.time()
        
        cursor.execute(f"PRAGMA table_info(tb_docs_{active_domain})")
        cols = [col[1] for col in cursor.fetchall()]
        has_filename = 'filename' in cols
        filename_col = "filename" if has_filename else "id as filename"
        
        if filter_type == 'all':
            cursor.execute(f"SELECT COUNT(id) FROM tb_docs_{active_domain}")
            total_docs = cursor.fetchone()[0]
            offset = (page - 1) * limit
            cursor.execute(f"SELECT id, {filename_col}, labels, content FROM tb_docs_{active_domain} ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset))
            rows = cursor.fetchall()
        else:
            # [BIG DATA DOCTRINE] C-Engine JSON1 Offloading (Zero Python RAM Allocation)
            if filter_type == 'outlier':
                count_query = f"""
                    SELECT COUNT(id) FROM tb_docs_{active_domain} 
                    WHERE labels IS NULL OR labels = '[]' OR json_array_length(labels) = 0 
                    OR EXISTS (SELECT 1 FROM json_each(tb_docs_{active_domain}.labels) WHERE json_each.value = 'Tidak Terklasifikasi')
                """
                data_query = f"""
                    SELECT id, {filename_col}, labels, content FROM tb_docs_{active_domain} 
                    WHERE labels IS NULL OR labels = '[]' OR json_array_length(labels) = 0 
                    OR EXISTS (SELECT 1 FROM json_each(tb_docs_{active_domain}.labels) WHERE json_each.value = 'Tidak Terklasifikasi')
                    ORDER BY id DESC LIMIT ? OFFSET ?
                """
            elif filter_type == 'overlap':
                count_query = f"""
                    SELECT COUNT(id) FROM tb_docs_{active_domain} 
                    WHERE json_array_length(labels) > 1 
                    AND NOT EXISTS (SELECT 1 FROM json_each(tb_docs_{active_domain}.labels) WHERE json_each.value = 'Tidak Terklasifikasi')
                """
                data_query = f"""
                    SELECT id, {filename_col}, labels, content FROM tb_docs_{active_domain} 
                    WHERE json_array_length(labels) > 1 
                    AND NOT EXISTS (SELECT 1 FROM json_each(tb_docs_{active_domain}.labels) WHERE json_each.value = 'Tidak Terklasifikasi')
                    ORDER BY id DESC LIMIT ? OFFSET ?
                """
            elif filter_type.startswith('label_'):
                target_label = filter_type[6:] # Menghilangkan prefix "label_"
                count_query = f"""
                    SELECT COUNT(id) FROM tb_docs_{active_domain} 
                    WHERE EXISTS (SELECT 1 FROM json_each(tb_docs_{active_domain}.labels) WHERE json_each.value = ?)
                """
                data_query = f"""
                    SELECT id, {filename_col}, labels, content FROM tb_docs_{active_domain} 
                    WHERE EXISTS (SELECT 1 FROM json_each(tb_docs_{active_domain}.labels) WHERE json_each.value = ?)
                    ORDER BY id DESC LIMIT ? OFFSET ?
                """
                cursor.execute(count_query, (target_label,))
                total_docs = cursor.fetchone()[0]
                offset = (page - 1) * limit
                cursor.execute(data_query, (target_label, limit, offset))
                rows = cursor.fetchall()
            
            if not filter_type.startswith('label_'):
                cursor.execute(count_query)
                total_docs = cursor.fetchone()[0]
                offset = (page - 1) * limit
                cursor.execute(data_query, (limit, offset))
                rows = cursor.fetchall()
                
        conn.close()
        
        docs = []
        for r in rows:
            docs.append({
                "id": r[0],
                "filename": r[1],
                "labels": json.loads(r[2]) if r[2] else [],
                "content": r[3]
            })
            
        total_pages = math.ceil(total_docs / limit) if total_docs > 0 else 1
        t_end = time.time()
        elapsed_ms = round((t_end - t_start) * 1000, 2)
        
        return jsonify({
            "status": "success", 
            "documents": docs,
            "total": total_docs,
            "page": page,
            "limit": limit,
            "total_pages": total_pages,
            "debug_time_ms": elapsed_ms
        })
    except Exception as e:
        log_error("DB Explorer", f"Gagal memuat dokumen (Pagination): {str(e)}", exc=True)
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/status", methods=["GET"])
def get_status():
    global active_domain, MASTER_DB_PATH, TAXONOMY
    
    conn = DBConnection(MASTER_DB_PATH, timeout=15)
    c = conn.cursor()
    # Pastikan tabel polimorfik dokumen terbuat jika belum ada
    c.execute(f'''
        CREATE TABLE IF NOT EXISTS tb_docs_{active_domain} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            content TEXT,
            labels TEXT,
            embedding TEXT
        )
    ''')
    conn.commit()
    
    c.execute(f"SELECT COUNT(*) FROM tb_docs_{active_domain}")
    total_docs = c.fetchone()[0]
    conn.close()
    
    # Hitung Rice Rule optimal X
    optimal_x = math.ceil(2 * (total_docs ** (1/3))) if total_docs > 0 else 0
    
    # [ANTI-OOM & MEMORY SAFE FIRST] 
    # Alih-alih melooping json.loads() pada puluhan ribu row dari f"SELECT labels FROM tb_docs_{active_domain}", 
    # kita hitung O(1) dari TAXONOMY memory.
    actual_labels_count = len(TAXONOMY.get("Layer_1_Domain", [])) + len(TAXONOMY.get("Layer_2_Detail", []))
                
    db_names = {
        "akademik": "Akademik Kampus",
        "politik": "Politik & Regulasi",
        "ekonomi": "Ekonomi Makro & Mikro (Demo Kontaminasi)",
        "bisnis": "Peraturan Bisnis & Korporat",
        "etika": "Etika & Hukum Hak Asasi",
        "academic_demo_real": "Teknologi & Komputer (Demo Real)"
    }
    db_name = db_names.get(active_domain, "Domain: " + active_domain)
    
    return jsonify({
        "active_db": db_name,
        "db_type": active_domain,
        "total_docs": total_docs,
        "optimal_labels_count": optimal_x,
        "actual_labels_count": actual_labels_count,
        "taxonomy": TAXONOMY
    })

@app.route("/api/switch_db", methods=["POST"])
def switch_db():
    global active_domain, TAXONOMY, DB_EMBEDDING_CACHE
    data = request.get_json()
    target = data.get("db_type", "")
    
    if target in get_available_domains():
        set_active_domain(target)
        active_domain = target
        TAXONOMY = load_taxonomy(active_domain)
        DB_EMBEDDING_CACHE = {} # Reset cache
        return jsonify({"status": "success", "message": f"Berhasil dialihkan ke Domain {target}"})
    return jsonify({"status": "error", "message": "Domain tidak ditemukan."})

@app.route("/api/ledgers", methods=["GET"])
def get_ledgers():
    domains = get_available_domains()
    return jsonify({"status": "success", "ledgers": domains, "active": active_domain})

@app.route("/api/ledgers/create", methods=["POST"])
def create_ledger():
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"status": "error", "message": "Nama domain tidak boleh kosong."})
    
    name = "".join(c for c in name if c.isalnum() or c == '_').lower()
    
    if name in get_available_domains():
        return jsonify({"status": "error", "message": "Domain dengan nama ini sudah ada."})
    
    try:
        load_taxonomy(name) # Ini akan membuat tabel otomatis
        return jsonify({"status": "success", "message": f"Domain {name} berhasil dibuat.", "ledgers": get_available_domains()})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/ledgers/rename", methods=["POST"])
def rename_ledger():
    global active_domain
    data = request.get_json()
    old_name = data.get("old_name", "").strip()
    new_name = data.get("new_name", "").strip()
    
    new_name = "".join(c for c in new_name if c.isalnum() or c == '_').lower()
        
    if old_name not in get_available_domains():
        return jsonify({"status": "error", "message": "Domain lama tidak ditemukan."})
    if new_name in get_available_domains():
        return jsonify({"status": "error", "message": "Nama domain baru sudah digunakan."})
        
    try:
        conn = DBConnection(MASTER_DB_PATH)
        c = conn.cursor()
        c.execute(f"ALTER TABLE tb_docs_{old_name} RENAME TO tb_docs_{new_name}")
        c.execute(f"ALTER TABLE tb_tax_{old_name} RENAME TO tb_tax_{new_name}")
        c.execute(f"ALTER TABLE tb_set_{old_name} RENAME TO tb_set_{new_name}")
        conn.commit()
        conn.close()
        
        if active_domain == old_name:
            active_domain = new_name
            set_active_domain(new_name)
        return jsonify({"status": "success", "message": f"Berhasil diubah menjadi {new_name}", "ledgers": get_available_domains(), "active": active_domain})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/ledgers/delete", methods=["POST"])
def delete_ledger():
    global active_domain, TAXONOMY
    data = request.get_json()
    target = data.get("name", "").strip()
    
    if target not in get_available_domains():
        return jsonify({"status": "error", "message": "Domain tidak ditemukan."})
        
    try:
        conn = DBConnection(MASTER_DB_PATH)
        c = conn.cursor()
        c.execute(f"DROP TABLE IF EXISTS tb_docs_{target}")
        c.execute(f"DROP TABLE IF EXISTS tb_tax_{target}")
        c.execute(f"DROP TABLE IF EXISTS tb_set_{target}")
        conn.commit()
        conn.close()
        
        domains = get_available_domains()
        if active_domain == target:
            active_domain = domains[0] if domains else "default"
            set_active_domain(active_domain)
            TAXONOMY = load_taxonomy(active_domain)
            
        return jsonify({"status": "success", "message": f"Domain {target} berhasil dihapus.", "ledgers": get_available_domains(), "active": active_domain})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route("/api/taxonomy/settings", methods=["POST"])
def update_taxonomy_settings():
    try:
        data = request.get_json()
        k = data.get("key")
        v = data.get("value")
        if k and v is not None:
            save_setting(active_domain, k, v)
        return jsonify({"status": "success", "taxonomy": TAXONOMY})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/taxonomy/add", methods=["POST"])
def add_taxonomy_label():
    try:
        data = request.get_json()
        layer = data.get("layer")
        name = data.get("name")
        if not layer or not name: return jsonify({"error": "Missing layer or name"})
        
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute(f"INSERT INTO tb_tax_{active_domain} (layer, name) VALUES (?, ?)", (layer, name))
        conn.commit()
        conn.close()
        
        global TAXONOMY
        TAXONOMY = load_taxonomy(active_domain)
        return jsonify({"status": "success", "taxonomy": TAXONOMY})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Label sudah ada."})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/taxonomy/edit", methods=["POST"])
def edit_taxonomy_label():
    try:
        data = request.get_json()
        old_name = data.get("old_name")
        new_name = data.get("new_name")
        layer = data.get("layer")
        
        if not old_name or not new_name or not layer: 
            return jsonify({"error": "Invalid data"})
            
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute(f"UPDATE tb_tax_{active_domain} SET name=? WHERE layer=? AND name=?", (new_name, layer, old_name))
        conn.commit()
        conn.close()
        
        global TAXONOMY
        TAXONOMY = load_taxonomy(active_domain)
        
        threading.Thread(target=async_relabel_task, args=(MASTER_DB_PATH, TAXONOMY["Layer_1_Domain"], TAXONOMY["Layer_2_Detail"])).start()
        
        return jsonify({"status": "success", "taxonomy": TAXONOMY})
    except sqlite3.IntegrityError:
        return jsonify({"error": "Label dengan nama tersebut sudah ada."})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/taxonomy/delete", methods=["POST"])
def delete_taxonomy_label():
    try:
        data = request.get_json()
        name = data.get("name")
        layer = data.get("layer")
        
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute("DELETE FROM tb_tax_{domain} WHERE layer=? AND name=?", (layer, name))
        conn.commit()
        conn.close()
        
        global TAXONOMY
        TAXONOMY = load_taxonomy(active_domain)
        
        threading.Thread(target=async_relabel_task, args=(MASTER_DB_PATH, TAXONOMY["Layer_1_Domain"], TAXONOMY["Layer_2_Detail"])).start()
        
        return jsonify({"status": "success", "taxonomy": TAXONOMY})
    except Exception as e:
        return jsonify({"error": str(e)})

@app.route("/api/search", methods=["POST"])
def search():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        alpha = float(data.get("alpha", 0.70))
        
        if not query:
            return jsonify([])
            
        # CORE_ENG: Semantic Vectorization via Dense MiniLM-L12 (ONNX)
        doc_vector = get_onnx_embedding(query)
        
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        cursor = conn.cursor()
        
        query_words = query.lower().split()
        if not query_words:
            return jsonify([])
            
        conditions = " OR ".join(["content LIKE ?" for _ in query_words])
        params = [f"%{w}%" for w in query_words]
        
        cursor.execute(f"SELECT filename, labels, content, embedding, id FROM tb_docs_{active_domain} WHERE {conditions}", params)
        rows_db = cursor.fetchall()
        conn.close()
        
        if not rows_db:
            return jsonify([])
            
        corpus = [row[2] for row in rows_db]
        filenames = [row[0] for row in rows_db]
        labels_list = [json.loads(row[1]) for row in rows_db]
        embeddings = [get_db_embedding(active_domain, row[4], row[3]) for row in rows_db]
        
        # CORE_ENG: Lexical Pipeline via Okapi BM25
        bm25 = BM25(corpus)
        query_words = query.lower().split()
        bm25_scores = [bm25.get_score(query_words, i) for i in range(len(corpus))]
        norm_bm25_scores = [1.0 - np.exp(-0.2 * score) for score in bm25_scores]
        
        results = []
        for i in range(len(rows_db)):
            dense_sim = get_cosine_similarity(doc_vector, embeddings[i])
            sparse_score = norm_bm25_scores[i]
            
            if sparse_score <= 0.05:
                hybrid_score = 0.0
            else:
                hybrid_score = alpha * dense_sim + (1.0 - alpha) * sparse_score
            final_sim = max(0.0, min(1.0, hybrid_score)) * 100.0
            
            results.append({
                "filename": filenames[i],
                "labels": labels_list[i],
                "content": corpus[i],
                "dense_score": float(dense_sim * 100.0),
                "sparse_score": float(sparse_score * 100.0),
                "similarity": float(final_sim)
            })
            
        results = sorted(results, key=lambda x: x["similarity"], reverse=True)
        return jsonify(results[:15])
    except Exception as e:
        log_error("Search API", f"Gagal mengeksekusi pencarian: {str(e)}", exc=True)
        return jsonify({"error": str(e)})

@app.route("/api/recommend", methods=["POST"])
def recommend():
    try:
        query = ""
        alpha = 0.70
        limit = 20
        offset = 0
        
        if request.content_type and "multipart/form-data" in request.content_type:
            alpha = float(request.form.get("alpha", 0.70))
            limit = int(request.form.get("limit", 20))
            offset = int(request.form.get("offset", 0))
            if 'file' in request.files:
                file = request.files['file']
                if file.filename != '':
                    filename = werkzeug.utils.secure_filename(file.filename)
                    query = extract_text_from_file_object(file, filename)
        else:
            data = request.get_json() or {}
            query = data.get("query", "").strip()
            alpha = float(data.get("alpha", 0.70))
            limit = int(data.get("limit", 20))
            offset = int(data.get("offset", 0))
        
        if not query:
            return jsonify({"data_files": [], "doc_files": []})
            
        doc_vector = get_onnx_embedding(query)
        
        import re
        from collections import Counter
        text_lower = query.lower()
        words = re.findall(r'\b[a-z]{3,}\b', text_lower)
        stop_words_reco = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta", "domain", "adalah", "merupakan", "yaitu", "yakni", "tentang", "terkait", "hal", "pasal", "undang", "nomor", "tahun", "ayat", "huruf", "angka", "bahwa", "oleh", "karena", "sebab", "tersebut", "tidak", "bisa", "akan", "dapat", "menjadi", "sebagaimana", "jo", "peraturan", "keputusan", "ketetapan", "republik", "indonesia"}
        filtered_words = [w for w in words if w not in stop_words_reco]
        word_counts = Counter(filtered_words)
        query_words = [w for w, count in word_counts.most_common(20)]
        if not query_words:
            query_words = ["data"]
            
        conditions = " OR ".join(["content LIKE ?" for _ in query_words])
        params = [f"%{w}%" for w in query_words]
        
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        cursor = conn.cursor()
        cursor.execute(f"SELECT filename, labels, content, embedding, id FROM tb_docs_{active_domain} WHERE {conditions}", params)
        rows_db = cursor.fetchall()
        conn.close()
        
        if not rows_db:
            return jsonify({"data_files": [], "doc_files": []})
            
        corpus = [row[2] for row in rows_db]
        filenames = [row[0] for row in rows_db]
        embeddings = [get_db_embedding(active_domain, row[4], row[3]) for row in rows_db]
        
        bm25 = BM25(corpus)
        norm_bm25_scores = [1.0 - np.exp(-0.2 * bm25.get_score(query_words, i)) for i in range(len(corpus))]
        
        data_files = []
        doc_files = []
        
        for i in range(len(rows_db)):
            sparse_score = norm_bm25_scores[i]
            if sparse_score <= 0.05:
                continue
                
            dense_sim = get_cosine_similarity(doc_vector, embeddings[i])
            hybrid_score = alpha * dense_sim + (1.0 - alpha) * sparse_score
            final_sim = max(0.0, min(1.0, hybrid_score)) * 100.0
            
            lower_name = filenames[i].lower()
            doc_obj = {
                "filename": filenames[i],
                "similarity": float(final_sim)
            }
            
            if lower_name.endswith('.csv') or lower_name.endswith('.xlsx'):
                data_files.append(doc_obj)
            else:
                doc_files.append(doc_obj)
                
        data_files = sorted(data_files, key=lambda x: x["similarity"], reverse=True)
        doc_files = sorted(doc_files, key=lambda x: x["similarity"], reverse=True)
        
        return jsonify({
            "data_files": data_files[offset:offset+limit],
            "doc_files": doc_files[offset:offset+limit]
        })
    except Exception as e:
        log_error("Recommend API", f"Gagal menarik rekomendasi: {str(e)}", exc=True)
        return jsonify({"error": str(e)})

@app.route("/api/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        text = data.get("text", "").strip()
        if not text:
            return jsonify({"error": "Konten teks kosong"})
            
        doc_vector = get_onnx_embedding(text)
        text_lower = text.lower()
        
        # 1. Layer 2 Detail prediction
        l2_raw_sims = []
        for label in TAXONOMY.get("Layer_2_Detail", []):
            lbl_vector = get_onnx_embedding(label)
            sim = get_cosine_similarity(doc_vector, lbl_vector)
            l2_raw_sims.append(sim)
            
        # [FIXED] SOFT LEXICAL GATEKEEPER dengan Stop-Word/IDF Penalty
        stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta", "domain", "adalah", "merupakan", "yaitu", "yakni", "tentang", "terkait", "hal", "pasal", "undang", "nomor", "tahun", "ayat", "huruf", "angka", "bahwa", "oleh", "karena", "sebab", "tersebut", "tidak", "bisa", "akan", "dapat", "menjadi", "sebagaimana", "jo", "peraturan", "keputusan", "ketetapan", "republik", "indonesia"}
        for i, label in enumerate(TAXONOMY.get("Layer_2_Detail", [])):
            text_words = set(text_lower.split())
            label_words = set(label.lower().split())
            
            overlap_weight = 0.0
            for w in text_words.intersection(label_words):
                if w not in stop_words:
                    overlap_weight += 1.0
                else:
                    overlap_weight += 0.05
                    
            if overlap_weight > 0.5:
                l2_raw_sims[i] = l2_raw_sims[i] * 1.0
            else:
                l2_raw_sims[i] = l2_raw_sims[i] * 0.80

        dyn_t2 = float(TAXONOMY.get("threshold_l2", 0.55))
        for i in range(len(l2_raw_sims)):
            if l2_raw_sims[i] < dyn_t2: 
                l2_raw_sims[i] = 0.0
            
        l2_scores = [max(0.0, min(1.0, sim)) * 100.0 for sim in l2_raw_sims]
        l2_sorted = sorted(zip(TAXONOMY.get("Layer_2_Detail", []), l2_scores), key=lambda x: x[1], reverse=True)
        if not l2_sorted or l2_sorted[0][1] == 0.0:
            l2_sorted = [("Tidak Terklasifikasi", 0.0)] + l2_sorted

        # 2. Layer 1 Domain prediction
        l1_raw_sims = []
        for label in TAXONOMY.get("Layer_1_Domain", []):
            lbl_vector = get_onnx_embedding(label)
            sim = get_cosine_similarity(doc_vector, lbl_vector)
            l1_raw_sims.append(sim)
            
        for i, label in enumerate(TAXONOMY.get("Layer_1_Domain", [])):
            text_words = set(text_lower.split())
            label_words = set(label.lower().split())
            
            overlap_weight = 0.0
            for w in text_words.intersection(label_words):
                if w not in stop_words:
                    overlap_weight += 1.0
                else:
                    overlap_weight += 0.05
                    
            if overlap_weight > 0.5:
                l1_raw_sims[i] = l1_raw_sims[i] * 1.0
            else:
                l1_raw_sims[i] = l1_raw_sims[i] * 0.80

        dyn_t1 = float(TAXONOMY.get("threshold_l1", 0.50))
        for i in range(len(l1_raw_sims)):
            if l1_raw_sims[i] < dyn_t1: 
                l1_raw_sims[i] = 0.0
            
        l1_scores = [max(0.0, min(1.0, sim)) * 100.0 for sim in l1_raw_sims]
        l1_sorted = sorted(zip(TAXONOMY.get("Layer_1_Domain", []), l1_scores), key=lambda x: x[1], reverse=True)
        if not l1_sorted or l1_sorted[0][1] == 0.0:
            l1_sorted = [("Tidak Terklasifikasi", 0.0)] + l1_sorted
        
        return jsonify({
            "layer_1": [{"label": x[0], "score": float(x[1])} for x in l1_sorted],
            "layer_2": [{"label": x[0], "score": float(x[1])} for x in l2_sorted]
        })
    except Exception as e:
        log_error("Predict API", f"Gagal memprediksi teks: {str(e)}", exc=True)
        return jsonify({"error": str(e)})

import werkzeug.utils

def extract_text_from_file_object(file, filename):
    ext = os.path.splitext(filename)[1].lower()
    content = ""
    
    if ext in ['.xlsx', '.csv']:
        df = pd.read_excel(file) if ext == '.xlsx' else pd.read_csv(file)
        cols = ", ".join(df.columns.astype(str).tolist())
        row_samples = []
        if not df.empty:
            for idx, row in df.head(3).iterrows():
                row_str = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                row_samples.append(f"Baris {idx+1}: {row_str}")
        sample_text = " // ".join(row_samples)
        content = f"Dokumen spreadsheet tabel. Kolom: {cols}. Data: {sample_text}"
    elif ext == '.pdf':
        content = ""
        # 1. Coba menggunakan PyMuPDF (fitz) karena lebih superior untuk layout kompleks
        try:
            import fitz
            file.seek(0)
            doc = fitz.open(stream=file.read(), filetype="pdf")
            text_pages = [page.get_text() for page in doc]
            content = "\n".join(text_pages)
        except:
            pass
            
        # 2. Fallback menggunakan pypdf jika fitz gagal atau tidak menghasilkan teks
        if not content.strip():
            try:
                import pypdf
                import io
                file.seek(0)
                pdf_file = io.BytesIO(file.read())
                reader = pypdf.PdfReader(pdf_file)
                text_pages = [page.extract_text() for page in reader.pages if page.extract_text()]
                content = "\n".join(text_pages)
            except:
                pass
                
        # 3. Fallback terakhir jika dokumen memang tidak memiliki layer teks (misal: hasil scan OCR)
        if not content.strip():
            content = f"Dokumen PDF {filename} (Gagal mengekstrak teks. Dokumen kemungkinan besar berupa hasil scan gambar atau dilindungi enkripsi DR)."
    elif ext == '.docx':
        import docx
        import io
        docx_file = io.BytesIO(file.read())
        doc = docx.Document(docx_file)
        content = "\n".join([para.text for para in doc.paragraphs])
        if not content.strip():
            content = f"Dokumen Word {filename} (tidak dapat mengekstrak teks)."
    elif ext == '.txt':
        content = file.read().decode('utf-8', errors='ignore')
    else:
        content = f"Dokumen {ext.upper()} dengan nama berkas {filename}. Berisi informasi terstruktur yang diunggah oleh pengguna."
        
    return content

@app.route("/api/ingest", methods=["POST"])
def ingest_file():
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file yang diunggah"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nama file kosong"})
        
    try:
        filename = werkzeug.utils.secure_filename(file.filename)
        content = extract_text_from_file_object(file, filename)
            
        # PROSES INGESTI (Vektor & Label)
        doc_vector = get_onnx_embedding(content)
        
        # Prediksi Label (L1 & L2) sama seperti Endpoint /api/predict
        text_lower = content.lower()
        stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta", "domain", "adalah", "merupakan", "yaitu", "yakni", "tentang", "terkait", "hal", "pasal", "undang", "nomor", "tahun", "ayat", "huruf", "angka", "bahwa", "oleh", "karena", "sebab", "tersebut", "tidak", "bisa", "akan", "dapat", "menjadi"}
        
        # Predict L2
        l2_raw_sims = []
        for label in TAXONOMY.get("Layer_2_Detail", []):
            lbl_vector = get_onnx_embedding(label)
            sim = get_cosine_similarity(doc_vector, lbl_vector)
            l2_raw_sims.append(sim)
            
        for i, label in enumerate(TAXONOMY.get("Layer_2_Detail", [])):
            text_words = set(text_lower.split())
            label_words = set(label.lower().split())
            overlap = sum(1.0 for w in text_words.intersection(label_words) if w not in stop_words)
            l2_raw_sims[i] = l2_raw_sims[i] * 1.0 if overlap > 0.5 else l2_raw_sims[i] * 0.80
            dyn_t2 = float(TAXONOMY.get("threshold_l2", 0.55))
            if l2_raw_sims[i] < dyn_t2: l2_raw_sims[i] = 0.0
            
        assigned_l2 = []
        for i, sim in enumerate(l2_raw_sims):
            if sim > 0.0:
                assigned_l2.append(TAXONOMY["Layer_2_Detail"][i])
        if not assigned_l2:
            assigned_l2 = ["Tidak Terklasifikasi"]

        # Predict L1
        l1_raw_sims = []
        for label in TAXONOMY.get("Layer_1_Domain", []):
            lbl_vector = get_onnx_embedding(label)
            sim = get_cosine_similarity(doc_vector, lbl_vector)
            l1_raw_sims.append(sim)
            
        for i, label in enumerate(TAXONOMY.get("Layer_1_Domain", [])):
            text_words = set(text_lower.split())
            label_words = set(label.lower().split())
            overlap = sum(1.0 for w in text_words.intersection(label_words) if w not in stop_words)
            l1_raw_sims[i] = l1_raw_sims[i] * 1.0 if overlap > 0.5 else l1_raw_sims[i] * 0.80
            dyn_t1 = float(TAXONOMY.get("threshold_l1", 0.50))
            if l1_raw_sims[i] < dyn_t1: l1_raw_sims[i] = 0.0
            
        assigned_l1 = []
        for i, sim in enumerate(l1_raw_sims):
            if sim > 0.0:
                assigned_l1.append(TAXONOMY["Layer_1_Domain"][i])
        if not assigned_l1:
            assigned_l1 = ["Tidak Terklasifikasi"]
            
        predicted_labels = list(set(assigned_l1 + assigned_l2))
        labels_json = json.dumps(predicted_labels)
        vector_json = json.dumps(doc_vector.tolist())
        
        # INSERT KE DB
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        try:
            c.execute(f"INSERT INTO tb_docs_{active_domain} (filename, content, labels, embedding) VALUES (?, ?, ?, ?)",
                      (filename, content, labels_json, vector_json))
            conn.commit()
        except sqlite3.IntegrityError:
            # Jika filename sudah ada, kita update saja
            c.execute(f"UPDATE tb_docs_{active_domain} SET content=?, labels=?, embedding=? WHERE filename=?",
                      (content, labels_json, vector_json, filename))
            conn.commit()
        conn.close()
            
        return jsonify({
            "status": "success", 
            "content": content, 
            "filename": filename,
            "labels": predicted_labels
        })
    except Exception as e:
        log_error("Ingestion API", f"Gagal memproses file {file.filename}: {str(e)}", exc=True)
        return jsonify({"error": f"Gagal memproses file: {str(e)}"})

@app.route("/api/labels", methods=["GET"])
def get_labels():
    # [BIG DATA DOCTRINE - TEORI #11: SINGLE-PASS AGGREGATION]
    # Mengganti loop 30 FULL TABLE SCANS (1.5 GB Disk Read per klik) menjadi 1 Kueri Agregat (Single-Pass)
    # yang diproses sepenuhnya oleh C-Engine SQLite JSON1, memotong latensi hingga 99% tanpa membekukan GIL Python.
    global TAXONOMY
    all_labels = set(TAXONOMY.get("Layer_1_Domain", []) + TAXONOMY.get("Layer_2_Detail", []))
    
    conn = DBConnection(MASTER_DB_PATH, timeout=15)
    c = conn.cursor()
    
    # 1 Putaran Kueri untuk Agregasi Massal C-Engine
    c.execute(f"""
        SELECT json_each.value, COUNT(tb_docs_{active_domain}.id) 
        FROM tb_docs_{active_domain}, json_each(tb_docs_{active_domain}.labels) 
        WHERE tb_docs_{active_domain}.labels IS NOT NULL AND tb_docs_{active_domain}.labels != '[]'
        GROUP BY json_each.value
    """)
    db_counts = dict(c.fetchall())
    conn.close()
    
    sorted_labels = []
    for lbl in all_labels:
        sorted_labels.append({"label": lbl, "count": db_counts.get(lbl, 0)})
    
    # Urutkan berdasarkan abjad
    sorted_labels = sorted(sorted_labels, key=lambda x: x['label'])
    return jsonify(sorted_labels)

@app.route("/api/labels/edit", methods=["POST"])
def edit_label():
    global TAXONOMY
    data = request.get_json()
    old_name = data.get("old_name", "").strip()
    new_name = data.get("new_name", "").strip()
    
    if not old_name or not new_name:
        return jsonify({"status": "error", "message": "Nama label tidak boleh kosong"})
        
    try:
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        # [BIG DATA DOCTRINE - TEORI #7: Existential Short-Circuiting]
        c.execute(f"""
            SELECT id, labels 
            FROM tb_docs_{active_domain} 
            WHERE EXISTS (
                SELECT 1 FROM json_each(tb_docs_{active_domain}.labels) WHERE json_each.value = ?
            )
        """, (old_name,))
        rows = c.fetchall()
        
        updated = 0
        for doc_id, labels_str in rows:
            if labels_str:
                labels = json.loads(labels_str)
                if old_name in labels:
                    new_labels = [new_name if l == old_name else l for l in labels]
                    c.execute(f"UPDATE tb_docs_{active_domain} SET labels = ? WHERE id = ?", (json.dumps(new_labels), doc_id))
                    updated += 1
                    
        conn.commit()
        conn.close()
        
        # Update dynamic lists
        if old_name in TAXONOMY["Layer_1_Domain"]:
            TAXONOMY["Layer_1_Domain"] = [new_name if x == old_name else x for x in TAXONOMY["Layer_1_Domain"]]
        if old_name in TAXONOMY["Layer_2_Detail"]:
            TAXONOMY["Layer_2_Detail"] = [new_name if x == old_name else x for x in TAXONOMY["Layer_2_Detail"]]
            
        return jsonify({"status": "success", "message": f"Berhasil memperbarui label '{old_name}' menjadi '{new_name}' pada {updated} berkas!"})
    except Exception as e:
        log_error("Label Editor", f"Gagal memperbarui label {old_name}: {str(e)}", exc=True)
        return jsonify({"status": "error", "message": f"Gagal memperbarui label: {e}"})

@app.route("/api/labels/delete", methods=["POST"])
def delete_label():
    global TAXONOMY
    data = request.get_json()
    lbl_to_delete = data.get("label", "").strip()
    
    if not lbl_to_delete:
        return jsonify({"status": "error", "message": "Nama label kosong"})
        
    try:
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        # [BIG DATA DOCTRINE - TEORI #7: Existential Short-Circuiting]
        c.execute(f"""
            SELECT id, labels 
            FROM tb_docs_{active_domain} 
            WHERE EXISTS (
                SELECT 1 FROM json_each(tb_docs_{active_domain}.labels) WHERE json_each.value = ?
            )
        """, (lbl_to_delete,))
        rows = c.fetchall()
        
        updated = 0
        for doc_id, labels_str in rows:
            if labels_str:
                labels = json.loads(labels_str)
                if lbl_to_delete in labels:
                    new_labels = [l for l in labels if l != lbl_to_delete]
                    c.execute(f"UPDATE tb_docs_{active_domain} SET labels = ? WHERE id = ?", (json.dumps(new_labels), doc_id))
                    updated += 1
                    
        conn.commit()
        conn.close()
        
        # Update global list
        if lbl_to_delete in TAXONOMY["Layer_1_Domain"]:
            TAXONOMY["Layer_1_Domain"].remove(lbl_to_delete)
        if lbl_to_delete in TAXONOMY["Layer_2_Detail"]:
            TAXONOMY["Layer_2_Detail"].remove(lbl_to_delete)
            
        return jsonify({"status": "success", "message": f"Berhasil menghapus label '{lbl_to_delete}' dari {updated} berkas!"})
    except Exception as e:
        log_error("Label Deleter", f"Gagal menghapus label {lbl_to_delete}: {str(e)}", exc=True)
        return jsonify({"status": "error", "message": f"Gagal menghapus label: {e}"})

@app.route("/api/labels/add", methods=["POST"])
def add_label():
    global TAXONOMY
    data = request.get_json()
    new_lbl = data.get("label", "").strip()
    level = data.get("level", "layer_2")
    
    if not new_lbl:
        return jsonify({"status": "error", "message": "Nama label kosong"})
        
    if level == "layer_1":
        if new_lbl not in TAXONOMY["Layer_1_Domain"]:
            TAXONOMY["Layer_1_Domain"].append(new_lbl)
        else:
            return jsonify({"status": "error", "message": f"Label '{new_lbl}' sudah ada di Layer 1"})
    else:
        if new_lbl not in TAXONOMY["Layer_2_Detail"]:
            TAXONOMY["Layer_2_Detail"].append(new_lbl)
        else:
            return jsonify({"status": "error", "message": f"Label '{new_lbl}' sudah ada di Layer 2"})
            
    return jsonify({"status": "success", "message": f"Berhasil menambahkan '{new_lbl}' ke taksonomi aktif!"})

from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

@app.route("/api/taxonomy/generate", methods=["POST"])
def generate_taxonomy():
    global TAXONOMY, DB_EMBEDDING_CACHE, TAXONOMY_PROGRESS, active_domain
    try:
        data_req = request.get_json() or {}
        threshold_l1 = float(data_req.get("threshold_l1", 0.50))
        threshold_l2 = float(data_req.get("threshold_l2", 0.55))
        
        domain_to_use = data_req.get("domain", active_domain)
        
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        cursor = conn.cursor()
        # [BIG DATA DOCTRINE - MEMORY SAFE FIRST]
        # Hanya tarik ID dan Embedding. Abaikan 'content' (Teks 30K dokumen = 1GB+ RAM)
        cursor.execute(f"SELECT id, embedding FROM tb_docs_{domain_to_use}")
        rows = cursor.fetchall()
        
        N = len(rows)
        if N == 0:
            conn.close()
            TAXONOMY_PROGRESS["status"] = "idle"
            return jsonify({"status": "error", "message": "Database kosong atau belum ada dokumen untuk dianalisis."})
            
        # RUMUS RICE RULE (Untuk Penemuan Topik / Discovery)
        X = math.ceil(2 * (N ** (1/3)))
        n_clusters_l2 = min(X, N)
        
        TAXONOMY_PROGRESS.update({
            "status": "running",
            "stage": "Mengekstrak Semantic Vektor (Memory Safe)",
            "current": 0,
            "total": N
        })
        
        ids = []
        embeddings = []
        DB_EMBEDDING_CACHE.clear() # Cegah RAM Leak saat scan masal
        
        for idx, row in enumerate(rows):
            doc_id, emb_str = row
            ids.append(doc_id)
            if emb_str is None or len(json.loads(emb_str)) != 384:
                # Fallback: tarik content HANYA jika embedding rusak/kosong
                cursor.execute(f"SELECT content FROM tb_docs_{domain_to_use} WHERE id = ?", (doc_id,))
                c_content = cursor.fetchone()[0]
                emb = get_onnx_embedding(c_content)
                cursor.execute(f"UPDATE tb_docs_{domain_to_use} SET embedding = ? WHERE id = ?", (json.dumps(emb.tolist()), doc_id))
            else:
                emb = np.array(json.loads(emb_str), dtype=np.float32)
                
            embeddings.append(emb)
            
            if (idx + 1) % 500 == 0:
                conn.commit() # [BATCH COMMIT] Cegah SQLite Disk I/O Error pada transaksi massal
                
            if (idx + 1) % 500 == 0 or (idx + 1) == N:
                TAXONOMY_PROGRESS["current"] = idx + 1
        
        conn.commit()
        del rows # Free memory explicitly
        import gc
        gc.collect()
        
        TAXONOMY_PROGRESS.update({"stage": "Menjalankan K-Means Clustering & TF-IDF (Batched)..."})
        embeddings = np.array(embeddings, dtype=np.float32)
        
        # 1. K-Means Layer 2 (Detail)
        kmeans_l2 = KMeans(n_clusters=n_clusters_l2, random_state=42, n_init="auto")
        cluster_l2_assignments = kmeans_l2.fit_predict(embeddings)
        
        # [BIG DATA DOCTRINE] TF-IDF Sampling (Max 30 dokumen per cluster)
        # Alih-alih memuat 31.000 dokumen ke RAM, kita sample 30 dokumen per cluster = RAM 99% lebih hemat
        layer_2_labels = []
        l2_cluster_to_label = {}
        import random
        
        for i in range(n_clusters_l2):
            cluster_docs_idx = np.where(cluster_l2_assignments == i)[0]
            if len(cluster_docs_idx) == 0:
                l2_cluster_to_label[i] = f"Cluster {i}"
                continue
                
            sample_size = min(30, len(cluster_docs_idx))
            sampled_indices = random.sample(list(cluster_docs_idx), sample_size)
            sampled_ids = [ids[idx] for idx in sampled_indices]
            
            placeholders = ','.join('?' * len(sampled_ids))
            cursor.execute(f"SELECT content FROM tb_docs_{domain_to_use} WHERE id IN ({placeholders})", sampled_ids)
            sample_contents = [r[0] for r in cursor.fetchall()]
            
            try:
                from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
                indo_stop_words = ["dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta", "domain", "adalah", "merupakan", "yaitu", "yakni", "tentang", "terkait", "hal", "pasal", "undang", "nomor", "tahun", "ayat", "huruf", "angka", "bahwa", "oleh", "karena", "sebab", "tersebut", "tidak", "bisa", "akan", "dapat", "menjadi", "sebagaimana", "jo", "peraturan", "keputusan", "ketetapan", "republik", "indonesia"]
                custom_stop_words = list(ENGLISH_STOP_WORDS) + indo_stop_words
                vectorizer = TfidfVectorizer(max_df=0.8, min_df=1, stop_words=custom_stop_words, token_pattern=r'(?u)\b[a-zA-Z][a-zA-Z]+\b')
                tfidf_matrix = vectorizer.fit_transform(sample_contents)
                feature_names = vectorizer.get_feature_names_out()
                
                cluster_tfidf = tfidf_matrix.sum(axis=0)
                cluster_tfidf = np.squeeze(np.asarray(cluster_tfidf))
                
                top_indices = cluster_tfidf.argsort()[::-1][:2]
                top_words = [feature_names[idx].title() for idx in top_indices]
                label_name = " ".join(top_words)
            except:
                label_name = ""
                
            if not label_name:
                label_name = f"Cluster {i}"
                
            layer_2_labels.append(label_name)
            l2_cluster_to_label[i] = label_name
            
        # 2. K-Means Layer 1 (Domain) berdasarkan pusat cluster Layer 2
        l2_centroids = kmeans_l2.cluster_centers_
        n_clusters_l1 = max(3, math.ceil(math.sqrt(n_clusters_l2)))
        n_clusters_l1 = min(n_clusters_l1, n_clusters_l2)
        
        kmeans_l1 = KMeans(n_clusters=n_clusters_l1, random_state=42, n_init="auto")
        cluster_l1_assignments = kmeans_l1.fit_predict(l2_centroids)
        
        layer_1_labels = []
        l1_cluster_to_label = {}
        
        for i in range(n_clusters_l1):
            l2_indices = np.where(cluster_l1_assignments == i)[0]
            if len(l2_indices) == 0:
                l1_cluster_to_label[i] = f"Domain {i}"
                continue
            
            # Ambil perwakilan kata dari sub-cluster terbesarnya
            representative_l2 = layer_2_labels[l2_indices[0]]
            l1_label_name = f"Domain {representative_l2.split()[0]}"
            layer_1_labels.append(l1_label_name)
            l1_cluster_to_label[i] = l1_label_name
            
        # Update TAXONOMY
        TAXONOMY["Layer_1_Domain"] = list(set(layer_1_labels))
        TAXONOMY["Layer_2_Detail"] = list(set(layer_2_labels))
        TAXONOMY["threshold_l1"] = threshold_l1
        TAXONOMY["threshold_l2"] = threshold_l2
        save_taxonomy(active_domain, TAXONOMY)
        
        # 3. Multi-Label Overlapping Assignment (Thresholding Venn Diagram)
        l2_embs = kmeans_l2.cluster_centers_
        l2_labels_map = [l2_cluster_to_label[i] for i in range(n_clusters_l2)]
        
        l1_embs = kmeans_l1.cluster_centers_
        l1_labels_map = [l1_cluster_to_label[i] for i in range(n_clusters_l1)]
        
        outlier_count = 0
        overlap_count = 0
        
        TAXONOMY_PROGRESS.update({"stage": "Thresholding Cosine (Venn Overlaps)...", "current": 0})
        
        for idx, doc_id in enumerate(ids):
            doc_emb = embeddings[idx]
            assigned_labels = []
            
            # Cek Layer 1 (Domain)
            for i, l1_emb in enumerate(l1_embs):
                sim = get_cosine_similarity(doc_emb, l1_emb)
                if sim >= threshold_l1:
                    assigned_labels.append(l1_labels_map[i])
                    
            # Cek Layer 2 (Detail)
            for i, l2_emb in enumerate(l2_embs):
                sim = get_cosine_similarity(doc_emb, l2_emb)
                if sim >= threshold_l2:
                    assigned_labels.append(l2_labels_map[i])
                    
            # Outlier Fallback: Jika tidak menembus threshold apa pun
            if not assigned_labels:
                outlier_count += 1
                assigned_labels.append("Tidak Terklasifikasi")
            elif len(assigned_labels) > 1:
                overlap_count += 1
                
            labels_json = json.dumps(list(set(assigned_labels)))
            cursor.execute(f"UPDATE tb_docs_{active_domain} SET labels = ? WHERE id = ?", (labels_json, doc_id))
            
            if (idx + 1) % 500 == 0:
                conn.commit() # [BATCH COMMIT] Mencegah penumpukan journal file SQLite (Disk I/O Error)
                
            if (idx + 1) % 50 == 0 or (idx + 1) == N:
                TAXONOMY_PROGRESS["current"] = idx + 1
            
        conn.commit()
        conn.close()
        
        TAXONOMY_PROGRESS.update({"status": "idle", "stage": "Selesai"})
        
        
        metrics = {
            "total_docs": N,
            "outliers": outlier_count,
            "outlier_pct": round((outlier_count / N) * 100, 1) if N > 0 else 0,
            "overlaps": overlap_count,
            "overlap_pct": round((overlap_count / N) * 100, 1) if N > 0 else 0
        }
        TAXONOMY["metrics"] = metrics
        save_setting(MASTER_DB_PATH, "last_metrics", json.dumps(metrics))
        
        return jsonify({
            "status": "success",
            "message": f"Multi-Label Venn Architecture selesai. T1={threshold_l1:.2f}, T2={threshold_l2:.2f}.",
            "taxonomy": TAXONOMY,
            "metrics": metrics
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        TAXONOMY_PROGRESS.update({"status": "idle", "stage": "Error"})
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/reset_db", methods=["POST"])
def reset_database():
    try:
        if MASTER_DB_PATH == DB_REAL_PATH:
            # Regenerate using real dataset generator
            import importlib
            import generate_real_demo
            importlib.reload(generate_real_demo)
            generate_real_demo.generate_real_dataset()
        else:
            # Reseed default database
            conn = DBConnection(DB_PATH, timeout=15)
            c = conn.cursor()
            c.execute("DROP TABLE IF EXISTS documents")
            c.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    content TEXT,
                    labels TEXT,
                    embedding TEXT
                )
            """)
            conn.commit()
            conn.close()
            # Run seeding
            os.system(f'python "{os.path.join(CURRENT_DIR, "app_gui.py")}" --seed')
            
        return jsonify({"status": "success", "message": "Database berhasil di-reset dan dibangkitkan ulang secara bersih!"})
    except Exception as e:
        log_error("DB Reset", f"Gagal mereset database: {str(e)}", exc=True)
        return jsonify({"status": "error", "message": f"Gagal mereset database: {e}"})

@app.route("/api/documents/wipe", methods=["POST"])
def wipe_database():
    try:
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute(f"DELETE FROM tb_docs_{active_domain}")
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Seluruh data berhasil dihapus dari pangkalan data aktif."})
    except Exception as e:
        log_error("DB Wipe", f"Gagal wipe data: {str(e)}", exc=True)
        return jsonify({"status": "error", "message": f"Gagal wipe data: {e}"})

@app.route("/api/documents/batch_upload", methods=["POST"])
def batch_upload():
    try:
        if 'files[]' not in request.files:
            return jsonify({"status": "error", "message": "Tidak ada file yang diunggah"})
            
        files = request.files.getlist('files[]')
        if not files:
            return jsonify({"status": "error", "message": "Daftar file kosong"})
            
        conn = DBConnection(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        
        success_count = 0
        for file in files:
            if file.filename == '':
                continue
            filename = werkzeug.utils.secure_filename(file.filename)
            content = extract_text_from_file_object(file, filename)
            
            if content:
                try:
                    emb = get_onnx_embedding(content)
                    c.execute(f"INSERT INTO tb_docs_{active_domain} (filename, content, labels, embedding) VALUES (?, ?, ?, ?)", 
                              (filename, content, json.dumps([]), json.dumps(emb.tolist())))
                    success_count += 1
                except sqlite3.IntegrityError:
                    pass # Abaikan file duplikat
                except Exception as ex:
                    log_error("Batch Upload", f"Gagal memproses file {filename}: {str(ex)}")
                    
        conn.commit()
        conn.close()
        
        return jsonify({"status": "success", "message": f"{success_count} file berhasil diunggah dan diekstraksi semantiknya!"})
    except Exception as e:
        log_error("Batch Upload", f"Kesalahan internal: {str(e)}", exc=True)
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/pasal/sync_supabase", methods=["POST"])
def sync_pasal_supabase():
    try:
        import threading
        import subprocess
        
        def run_sync_pipeline():
            log_error("Auto-Sync", "Memulai proses unduhan API Pasal.id di background...")
            ingest_pasal_script = os.path.join(PROJECT_ROOT, "ETL_PASAL", "ingest_pasal.py")
            ingest_pg_script = os.path.join(PROJECT_ROOT, "ETL_PASAL", "ingest_raw_postgres.py")
            
            # Step 1: Download
            res1 = subprocess.run([sys.executable, ingest_pasal_script], capture_output=True, text=True)
            if res1.returncode != 0:
                log_error("Auto-Sync", f"Gagal pada tahap unduhan: {res1.stderr}")
                return
                
            log_error("Auto-Sync", "Unduhan selesai. Memulai injeksi ke Supabase PostgreSQL...")
            
            # Step 2: Push to Postgres
            res2 = subprocess.run([sys.executable, ingest_pg_script], capture_output=True, text=True)
            if res2.returncode != 0:
                log_error("Auto-Sync", f"Gagal pada tahap injeksi Supabase: {res2.stderr}")
                return
                
            log_error("Auto-Sync", "Sinkronisasi ke Supabase PostgreSQL berhasil diselesaikan!")
            
        thread = threading.Thread(target=run_sync_pipeline)
        thread.daemon = True
        thread.start()
        
        return jsonify({"status": "success", "message": "Proses sinkronisasi telah berjalan di latar belakang (Background Thread)."})
    except Exception as e:
        log_error("Auto-Sync", f"Kesalahan internal: {str(e)}", exc=True)
        return jsonify({"status": "error", "message": str(e)})

if __name__ == "__main__":
    print("[INFO] Memulai server Flask pada http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
