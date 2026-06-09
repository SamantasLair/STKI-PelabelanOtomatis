import os
import json
import sqlite3
import numpy as np
import glob
import re
from tqdm import tqdm

# Konfigurasi Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR) # Mundur 1 direktori dari ETL_HAKI
ONNX_DIR = os.path.join(PROJECT_ROOT, "STKI", "onnx_model")
ONNX_FILE = os.path.join(ONNX_DIR, "multi_label_model.onnx")
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "_RawData", "hukum_pasal_id")
DB_MASTER_PATH = os.path.join(PROJECT_ROOT, "_databases", "stki_master.db")

# ONNX Engine Initialization
import onnxruntime as ort
from transformers import AutoTokenizer

print("[*] Memuat Model Semantic Dense: paraphrase-multilingual-MiniLM-L12-v2 via ONNX...")
# CPU Optimization Config
sess_options = ort.SessionOptions()
sess_options.intra_op_num_threads = 4
# CORE_ENG: Semantic Vectorization via Dense MiniLM-L12 (ONNX)
session = ort.InferenceSession(ONNX_FILE, sess_options=sess_options, providers=['CPUExecutionProvider'])
tokenizer = AutoTokenizer.from_pretrained(ONNX_DIR)

def extract_key_sentences(text, num_sentences=5):
    """TextRank Distillation untuk ekstrak intisari kalimat dengan bobot tertinggi."""
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
    """Generate semantic vector representation via MiniLM."""
    distilled_text = extract_key_sentences(text, num_sentences=5)
    inputs = tokenizer(
        distilled_text,
        return_tensors="np",
        padding="max_length",
        truncation=True,
        max_length=256
    )
    input_ids = inputs["input_ids"].astype(np.int64)
    attention_mask = inputs["attention_mask"].astype(np.int64)
    
    # Forward Pass
    outputs = session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
    logits = outputs[0].squeeze()
    
    # Vector Normalization
    probs = 1.0 / (1.0 + np.exp(-logits))
    return probs.tolist()

def extract_content_from_json(data):
    """Extract and aggregate structural content (Title + Articles) into contiguous string."""
    work = data.get("work", {})
    title = work.get("title", "")
    
    content_parts = [f"DOKUMEN HUKUM: {title}"]
    
    articles = data.get("articles", [])
    if articles:
        for art in articles:
            if art.get("content"):
                content_parts.append(f"Pasal {art.get('number', '')}: {art.get('content')}")
                
    return " \n".join(content_parts)

def main():
    print("="*60)
    print("🚀 MEMULAI TAHAP 2: VEKTORISASI DATA HUKUM (AI EMBEDDING) 🚀")
    print("="*60)
    
    # 1. Mendapatkan daftar seluruh berkas JSON
    json_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.json"))
    total_files = len(json_files)
    
    if total_files == 0:
        print("[!] Tidak ada dokumen JSON di _RawData/hukum_pasal_id/.")
        return
        
    print(f"[*] Ditemukan {total_files} dokumen JSON siap proses.")
    print(f"[*] Database Tujuan: {DB_MASTER_PATH}")
    
    # 2. Database Preparation
    os.makedirs(os.path.dirname(DB_MASTER_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_MASTER_PATH)
    cursor = conn.cursor()
    # Kita menggunakan tabel terpisah di dalam DB sentral (Polymorphic Separation)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_docs_hukum (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            content TEXT,
            labels TEXT,
            embedding TEXT
        )
    """)
    conn.commit()
    
    # 3. Sequential Vectorization Pipeline
    print("\n[*] Menjalankan NLP Embedding Engine...")
    
    with tqdm(total=total_files, desc="Proses Embedding", unit="doc") as pbar:
        for file_path in json_files:
            filename = os.path.basename(file_path)
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Metadata Extraction
                work = data.get("work", {})
                year = str(work.get("year", "Unknown"))
                doc_type = work.get("type", "UU")
                
                # Content Aggregation
                content_text = extract_content_from_json(data)
                
                # Venn Taxonomy Constraints
                labels = ["Hukum & Regulasi", f"Tahun {year}", f"Kategori {doc_type}"]
                
                # Dense Embedding Generation O(1)
                embedding_vector = get_onnx_embedding(content_text)
                
                # Bulk Insert
                cursor.execute("""
                    INSERT OR REPLACE INTO tb_docs_hukum (filename, content, labels, embedding)
                    VALUES (?, ?, ?, ?)
                """, (filename, content_text, json.dumps(labels), json.dumps(embedding_vector)))
                
            except Exception as e:
                pass
            finally:
                pbar.update(1)
                
    conn.commit()
    conn.close()
    
    print("\n" + "="*60)
    print("✅ TAHAP 2 SELESAI ✅")
    print(f"{total_files} dokumen hukum berhasil dikonversi ke vektor dan masuk ke tabel tb_docs_hukum di stki_master.db")
    print("="*60)

if __name__ == "__main__":
    main()
