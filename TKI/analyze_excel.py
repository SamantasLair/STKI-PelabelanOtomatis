import os
import sys
import numpy as np
import json

# 1. Penanganan Dependency Otomatis
try:
    import pandas as pd
    import onnxruntime as ort
    from transformers import AutoTokenizer
except ImportError:
    print("[INFO] Dependency belum lengkap. Menginstall library pendukung...")
    os.system("pip install --user -q pandas onnxruntime transformers")
    import pandas as pd
    import onnxruntime as ort
    from transformers import AutoTokenizer

# Definisikan Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
ONNX_DIR = os.path.join(ROOT_DIR, "STKI", "onnx_model")
ONNX_FILE = os.path.join(ONNX_DIR, "multi_label_model.onnx")

print("="*80)
print("SISTEM ANALISIS & PELABELAN EXCEL OTOMATIS (MULTI-LAYER SCANNER)")
print("="*80 + "\n")

# 2. Validasi Keberadaan Model
if not os.path.exists(ONNX_FILE):
    print(f"[ERROR] Berkas model ONNX tidak ditemukan di: {ONNX_FILE}")
    print("Silakan jalankan skrip 'STKI/test_onnx_local.py' terlebih dahulu untuk mengekstrak model.")
    sys.exit(1)

# 3. Memuat Model dan Tokenizer
print("Memuat Model ONNX dan Tokenizer ke memori...")
try:
    session = ort.InferenceSession(ONNX_FILE, providers=['CPUExecutionProvider'])
    # Memuat tokenizer dari folder hasil ekstrak zip
    tokenizer = AutoTokenizer.from_pretrained(ONNX_DIR)
    print("Model & Tokenizer berhasil dimuat! [SUKSES]\n")
except Exception as e:
    print(f"[ERROR] Gagal memuat model/tokenizer: {e}")
    sys.exit(1)

# 4. Fungsi Helper: Ekstraksi Representasi Semantik (Embedding) via ONNX
def get_onnx_embedding(text):
    # Tokenisasi teks input
    inputs = tokenizer(
        text, 
        return_tensors="np", 
        padding="max_length", 
        truncation=True, 
        max_length=256
    )
    
    # Ambil input ids dan attention mask
    input_ids = inputs["input_ids"].astype(np.int64)
    attention_mask = inputs["attention_mask"].astype(np.int64)
    
    # Model BERT-mini di notebook kita diekspor dengan multi-label logits,
    # tetapi untuk Zero-Shot Embedding kita bisa menghitung Cosine Similarity 
    # langsung dari logits/representasi atau kita jalankan inferensi.
    # Karena BERT-mini mengembalikan logits klasifikasi berdimensi 5, kita bisa menggunakan
    # logits tersebut sebagai penanda semantik (vektor identitas makna berdimensi 5!).
    outputs = session.run(
        None, 
        {
            "input_ids": input_ids,
            "attention_mask": attention_mask
        }
    )
    # outputs[0] adalah logits berdimensi (1, 5)
    return outputs[0].squeeze()

# Fungsi menghitung Cosine Similarity secara manual
def cosine_similarity_1d(v1, v2):
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

# 5. Fungsi Parsing Semantik Dokumen Excel
def parse_excel_to_text(file_path):
    try:
        df = pd.read_excel(file_path)
        cols = ", ".join(df.columns.astype(str).tolist())
        # Ambil cuplikan baris data pertama secara tekstual
        row_samples = []
        if not df.empty:
            for idx, row in df.head(3).iterrows():
                row_str = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                row_samples.append(f"Baris {idx+1}: {row_str}")
        
        sample_text = " // ".join(row_samples)
        
        # Susun teks semantik yang mewakili dokumen excel
        semantic_summary = (
            f"Dokumen spreadsheet tabel akademis kampus. "
            f"Daftar kolom struktur metadata: {cols}. "
            f"Cuplikan sampel isi berkas: {sample_text}."
        )
        return semantic_summary, df.columns.tolist()
    except Exception as e:
        print(f"[ERROR] Gagal membaca berkas Excel {file_path}: {e}")
        return None, None

# 6. Daftar Taksonomi Label Multi-Layer (Sesuai Kebutuhan Civitas Akademika)
TAXONOMY = {
    "Layer_1_Domain": [
        "Akademik Mahasiswa",
        "Administrasi Dosen",
        "Jadwal dan SKS Perkuliahan"
    ],
    "Layer_2_Detail": [
        "Transkrip Nilai Lengkap",
        "KRS SKS Kelas",
        "Daftar Dosen Pengajar",
        "Laporan Keuangan",
        "Kurikulum Jurusan"
    ]
}

# 7. Fungsi Klasifikasi Multi-Layer Dinamis
def analyze_and_label_excel(file_path):
    print("-" * 80)
    print(f"MENGANALISIS BERKAS: {os.path.basename(file_path)}")
    print("-" * 80)
    
    # A. Parse berkas Excel menjadi rangkuman teks semantik
    semantic_text, columns = parse_excel_to_text(file_path)
    if semantic_text is None:
        return
        
    print(f"Struktur Kolom Terdeteksi: {columns}")
    print(f"Representasi Semantik Teks  : {semantic_text[:120]}...\n")
    
    # B. Hitung embedding ONNX untuk dokumen excel
    doc_vector = get_onnx_embedding(semantic_text)
    
    # C. Kalkulasi Layer 1: Domain/Konteks
    print("EVALUASI LAYER 1: Domain / Konteks Makro")
    l1_results = []
    for l1_label in TAXONOMY["Layer_1_Domain"]:
        label_vector = get_onnx_embedding(l1_label)
        similarity = cosine_similarity_1d(doc_vector, label_vector)
        # Normalisasi skor cos_sim desimal ke persentase positif 0-100%
        normalized_score = max(0.0, similarity * 100.0)
        l1_results.append((l1_label, normalized_score))
        
    l1_results = sorted(l1_results, key=lambda x: x[1], reverse=True)
    for i, (label, score) in enumerate(l1_results):
        print(f"  [{i+1:02d}] Label: {label: <30} | Skor Kemiripan: {score:05.2f}%")
        
    # Pilih Domain Utama (Skor Tertinggi dan > 30%)
    best_l1_label, best_l1_score = l1_results[0]
    assigned_l1 = best_l1_label if best_l1_score > 30.0 else "Tidak Terklasifikasi"
    print(f"==> KEPUTUSAN LAYER 1: Terpetakan ke domain '{assigned_l1}' (Skor: {best_l1_score:05.2f}%)\n")
    
    # D. Kalkulasi Layer 2: Tipe Berkas / Aksi Mikro
    print("EVALUASI LAYER 2: Tipe Berkas / Aksi Mikro")
    l2_results = []
    for l2_label in TAXONOMY["Layer_2_Detail"]:
        label_vector = get_onnx_embedding(l2_label)
        similarity = cosine_similarity_1d(doc_vector, label_vector)
        normalized_score = max(0.0, similarity * 100.0)
        l2_results.append((l2_label, normalized_score))
        
    l2_results = sorted(l2_results, key=lambda x: x[1], reverse=True)
    for i, (label, score) in enumerate(l2_results):
        print(f"  [{i+1:02d}] Label: {label: <30} | Skor Kemiripan: {score:05.2f}%")
        
    best_l2_label, best_l2_score = l2_results[0]
    assigned_l2 = best_l2_label if best_l2_score > 35.0 else "Tidak Terklasifikasi"
    print(f"==> KEPUTUSAN LAYER 2: Terpetakan ke tipe '{assigned_l2}' (Skor: {best_l2_score:05.2f}%)\n")
    
    # E. Kesimpulan Pelabelan Akhir
    print("KESIMPULAN PELABELAN MULTI-LAYER:")
    print("*" * 50)
    print(f"Berkas           : {os.path.basename(file_path)}")
    print(f"Label Layer 1    : {assigned_l1}")
    print(f"Label Layer 2    : {assigned_l2}")
    print("*" * 50 + "\n")

# 8. Menu Utama Uji Coba Berkas
if __name__ == "__main__":
    # Cari berkas sampel excel di folder TKI
    excel_files = [
        os.path.join(CURRENT_DIR, "data_mahasiswa.xlsx"),
        os.path.join(CURRENT_DIR, "data_sks.xlsx"),
        os.path.join(CURRENT_DIR, "daftar_dosen.xlsx")
    ]
    
    # Validasi apakah berkas sampel sudah ada
    samples_exist = all([os.path.exists(f) for f in excel_files])
    
    if not samples_exist:
        print("[PERINGATAN] Berkas sampel Excel belum terbuat.")
        print("Menjalankan generator sampel 'TKI/generate_samples.py' otomatis...")
        os.system(f"python {os.path.join(CURRENT_DIR, 'generate_samples.py')}")
        print("\n")
        
    # Lakukan evaluasi secara sekaligus (Batch/Bulk Processing)
    print("MEMULAI EVALUASI SECARA SEKALIGUS (BATCH EVALUATION):")
    print("=" * 80)
    for f_path in excel_files:
        if os.path.exists(f_path):
            analyze_and_label_excel(f_path)
            
    print("=" * 80)
    print("UJI COBA ANALISIS & PELABELAN EXCEL MULTI-LAYER SELESAI! [SUKSES]")
    print("=" * 80)
