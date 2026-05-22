import pandas as pd
import numpy as np
import time
import os
import sqlite3

# Import Tokenizer dan ONNX dari sistem STKI yang ada
import onnxruntime as ort
from transformers import AutoTokenizer

def init_stki_engine():
    # Load Model ONNX dan Tokenizer (menggunakan model IndoBERT)
    model_path = "STKI/onnx_model/multi_label_model.onnx"
    tokenizer = AutoTokenizer.from_pretrained("indobenchmark/indobert-base-p1")
    session = ort.InferenceSession(model_path)
    return tokenizer, session

def get_onnx_embedding(text, tokenizer, session):
    inputs = tokenizer(text, return_tensors="np", truncation=True, padding="max_length", max_length=256)
    ort_inputs = {
        "input_ids": inputs["input_ids"].astype(np.int64),
        "attention_mask": inputs["attention_mask"].astype(np.int64)
    }
    logits = session.run(None, ort_inputs)[0]
    return logits[0]

def stki_pseudo_relevance_feedback_robust(df, tokenizer, session):
    """
    HIPOTESIS 1 (Solusi): Dense Vector Retrieval via ONNX.
    Menerjemahkan header kolom menjadi Dense Vector dan menghitung Cosine Similarity
    dengan target kelas yang ada di database.
    """
    # Menghapus underscore agar tokenisasi IndoBERT berjalan normal
    headers = " ".join(df.columns.tolist()).replace("_", " ").lower()
    sample_data = " ".join(df.head(1).astype(str).values.flatten()).replace("_", " ").lower()
    
    # Prompting untuk memberikan konteks semantik ke model klasifikasi ONNX
    query_text = f"data laporan akademik mahasiswa berisi {headers}. sampel: {sample_data}"
    
    # Template target vektor bayangan (Simulasi)
    templates = {
        "Transkrip Nilai Lengkap": "skor mutu beban studi nilai ipk angka indeks",
        "Laporan Keuangan": "uang bayar spp tagihan semester keuangan",
        "KRS SKS Kelas": "jadwal kelas ruang dosen mata kuliah pengampu"
    }
    
    # Dapatkan embedding query (menggunakan context)
    query_vec = get_onnx_embedding(query_text, tokenizer, session)
    
    best_score = -1
    best_template = "Tidak Dikenali"
    
    for t_name, t_text in templates.items():
        t_vec = get_onnx_embedding(t_text, tokenizer, session)
        
        # Hitung Cosine Similarity
        dot = np.dot(query_vec, t_vec)
        norm = np.linalg.norm(query_vec) * np.linalg.norm(t_vec)
        sim = dot / norm if norm > 0 else 0
        
        if sim > best_score:
            best_score = sim
            best_template = t_name
            
    # Ambang batas Cosine Similarity agar tidak asal tebak
    if best_score < 0.60:
        return "Tidak Dikenali"
        
    return best_template

def semantic_schema_alignment_robust(df, template):
    """
    HIPOTESIS 2 (Solusi): Fuzzy Matching & Normalization.
    """
    if template == "Transkrip Nilai Lengkap":
        # Deteksi kolom nilai (Bisa bernama 'Nilai_Huruf', 'Skor_Mutu', dll)
        # Cari kolom yang isinya dominan huruf A, B, C, D, E
        target_col = None
        for col in df.columns:
            # Hindari mendeteksi kolom Identitas atau kolom Non-Akademik sebagai kolom Nilai
            col_lower = col.lower()
            if any(w in col_lower for w in ['nama', 'id', 'nim', 'agama', 'darah', 'kelas', 'ruang', 'gender']):
                continue 
            sample = df[col].astype(str).str.upper().str.strip()
            if sample.isin(['A', 'B', 'C', 'D', 'E']).sum() >= len(df) * 0.5:
                target_col = col
                break
                
        if target_col is None:
            return False, df, "Gagal menemukan kolom ordinal yang valid untuk dikonversi."
            
        # Mapping dengan Normalisasi (Huruf Kecil/Besar tidak masalah)
        df['Bobot_Nilai'] = df[target_col].astype(str).str.upper().str.strip()
        mapping_nilai = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'E': 0.0}
        df['Bobot_Nilai'] = df['Bobot_Nilai'].map(mapping_nilai)
        
        # Tangani data aneh ('X') dengan aman
        if df['Bobot_Nilai'].isnull().any():
            invalid_count = df['Bobot_Nilai'].isnull().sum()
            print(f"[WARNING] Ditemukan {invalid_count} data kotor/tak terpetakan. Dihapus (Drop).")
            df = df.dropna(subset=['Bobot_Nilai'])
            
        return True, df, "Success"
        
    return False, df, "Template tidak didukung."

def hard_coded_rule_extractor_robust(df, template):
    """
    HIPOTESIS 3 & 4 (Solusi): Defensive Programming & Vectorized Backend.
    """
    if template == "Transkrip Nilai Lengkap":
        # Defensive Programming: Cek keberadaan Kolom Esensial
        # Kita butuh sesuatu yang merepresentasikan SKS. Cari kata 'SKS' atau 'Beban'
        sks_col = [c for c in df.columns if 'sks' in c.lower() or 'beban' in c.lower()]
        id_col = [c for c in df.columns if 'nim' in c.lower() or 'id' in c.lower()]
        
        if not sks_col or not id_col or 'Bobot_Nilai' not in df.columns:
            raise KeyError(f"Skema tidak valid. Kehilangan kolom esensial. SKS:{sks_col}, ID:{id_col}")
            
        sks_c = sks_col[0]
        id_c = id_col[0]
        
        df['Total_Skor'] = df['Bobot_Nilai'] * df[sks_c]
        
        # Agregasi
        laporan = df.groupby(id_c).apply(
            lambda x: pd.Series({
                'Total_SKS_Diambil': x[sks_c].sum(),
                'IPK_Kumulatif': round(x['Total_Skor'].sum() / x[sks_c].sum(), 2) if x[sks_c].sum() > 0 else 0
            }), include_groups=False
        ).reset_index()
        
        return laporan
    return pd.DataFrame()

def run_pilar3_pipeline(csv_path):
    print(f"=== MEMULAI PIPELINE PILAR 3 V2 (PRODUCTION READY) ===")
    start_time = time.time()
    
    tokenizer, session = init_stki_engine()
    
    df_raw = pd.read_csv(csv_path)
    print(f"[1] Data Mentah Dibaca: Bentuk Awal {df_raw.columns.tolist()}")
    
    template_target = stki_pseudo_relevance_feedback_robust(df_raw, tokenizer, session)
    print(f"[2] STKI Dense Retrieval menetapkan format: '{template_target}'")
    
    if template_target == "Tidak Dikenali":
        print("[!] Abort: Template tidak ditemukan.")
        return
        
    is_aligned, df_aligned, msg = semantic_schema_alignment_robust(df_raw, template_target)
    if not is_aligned:
        print(f"[!] Abort: {msg}")
        return
        
    try:
        df_laporan = hard_coded_rule_extractor_robust(df_aligned, template_target)
        print(f"[3] Ekstraksi HCRE Sukses. Menghasilkan Laporan.")
        print(df_laporan.to_string(index=False))
    except Exception as e:
        print(f"[!] Fatal Error Dihindari (Graceful Exit): {str(e)}")
        
    print(f"=========================================================")
    print(f"Waktu Komputasi Total: {time.time() - start_time:.5f} detik")

if __name__ == "__main__":
    csv_file = "testing/data_mahasiswa_mentah.csv"
    if os.path.exists(csv_file):
        run_pilar3_pipeline(csv_file)
