import os
import sys
import json
import sqlite3
import numpy as np
import time
import math

# Menyiapkan path absolut
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
QA_DIR = os.path.dirname(CURRENT_DIR)
ROOT_DIR = os.path.dirname(QA_DIR)
sys.path.append(ROOT_DIR)

from TKI.app_web import get_onnx_embedding, BM25, get_cosine_similarity

DB_PATH = os.path.join(ROOT_DIR, "academic_demo_real.db")

# ---------------------------------------------------------
# SKENARIO PENGUJIAN: NDCG & SEMANTIC ROBUSTNESS (TYPO/SYNONYM)
# ---------------------------------------------------------
# NDCG (Normalized Discounted Cumulative Gain) adalah standar industri untuk
# mengukur kualitas urutan pencarian berdasarkan "Graded Relevance" (Tingkat Relevansi).
# 3 = Sangat Relevan (Perfect Match)
# 2 = Cukup Relevan (Synonym / Konteks Serupa)
# 1 = Sedikit Relevan (Singgungan Tipis)
# 0 = Noise / Tidak Relevan

TEST_CASES = [
    {
        # Kasus 1: Query dengan Typo dan Sinonim ("artificial intelegence" -> Artificial Intelligence)
        "query": "cara bikin artificial intelegence untuk klasifikasi gambar",
        "injections": [
            (9101, "AI_Vision_Perfect.pdf", 3, "Skripsi ini membahas perancangan Artificial Intelligence (AI) menggunakan CNN untuk klasifikasi gambar medis."),
            (9102, "Machine_Learning_Partial.pdf", 2, "Penelitian mengenai Machine Learning dan pengenalan pola visual tanpa menyebutkan AI secara eksplisit."),
            (9103, "Data_Mining_Weak.pdf", 1, "Penggunaan algoritma k-means untuk memisahkan data numerik pada database, bagian dari ilmu data."),
            (9104, "Cooking_Noise.pdf", 0, "Cara membuat kue bolu yang enak menggunakan oven listrik pintar.")
        ]
    },
    {
        # Kasus 2: Query Konseptual (Mencari makna, bukan kata persis)
        "query": "aturan hukum memberhentikan pekerja sepihak",
        "injections": [
            (9201, "PHK_Perfect.pdf", 3, "Undang-undang ketenagakerjaan pasal 151 mengenai prosedur Pemutusan Hubungan Kerja (PHK) oleh perusahaan."),
            (9202, "Kontrak_Kerja_Partial.pdf", 2, "Peraturan terkait penyelesaian sengketa masa akhir kontrak karyawan swasta."),
            (9203, "Hak_Asasi_Weak.pdf", 1, "Buku tentang hak asasi manusia dalam memperoleh penghidupan yang layak."),
            (9204, "Resep_Kopi_Noise.pdf", 0, "Panduan meracik kopi arabika untuk pekerja di pagi hari.")
        ]
    }
]

def compute_dcg(relevances):
    dcg = 0.0
    for i, rel in enumerate(relevances):
        # DCG = rel_i / log2(i + 2)
        dcg += rel / math.log2(i + 2)
    return dcg

def evaluate_ndcg():
    print("=========================================================")
    print("[SYSTEM] ANTIGRAVITY v4.0 - TEST #2 (NDCG & ROBUSTNESS)")
    print("=========================================================\n")
    
    alpha = 0.70 # Hybrid Alpha
    
    # Ambil sedikit sampel riil sebagai noise background (anti-OOM)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, labels, content, embedding FROM documents LIMIT 300")
    real_rows = c.fetchall()
    conn.close()
    
    total_ndcg = 0.0
    
    for case_idx, case in enumerate(TEST_CASES):
        print(f"[{case_idx+1}] MENGUJI KASUS ROBUSTNESS: '{case['query']}'")
        
        # Salin base rows
        rows = list(real_rows)
        
        # Map id dokumen ke skor relevansi (ideal)
        relevance_map = {}
        for (doc_id, filename, rel_score, text) in case["injections"]:
            emb = get_onnx_embedding(text)
            rows.append((doc_id, filename, "[]", text, json.dumps(emb.tolist())))
            relevance_map[doc_id] = rel_score
            
        corpus_texts = [r[3] for r in rows]
        embeddings = [np.array(json.loads(r[4])) for r in rows]
        
        # Build Index
        bm25 = BM25(corpus_texts)
        
        # Eksekusi Query
        query = case["query"]
        query_vector = get_onnx_embedding(query)
        query_words = query.lower().split()
        
        results = []
        for i in range(len(rows)):
            sparse_score = bm25.get_score(query_words, i)
            norm_sparse = 1.0 - np.exp(-0.2 * sparse_score)
            
            if norm_sparse <= 0.05:
                hybrid_score = 0.0
            else:
                dense_sim = get_cosine_similarity(query_vector, embeddings[i])
                hybrid_score = alpha * dense_sim + (1.0 - alpha) * norm_sparse
            
            doc_id = rows[i][0]
            rel_score = relevance_map.get(doc_id, 0) # 0 jika itu adalah dokumen riil (noise)
            
            results.append({"doc_id": doc_id, "score": hybrid_score, "rel_score": rel_score})
            
        # Urutkan berdasarkan prediksi sistem
        results.sort(key=lambda x: x["score"], reverse=True)
        
        # Hitung DCG@5 dari sistem
        top_5_rels = [res["rel_score"] for res in results[:5]]
        dcg = compute_dcg(top_5_rels)
        
        # Hitung IDCG@5 (Ideal DCG) jika diurutkan dengan sempurna [3, 2, 1, 0, 0]
        ideal_rels = sorted(relevance_map.values(), reverse=True)[:5]
        # Pad dengan 0 jika kurang dari 5
        while len(ideal_rels) < 5:
            ideal_rels.append(0)
            
        idcg = compute_dcg(ideal_rels)
        
        # NDCG
        ndcg = dcg / idcg if idcg > 0 else 0.0
        total_ndcg += ndcg
        
        print(f" -> Urutan Relevansi Sistem (Top 5): {top_5_rels}")
        print(f" -> Ideal Order (Target)           : {ideal_rels}")
        print(f" -> NDCG@5 Score                   : {ndcg*100:.2f}%\n")
        
    avg_ndcg = total_ndcg / len(TEST_CASES)
    
    print("=========================================================")
    print("[RESULT] HASIL AUDIT NDCG (Normalized Discounted Cumulative Gain)")
    print("=========================================================")
    print(f"Skor Rata-Rata NDCG@5: {avg_ndcg*100:.2f}%")
    print("=========================================================")
    
    if avg_ndcg >= 0.75:
        print("[STATUS] PASSED - Sistem cerdas, tahan Typo & membedakan gradasi makna.")
    else:
        print("[STATUS] FAILED - Sistem kesulitan meranking makna bertingkat.")

if __name__ == "__main__":
    evaluate_ndcg()
