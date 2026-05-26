import os
import sys
import re
import sqlite3
import json
import numpy as np
import pandas as pd
import math
import threading
from flask import Flask, render_template, jsonify, request

# Konfigurasi Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
ONNX_DIR = os.path.join(ROOT_DIR, "STKI", "onnx_model")
ONNX_FILE = os.path.join(ONNX_DIR, "multi_label_model.onnx")
DB_PATH = os.path.join(ROOT_DIR, "academic_metadata.db")
DB_REAL_PATH = os.path.join(ROOT_DIR, "academic_demo_real.db")

app = Flask(__name__, template_folder=os.path.join(CURRENT_DIR, "templates"), static_folder=os.path.join(CURRENT_DIR, "static"))

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

# Taksonomi Dinamis untuk 6 Database
TAXONOMIES = {
    "akademik": {
        "Layer_1_Domain": ["Akademik Mahasiswa", "Administrasi Dosen", "Jadwal dan SKS Perkuliahan"],
        "Layer_2_Detail": ["Transkrip Nilai Lengkap", "KRS SKS Kelas", "Daftar Dosen Pengajar", "Laporan Keuangan", "Kurikulum Jurusan"]
    },
    "politik": {
        "Layer_1_Domain": ["Kebijakan Publik", "Pemilihan Umum", "Partai Politik"],
        "Layer_2_Detail": ["RUU Pemilu", "Laporan Kampanye", "Debat Kandidat", "Regulasi Daerah", "Survei Elektabilitas"]
    },
    "ekonomi": {
        "Layer_1_Domain": ["Makroekonomi", "Mikroekonomi", "Keuangan Internasional"],
        "Layer_2_Detail": ["Laporan Inflasi", "Kebijakan Moneter", "Pasar Saham", "Analisis UMKM", "Nilai Tukar Mata Uang"]
    },
    "bisnis": {
        "Layer_1_Domain": ["Hukum Perusahaan", "Pajak & Cukai", "Ketenagakerjaan"],
        "Layer_2_Detail": ["Pendirian PT", "Pajak Pertambahan Nilai", "Kontrak Karyawan", "Izin Usaha", "Audit Keuangan"]
    },
    "etika": {
        "Layer_1_Domain": ["Etika Profesi", "Integritas Korporat", "Hak Asasi Manusia"],
        "Layer_2_Detail": ["Kode Etik Kedokteran", "Anti Korupsi", "Whistleblower", "Diskriminasi Tempat Kerja", "Perlindungan Data Pribadi"]
    },
    "demo_real": {
        "Layer_1_Domain": ["Skripsi & Tugas Akhir", "Dataset & Publikasi Riset", "Jurnal & Artikel Ilmiah"],
        "Layer_2_Detail": [
            "Skripsi Informatika", "Skripsi Sistem Informasi", "Skripsi Teknik Komputer",
            "Dataset Citra Medis", "Dataset Teks Indonesia", "Dataset Sensor IoT",
            "Jurnal Sinta 1 Gold", "Jurnal Sinta 2 Silver", "Jurnal Sinta 3 Bronze",
            "Artikel Konferensi IEEE", "Artikel Prosiding Nasional", "Laporan Pengabdian",
            "Proposal Hibah Riset", "Monograf Buku Ajar", "Paten HAKI Terdaftar",
            "Hak Cipta Software", "Desain Industri"
        ]
    }
}

TAXONOMY = {
    "Layer_1_Domain": list(TAXONOMIES[active_db_type]["Layer_1_Domain"]),
    "Layer_2_Detail": list(TAXONOMIES[active_db_type]["Layer_2_Detail"])
}

# Peta turunan ke induk secara statik untuk UI dan Helper fallback
CHILD_TO_PARENT_MAP = {
    # Akademik
    "Transkrip Nilai Lengkap": "Akademik Mahasiswa",
    "KRS SKS Kelas": "Akademik Mahasiswa",
    "Laporan Keuangan": "Akademik Mahasiswa",
    "Daftar Dosen Pengajar": "Administrasi Dosen",
    "Kurikulum Jurusan": "Jadwal dan SKS Perkuliahan",
    
    # Politik
    "RUU Pemilu": "Pemilihan Umum",
    "Laporan Kampanye": "Pemilihan Umum",
    "Debat Kandidat": "Pemilihan Umum",
    "Regulasi Daerah": "Kebijakan Publik",
    "Survei Elektabilitas": "Partai Politik",
    
    # Ekonomi
    "Laporan Inflasi": "Makroekonomi",
    "Kebijakan Moneter": "Makroekonomi",
    "Pasar Saham": "Keuangan Internasional",
    "Nilai Tukar Mata Uang": "Keuangan Internasional",
    "Analisis UMKM": "Mikroekonomi",
    
    # Bisnis
    "Pendirian PT": "Hukum Perusahaan",
    "Izin Usaha": "Hukum Perusahaan",
    "Pajak Pertambahan Nilai": "Pajak & Cukai",
    "Kontrak Karyawan": "Ketenagakerjaan",
    "Audit Keuangan": "Pajak & Cukai",
    
    # Etika
    "Kode Etik Kedokteran": "Etika Profesi",
    "Anti Korupsi": "Integritas Korporat",
    "Whistleblower": "Integritas Korporat",
    "Diskriminasi Tempat Kerja": "Hak Asasi Manusia",
    "Perlindungan Data Pribadi": "Hak Asasi Manusia",
    
    # Demo Real
    "Skripsi Informatika": "Skripsi & Tugas Akhir",
    "Skripsi Sistem Informasi": "Skripsi & Tugas Akhir",
    "Skripsi Teknik Komputer": "Skripsi & Tugas Akhir",
    "Dataset Citra Medis": "Dataset & Publikasi Riset",
    "Dataset Teks Indonesia": "Dataset & Publikasi Riset",
    "Dataset Sensor IoT": "Dataset & Publikasi Riset",
    "Paten HAKI Terdaftar": "Dataset & Publikasi Riset",
    "Hak Cipta Software": "Dataset & Publikasi Riset",
    "Desain Industri": "Dataset & Publikasi Riset",
    "Proposal Hibah Riset": "Dataset & Publikasi Riset",
    "Jurnal Sinta 1 Gold": "Jurnal & Artikel Ilmiah",
    "Jurnal Sinta 2 Silver": "Jurnal & Artikel Ilmiah",
    "Jurnal Sinta 3 Bronze": "Jurnal & Artikel Ilmiah",
    "Artikel Konferensi IEEE": "Jurnal & Artikel Ilmiah",
    "Artikel Prosiding Nasional": "Jurnal & Artikel Ilmiah",
    "Laporan Pengabdian": "Jurnal & Artikel Ilmiah",
    "Monograf Buku Ajar": "Jurnal & Artikel Ilmiah",
}

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
                text_words = set(text.lower().split())
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
                if l2_raw_sims[i] < 0.85: # Threshold disesuaikan menjadi 0.85
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
                text_words = set(text.lower().split())
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
                if l1_raw_sims[i] < 0.85:
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
    return render_template("index.html")

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
    
    if target in TAXONOMIES:
        active_db_type = target
        active_db_path = DB_PATHS[target]
        TAXONOMY["Layer_1_Domain"] = list(TAXONOMIES[target]["Layer_1_Domain"])
        TAXONOMY["Layer_2_Detail"] = list(TAXONOMIES[target]["Layer_2_Detail"])
        
        # Trigger real demo generation if it's demo_real and doesn't exist
        if target == "demo_real" and not os.path.exists(active_db_path):
            os.system(f'python "{os.path.join(CURRENT_DIR, "generate_real_demo.py")}"')
            
    return jsonify({"status": "success", "message": f"Berhasil dialihkan ke Database {target.upper()}"})

@app.route("/api/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "").strip()
    alpha = float(data.get("alpha", 0.70))
    
    if not query:
        return jsonify([])
        
    doc_vector = get_onnx_embedding(query)
    
    conn = sqlite3.connect(active_db_path)
    cursor = conn.cursor()
    
    # [FIXED] Menghapus LIMIT 2500. Menggunakan SQL LIKE dinamis sebagai pre-filter
    # Ini memastikan hanya dokumen yang berpotensi memiliki BM25 > 0 yang ditarik ke Memory,
    # menyelamatkan OOM tanpa merusak akurasi global corpus.
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
    
    # BM25 Sparse Retrieval dengan Normalisasi Probabilistik (Asimtotik)
    bm25 = BM25(corpus)
    query_words = query.lower().split()
    bm25_scores = [bm25.get_score(query_words, i) for i in range(len(corpus))]
    # Menggunakan fungsi 1 - exp(-0.2 * score) untuk normalisasi asimtotik (rentang 0-1)
    # Alih-alih max() yang merusak relativitas skor.
    norm_bm25_scores = [1.0 - np.exp(-0.2 * score) for score in bm25_scores]
    
    results = []
    for i in range(len(rows_db)):
        dense_sim = get_cosine_similarity(doc_vector, embeddings[i])
        sparse_score = norm_bm25_scores[i]
        
        # Hybrid Fusion (Linear Combination) dengan Penalty Absolut untuk OOD
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
        
    # Sort Descending
    results = sorted(results, key=lambda x: x["similarity"], reverse=True)
    return jsonify(results[:15])  # Kembalikan top 15 dokumen terbaik

@app.route("/api/recommend", methods=["POST"])
def recommend():
    # Endpoint khusus untuk Recommendation Engine dengan Server-Side Pagination
    data = request.get_json()
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
    # Pagination diterapkan langsung pada SQL DB
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
        
        # Server-Side File Partitioning
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

@app.route("/api/predict", methods=["POST"])
def predict():
    data = request.get_json()
    text = data.get("text", "").strip()
    if not text:
        return jsonify({"error": "Konten teks kosong"})
        
    doc_vector = get_onnx_embedding(text)
    text_lower = text.lower()
    
    # 1. Layer 2 Detail prediction
    l2_raw_sims = []
    for label in TAXONOMY["Layer_2_Detail"]:
        lbl_vector = get_onnx_embedding(label)
        sim = get_cosine_similarity(doc_vector, lbl_vector)
        l2_raw_sims.append(sim)
        
    # [FIXED] SOFT LEXICAL GATEKEEPER dengan Stop-Word/IDF Penalty
    stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta"}
    for i, label in enumerate(TAXONOMY["Layer_2_Detail"]):
        text_words = set(text.lower().split())
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
        if l2_raw_sims[i] < 0.85:
            l2_raw_sims[i] = 0.0
        
    l2_scores = [max(0.0, min(1.0, sim)) * 100.0 for sim in l2_raw_sims]
    l2_sorted = sorted(zip(TAXONOMY["Layer_2_Detail"], l2_scores), key=lambda x: x[1], reverse=True)
    
    best_l2_label = "Tidak Terklasifikasi"
    if l2_sorted[0][1] > 0.0:
        best_l2_label = l2_sorted[0][0]
    else:
        l2_sorted = [("Tidak Terklasifikasi", 0.0)] + l2_sorted

    # 2. Layer 1 Domain prediction
    l1_raw_sims = []
    for label in TAXONOMY["Layer_1_Domain"]:
        lbl_vector = get_onnx_embedding(label)
        sim = get_cosine_similarity(doc_vector, lbl_vector)
        l1_raw_sims.append(sim)
        
    # [FIXED] Menghapus propagasi hierarki di Layer 1.
    
    # [FIXED] SOFT LEXICAL GATEKEEPER dengan Stop-Word/IDF Penalty
    stop_words = {"dan", "atau", "di", "ke", "dari", "pada", "untuk", "dengan", "yang", "ini", "itu", "juga", "sebagai", "dalam", "serta"}
    for i, label in enumerate(TAXONOMY["Layer_1_Domain"]):
        text_words = set(text.lower().split())
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
        if l1_raw_sims[i] < 0.85:
            l1_raw_sims[i] = 0.0
        
    l1_scores = [max(0.0, min(1.0, sim)) * 100.0 for sim in l1_raw_sims]
    l1_sorted = sorted(zip(TAXONOMY["Layer_1_Domain"], l1_scores), key=lambda x: x[1], reverse=True)
    if l1_sorted[0][1] == 0.0:
        l1_sorted = [("Tidak Terklasifikasi", 0.0)] + l1_sorted
    
    return jsonify({
        "layer_1": [{"label": x[0], "score": float(x[1])} for x in l1_sorted],
        "layer_2": [{"label": x[0], "score": float(x[1])} for x in l2_sorted]
    })

import werkzeug.utils

@app.route("/api/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file yang diunggah"})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Nama file kosong"})
        
    try:
        filename = werkzeug.utils.secure_filename(file.filename)
        ext = os.path.splitext(filename)[1].lower()
        
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
            
        return jsonify({"status": "success", "content": content, "filename": filename})
    except Exception as e:
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

@app.route("/api/labels/regenerate", methods=["POST"])
def regenerate_labels():
    global relabel_progress
    if relabel_progress["status"] == "running":
        return jsonify({"status": "error", "message": "Proses regenerasi label sedang berjalan"})
        
    t = threading.Thread(target=async_relabel_task, args=(active_db_path, TAXONOMY["Layer_1_Domain"], TAXONOMY["Layer_2_Detail"]))
    t.start()
    return jsonify({"status": "success", "message": "Batch regenerasi label ONNX dimulai"})

@app.route("/api/labels/regenerate/progress", methods=["GET"])
def get_regenerate_progress():
    return jsonify(relabel_progress)

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
        return jsonify({"status": "error", "message": f"Gagal mereset database: {e}"})

if __name__ == "__main__":
    print("[INFO] Memulai server Flask pada http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=False)
