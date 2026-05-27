import os
import sys
import re
import sqlite3
import json
import numpy as np
import pandas as pd
import math
import threading
from flask import Flask, render_template, jsonify, request, redirect

# Konfigurasi Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
ONNX_DIR = os.path.join(ROOT_DIR, "STKI", "onnx_model")
ONNX_FILE = os.path.join(ONNX_DIR, "multi_label_model.onnx")
DB_PATH = os.path.join(ROOT_DIR, "academic_metadata.db")
DB_REAL_PATH = os.path.join(ROOT_DIR, "academic_demo_real.db")

app = Flask(__name__, 
            template_folder=os.path.join(ROOT_DIR, "_UIUX"), 
            static_folder=os.path.join(ROOT_DIR, "_UIUX"),
            static_url_path="/")

# State Sistem Aktif (Default)
active_db_type = "akademik"
DB_PATHS = {
    "akademik": os.path.join(ROOT_DIR, "academic_metadata.db"),
    "demo_real": os.path.join(ROOT_DIR, "academic_demo_real.db"),
    "politik": os.path.join(ROOT_DIR, "db_politik.db"),
    "ekonomi": os.path.join(ROOT_DIR, "db_ekonomi.db"),
    "bisnis": os.path.join(ROOT_DIR, "db_bisnis.db"),
    "etika": os.path.join(ROOT_DIR, "db_etika.db")
}
active_db_path = DB_PATHS[active_db_type]

# Taksonomi Dinamis (Diload dari file JSON)
TAXONOMY_FILE = os.path.join(ROOT_DIR, "taxonomy_dynamic.json")

def load_taxonomy(db_type):
    if not os.path.exists(TAXONOMY_FILE):
        return {"Layer_1_Domain": ["Umum"], "Layer_2_Detail": ["Tidak Terklasifikasi"]}
    try:
        with open(TAXONOMY_FILE, 'r') as f:
            data = json.load(f)
            return data.get(db_type, {"Layer_1_Domain": ["Umum"], "Layer_2_Detail": ["Tidak Terklasifikasi"]})
    except:
        return {"Layer_1_Domain": ["Umum"], "Layer_2_Detail": ["Tidak Terklasifikasi"]}

def save_taxonomy(db_type, tax_data):
    data = {}
    if os.path.exists(TAXONOMY_FILE):
        try:
            with open(TAXONOMY_FILE, 'r') as f:
                data = json.load(f)
        except:
            pass
    data[db_type] = tax_data
    with open(TAXONOMY_FILE, 'w') as f:
        json.dump(data, f, indent=4)

TAXONOMY = load_taxonomy(active_db_type)

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
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
from transformers import AutoTokenizer

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

def get_onnx_embedding(text):
    if session is None or tokenizer is None:
        return np.zeros(5)
    distilled_text = extract_key_sentences(text, num_sentences=5)
    # [FIXED] IndoBERT sangat sensitif huruf kapital dan sering menganggapnya [UNK].
    # Text harus diturunkan menjadi lowercase sebelum masuk tokenizer.
    inputs = tokenizer(distilled_text.lower(), return_tensors="np", padding="max_length", truncation=True, max_length=256)
    input_ids = inputs["input_ids"].astype(np.int64)
    attention_mask = inputs["attention_mask"].astype(np.int64)
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
        tokenizer = AutoTokenizer.from_pretrained(ONNX_DIR)
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
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, content FROM documents")
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
            stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta"}
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
            
            for i in range(len(l2_raw_sims)):
                if l2_raw_sims[i] < 0.35: # Threshold disesuaikan menjadi 35%
                    l2_raw_sims[i] = 0.0
            
            best_l2_label = "Tidak Terklasifikasi"
            if max(l2_raw_sims) > 0.0:
                best_l2_label = tax_layer2[np.argmax(l2_raw_sims)]

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
            stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta"}
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
            
            for i in range(len(l1_raw_sims)):
                if l1_raw_sims[i] < 0.30: # Threshold disesuaikan menjadi 30%
                    l1_raw_sims[i] = 0.0
                
            best_l1_label = "Tidak Terklasifikasi"
            if max(l1_raw_sims) > 0.0:
                best_l1_label = tax_layer1[np.argmax(l1_raw_sims)]
            
            predicted_labels = [best_l1_label, best_l2_label]
            cursor.execute("UPDATE documents SET labels = ? WHERE id = ?", (json.dumps(predicted_labels), doc_id))
            
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
        conn = sqlite3.connect(active_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, labels, content FROM documents ORDER BY id DESC LIMIT 500")
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
        return jsonify({"status": "success", "documents": docs})
    except Exception as e:
        log_error("DB Explorer", f"Gagal memuat dokumen: {str(e)}", exc=True)
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/status", methods=["GET"])
def get_status():
    global active_db_type, active_db_path, TAXONOMY
    
    # Buat DB jika belum ada
    if not os.path.exists(active_db_path):
        conn = sqlite3.connect(active_db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT UNIQUE,
                content TEXT,
                labels TEXT,
                embedding TEXT
            )
        ''')
        conn.commit()
        conn.close()
        
    conn = sqlite3.connect(active_db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM documents")
    total_docs = c.fetchone()[0]
    
    # Hitung Rice Rule optimal X
    optimal_x = math.ceil(2 * (total_docs ** (1/3))) if total_docs > 0 else 0
    
    # Ambil unique labels saat ini di DB
    c.execute("SELECT labels FROM documents")
    rows = c.fetchall()
    conn.close()
    
    unique_labels = set()
    for r in rows:
        if r[0]:
            try:
                for l in json.loads(r[0]):
                    unique_labels.add(l)
            except:
                pass
                
    db_names = {
        "akademik": "Akademik Kampus",
        "politik": "Politik & Regulasi",
        "ekonomi": "Ekonomi Makro & Mikro",
        "bisnis": "Peraturan Bisnis & Korporat",
        "etika": "Etika & Hukum Hak Asasi",
        "demo_real": "Demo Real (Riset & Jurnal)"
    }
    db_name = db_names.get(active_db_type, "Unknown Database")
    
    return jsonify({
        "active_db": db_name,
        "db_type": active_db_type,
        "total_docs": total_docs,
        "optimal_labels_count": optimal_x,
        "actual_labels_count": len(unique_labels),
        "taxonomy": TAXONOMY
    })

@app.route("/api/switch_db", methods=["POST"])
def switch_db():
    global active_db_type, active_db_path, TAXONOMY
    data = request.get_json()
    target = data.get("db_type", "akademik")
    
    if target in DB_PATHS:
        active_db_type = target
        active_db_path = DB_PATHS[target]
        TAXONOMY = load_taxonomy(target)
        
        # Trigger real demo generation if it's demo_real and doesn't exist
        if target == "demo_real" and not os.path.exists(active_db_path):
            os.system(f'python "{os.path.join(CURRENT_DIR, "generate_real_demo.py")}"')
            
    return jsonify({"status": "success", "message": f"Berhasil dialihkan ke Database {target.upper()}"})

@app.route("/api/search", methods=["POST"])
def search():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        alpha = float(data.get("alpha", 0.70))
        
        if not query:
            return jsonify([])
            
        doc_vector = get_onnx_embedding(query)
        
        conn = sqlite3.connect(active_db_path)
        cursor = conn.cursor()
        
        query_words = query.lower().split()
        if not query_words:
            return jsonify([])
            
        conditions = " OR ".join(["content LIKE ?" for _ in query_words])
        params = [f"%{w}%" for w in query_words]
        
        cursor.execute(f"SELECT filename, labels, content, embedding FROM documents WHERE {conditions}", params)
        rows_db = cursor.fetchall()
        conn.close()
        
        if not rows_db:
            return jsonify([])
            
        corpus = [row[2] for row in rows_db]
        filenames = [row[0] for row in rows_db]
        labels_list = [json.loads(row[1]) for row in rows_db]
        embeddings = [np.array(json.loads(row[3])) for row in rows_db]
        
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
        query_words = query.lower().split()
        conditions = " OR ".join(["content LIKE ?" for _ in query_words])
        params = [f"%{w}%" for w in query_words]
        
        conn = sqlite3.connect(active_db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT filename, labels, content, embedding FROM documents WHERE {conditions} LIMIT ? OFFSET ?", (*params, limit, offset))
        rows_db = cursor.fetchall()
        conn.close()
        
        if not rows_db:
            return jsonify({"data_files": [], "doc_files": []})
            
        corpus = [row[2] for row in rows_db]
        filenames = [row[0] for row in rows_db]
        embeddings = [np.array(json.loads(row[3])) for row in rows_db]
        
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
            elif lower_name.endswith('.pdf') or lower_name.endswith('.docx') or lower_name.endswith('.txt'):
                doc_files.append(doc_obj)
                
        data_files = sorted(data_files, key=lambda x: x["similarity"], reverse=True)
        doc_files = sorted(doc_files, key=lambda x: x["similarity"], reverse=True)
        
        return jsonify({
            "data_files": data_files,
            "doc_files": doc_files
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
        stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta"}
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

        for i in range(len(l2_raw_sims)):
            if l2_raw_sims[i] < 0.35: 
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

        for i in range(len(l1_raw_sims)):
            if l1_raw_sims[i] < 0.30: 
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
        import pypdf
        import io
        pdf_file = io.BytesIO(file.read())
        reader = pypdf.PdfReader(pdf_file)
        text_pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                text_pages.append(t)
        content = "\n".join(text_pages)
        if not content.strip():
            content = f"Dokumen PDF {filename} (tidak dapat mengekstrak teks)."
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
        stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta"}
        
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
            if l2_raw_sims[i] < 0.35: l2_raw_sims[i] = 0.0
            
        best_l2 = "Tidak Terklasifikasi"
        if l2_raw_sims and max(l2_raw_sims) > 0.0:
            best_l2 = TAXONOMY["Layer_2_Detail"][np.argmax(l2_raw_sims)]

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
            if l1_raw_sims[i] < 0.30: l1_raw_sims[i] = 0.0
            
        best_l1 = "Tidak Terklasifikasi"
        if l1_raw_sims and max(l1_raw_sims) > 0.0:
            best_l1 = TAXONOMY["Layer_1_Domain"][np.argmax(l1_raw_sims)]
            
        labels_json = json.dumps([best_l1, best_l2])
        vector_json = json.dumps(doc_vector.tolist())
        
        # INSERT KE DB
        conn = sqlite3.connect(active_db_path)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO documents (filename, content, labels, embedding) VALUES (?, ?, ?, ?)",
                      (filename, content, labels_json, vector_json))
            conn.commit()
        except sqlite3.IntegrityError:
            # Jika filename sudah ada, kita update saja
            c.execute("UPDATE documents SET content=?, labels=?, embedding=? WHERE filename=?",
                      (content, labels_json, vector_json, filename))
            conn.commit()
        conn.close()
            
        return jsonify({
            "status": "success", 
            "content": content, 
            "filename": filename,
            "labels": [best_l1, best_l2]
        })
    except Exception as e:
        log_error("Ingestion API", f"Gagal memproses file {file.filename}: {str(e)}", exc=True)
        return jsonify({"error": f"Gagal memproses file: {str(e)}"})

@app.route("/api/labels", methods=["GET"])
def get_labels():
    conn = sqlite3.connect(active_db_path)
    c = conn.cursor()
    c.execute("SELECT labels FROM documents")
    rows = c.fetchall()
    conn.close()
    
    unique_labels = {}
    for r in rows:
        if r[0]:
            try:
                for l in json.loads(r[0]):
                    unique_labels[l] = unique_labels.get(l, 0) + 1
            except:
                pass
                
    sorted_labels = [{"label": k, "count": v} for k, v in sorted(unique_labels.items())]
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
        conn = sqlite3.connect(active_db_path)
        c = conn.cursor()
        c.execute("SELECT id, labels FROM documents")
        rows = c.fetchall()
        
        updated = 0
        for doc_id, labels_str in rows:
            if labels_str:
                labels = json.loads(labels_str)
                if old_name in labels:
                    new_labels = [new_name if l == old_name else l for l in labels]
                    c.execute("UPDATE documents SET labels = ? WHERE id = ?", (json.dumps(new_labels), doc_id))
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
        conn = sqlite3.connect(active_db_path)
        c = conn.cursor()
        c.execute("SELECT id, labels FROM documents")
        rows = c.fetchall()
        
        updated = 0
        for doc_id, labels_str in rows:
            if labels_str:
                labels = json.loads(labels_str)
                if lbl_to_delete in labels:
                    new_labels = [l for l in labels if l != lbl_to_delete]
                    c.execute("UPDATE documents SET labels = ? WHERE id = ?", (json.dumps(new_labels), doc_id))
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
    global TAXONOMY
    try:
        conn = sqlite3.connect(active_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, content, embedding FROM documents WHERE embedding IS NOT NULL")
        rows = cursor.fetchall()
        
        N = len(rows)
        if N == 0:
            conn.close()
            return jsonify({"status": "error", "message": "Database kosong atau belum ada dokumen untuk dianalisis."})
            
        # RUMUS RICE RULE
        X = math.ceil(2 * (N ** (1/3)))
        n_clusters_l2 = min(X, N)
        
        ids = [r[0] for r in rows]
        contents = [r[1] for r in rows]
        
        embeddings = []
        for r in rows:
            emb = np.array(json.loads(r[2]))
            if len(emb) != 384:
                emb = get_onnx_embedding(r[1])
            embeddings.append(emb)
        embeddings = np.array(embeddings)
        
        # 1. K-Means Layer 2 (Detail)
        kmeans_l2 = KMeans(n_clusters=n_clusters_l2, random_state=42, n_init="auto")
        cluster_l2_assignments = kmeans_l2.fit_predict(embeddings)
        
        # Ekstraksi Kata Kunci menggunakan TF-IDF
        try:
            vectorizer = TfidfVectorizer(max_df=0.8, min_df=2, stop_words=["dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta"])
            tfidf_matrix = vectorizer.fit_transform(contents)
        except:
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(contents)
            
        feature_names = vectorizer.get_feature_names_out()
        layer_2_labels = []
        l2_cluster_to_label = {}
        
        for i in range(n_clusters_l2):
            cluster_docs_idx = np.where(cluster_l2_assignments == i)[0]
            if len(cluster_docs_idx) == 0:
                l2_cluster_to_label[i] = f"Cluster {i}"
                continue
                
            cluster_tfidf = tfidf_matrix[cluster_docs_idx].sum(axis=0)
            cluster_tfidf = np.squeeze(np.asarray(cluster_tfidf))
            
            top_indices = cluster_tfidf.argsort()[::-1][:2]
            top_words = [feature_names[idx].title() for idx in top_indices]
            label_name = " ".join(top_words)
            
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
        save_taxonomy(active_db_type, TAXONOMY)
        
        # 3. Relabeling dokumen di Database
        for idx, doc_id in enumerate(ids):
            l2_cluster = cluster_l2_assignments[idx]
            l1_cluster = cluster_l1_assignments[l2_cluster]
            
            lbl_l2 = l2_cluster_to_label[l2_cluster]
            lbl_l1 = l1_cluster_to_label[l1_cluster]
            
            labels_json = json.dumps([lbl_l1, lbl_l2])
            cursor.execute("UPDATE documents SET labels = ? WHERE id = ?", (labels_json, doc_id))
            
        conn.commit()
        conn.close()
        
        return jsonify({
            "status": "success",
            "message": f"K-Means selesai. Rumus Rice (X={n_clusters_l2}) diterapkan.",
            "taxonomy": TAXONOMY
        })
    except Exception as e:
        log_error("Taxonomy Generator", f"Gagal generate taxonomy: {str(e)}", exc=True)
        return jsonify({"status": "error", "message": str(e)})

@app.route("/api/reset_db", methods=["POST"])
def reset_database():
    try:
        if active_db_path == DB_REAL_PATH:
            # Regenerate using real dataset generator
            import importlib
            import generate_real_demo
            importlib.reload(generate_real_demo)
            generate_real_demo.generate_real_dataset()
        else:
            # Reseed default database
            conn = sqlite3.connect(DB_PATH)
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
        conn = sqlite3.connect(active_db_path)
        c = conn.cursor()
        c.execute("DELETE FROM documents")
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
            
        conn = sqlite3.connect(active_db_path)
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
                    c.execute("INSERT INTO documents (filename, content, labels, embedding) VALUES (?, ?, ?, ?)", 
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

if __name__ == "__main__":
    print("[INFO] Memulai server Flask pada http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
