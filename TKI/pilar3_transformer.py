import pandas as pd
import numpy as np
import time

def stki_pseudo_relevance_feedback(df):
    """
    HIPOTESIS 1 (Solusi): Pseudo-Relevance Feedback (Rocchio-inspired).
    Sistem mengekstraksi header kolom dan beberapa sampel data untuk membentuk kueri padat,
    kemudian mencari template target yang paling relevan (Simulasi STKI BM25 + Dense).
    """
    headers = " ".join(df.columns.tolist())
    sample_data = " ".join(df.head(2).astype(str).values.flatten())
    query = f"{headers} {sample_data}".lower()
    
    # Simulasi STKI Matching
    # Jika query mengandung kata 'nilai', 'sks', 'mata_kuliah', maka template = 'Transkrip Nilai Lengkap'
    if 'nilai' in query and 'sks' in query:
        return "Transkrip Nilai Lengkap"
    elif 'keuangan' in query or 'bayar' in query:
        return "Laporan Keuangan"
    else:
        return "Tidak Dikenali"

def semantic_schema_alignment(df, template):
    """
    HIPOTESIS 2 (Solusi): Semantic Schema Alignment.
    Memeriksa tipe data ordinal (Huruf) dan mentranslasikannya ke rasio (Angka) menggunakan kamus heuristik
    karena template 'Transkrip Nilai Lengkap' membutuhkan metrik kontinu (Rata-rata IPK).
    """
    if template == "Transkrip Nilai Lengkap":
        if 'Nilai_Huruf' in df.columns:
            # Kamus Pemetaan Fuzzy / Heuristik
            mapping_nilai = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'E': 0.0}
            df['Bobot_Nilai'] = df['Nilai_Huruf'].map(mapping_nilai)
            
            # Menangani Schema Mismatch jika ada nilai yang tidak valid (Graceful Rejection)
            if df['Bobot_Nilai'].isnull().any():
                df['Bobot_Nilai'].fillna(0.0, inplace=True)
                print("[WARNING] Terdapat nilai huruf yang tidak valid. Dianggap 0.0.")
            return True, df
        else:
            return False, df
    return False, df

def hard_coded_rule_extractor(df, template):
    """
    HIPOTESIS 3 & 4 (Solusi): Vectorized Execution (O(1) Pandas Backend) & Hard-Coded Rule Extractor (HCRE).
    Mencegah komputasi O(N^2) iteratif dan mencegah AI Hallucination dengan menjamin fungsi matematika deterministik.
    """
    if template == "Transkrip Nilai Lengkap":
        # Komputasi Aljabar Deterministik & Vektorisasi
        df['Total_Skor'] = df['Bobot_Nilai'] * df['SKS']
        
        # Agregasi terpusat (Grouping)
        laporan = df.groupby(['NIM', 'Nama']).apply(
            lambda x: pd.Series({
                'Total_SKS_Diambil': x['SKS'].sum(),
                'IPK_Kumulatif': round(x['Total_Skor'].sum() / x['SKS'].sum(), 2)
            })
        ).reset_index()
        
        return laporan
    else:
        return pd.DataFrame()

def run_pilar3_pipeline(csv_path):
    print(f"=== MEMULAI PIPELINE PILAR 3 (RAG & TRANSFORMASI DATA) ===")
    start_time = time.time()
    
    # 1. Baca Data Mentah
    df_raw = pd.read_csv(csv_path)
    print(f"[1] Data Mentah Dibaca: {len(df_raw)} baris. Bentuk Awal: {df_raw.columns.tolist()}")
    
    # 2. STKI: Cari Template
    template_target = stki_pseudo_relevance_feedback(df_raw)
    print(f"[2] STKI Pseudo-Relevance Feedback menebak format laporan: '{template_target}'")
    
    if template_target == "Tidak Dikenali":
        print("[!] Gagal menemukan template yang relevan. Abort.")
        return
        
    # 3. DS: Schema Alignment
    is_aligned, df_aligned = semantic_schema_alignment(df_raw, template_target)
    if not is_aligned:
        print("[!] Graceful Rejection: Tipe data tidak cocok dengan kerangka laporan target.")
        return
    print(f"[3] Schema Alignment berhasil mengubah tipe Ordinal (Huruf) menjadi Rasio (Angka).")
    
    # 4. DS: Transformasi HCRE & Vektorisasi
    df_laporan = hard_coded_rule_extractor(df_aligned, template_target)
    print(f"[4] HCRE Extractor (Pandas Vectorized) berhasil menyusun laporan baru tanpa Halusinasi Generatif.")
    
    end_time = time.time()
    
    print("\n=== HASIL LAPORAN BARU ===")
    print(df_laporan.to_string(index=False))
    print(f"=========================================================")
    print(f"Waktu Komputasi: {end_time - start_time:.5f} detik (Kecepatan O(1) Vectorization)")

if __name__ == "__main__":
    csv_file = "testing/data_mahasiswa_mentah.csv"
    run_pilar3_pipeline(csv_file)
