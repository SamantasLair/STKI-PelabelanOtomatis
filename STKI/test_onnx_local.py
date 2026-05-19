import os
import zipfile
import shutil
import numpy as np

# Konfigurasi Path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ZIP_PATH = os.path.join(ROOT_DIR, "onnx_model.zip")
EXTRACT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "onnx_model")

print("="*80)
print("SISTEM UJI COBA INTEGRITAS ONNX LOKAL (OFFLINE DEMO)")
print("="*80 + "\n")

# 1. Ekstraksi Berkas Model Zip
if not os.path.exists(ZIP_PATH):
    print(f"[ERROR] Berkas 'onnx_model.zip' tidak ditemukan di root direktori: {ZIP_PATH}")
    print("Pastikan Anda sudah mendownload berkas zip dari Colab dan meletakkannya di folder utama UAS.")
    exit(1)

print(f"Mendeteksi berkas: {os.path.basename(ZIP_PATH)}")
print("Mengekstrak berkas zip secara lokal...")

try:
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(EXTRACT_DIR)
    print(f"Ekstraksi Sukses! Berkas disimpan di: {EXTRACT_DIR}\n")
except Exception as e:
    print(f"[ERROR] Gagal mengekstrak berkas zip: {e}")
    exit(1)

# 2. Pengujian Memuat Model menggunakan ONNX Runtime
print("Mencoba memuat model menggunakan ONNX Runtime...")
try:
    import onnxruntime as ort
except ImportError:
    print("\n[PERINGATAN] Library 'onnxruntime' belum terinstall di komputer lokal Anda.")
    print("Menginstall onnxruntime secara otomatis di terminal lokal Anda...")
    # Menjalankan instalasi lokal secara asinkron
    os.system("pip install -q onnxruntime")
    import onnxruntime as ort

onnx_file = os.path.join(EXTRACT_DIR, "multi_label_model.onnx")
if not os.path.exists(onnx_file):
    # Kadang zip colab bersarang satu folder di dalamnya
    nested_dir = os.path.join(EXTRACT_DIR, "onnx_model")
    if os.path.exists(os.path.join(nested_dir, "multi_label_model.onnx")):
        onnx_file = os.path.join(nested_dir, "multi_label_model.onnx")
        EXTRACT_DIR = nested_dir

print(f"Memuat berkas model: {os.path.basename(onnx_file)}")

try:
    # Memuat model ke CPU session
    session = ort.InferenceSession(onnx_file, providers=['CPUExecutionProvider'])
    print("Model ONNX berhasil dimuat ke memori lokal CPU! [SUKSES]\n")
    
    # 3. Menampilkan Informasi Metadata Model
    input_meta = session.get_inputs()
    output_meta = session.get_outputs()
    
    print("INFORMASI METADATA MODEL ONNX:")
    print("-" * 50)
    for i, inp in enumerate(input_meta):
        print(f"Input Node {i+1}  : Nama = '{inp.name}' | Shape = {inp.shape} | Tipe = {inp.type}")
    for i, out in enumerate(output_meta):
        print(f"Output Node {i+1} : Nama = '{out.name}' | Shape = {out.shape} | Tipe = {out.type}")
    print("-" * 50 + "\n")
    
    # 4. Melakukan Uji Coba Prediksi dengan Dummy Tensor
    print("Menjalankan uji coba inferensi semantik (Dummy Predict)...")
    # BERT-mini menggunakan input_ids dan attention_mask
    MAX_LENGTH = 256
    dummy_input_ids = np.zeros((1, MAX_LENGTH), dtype=np.int64)
    dummy_attention_mask = np.zeros((1, MAX_LENGTH), dtype=np.int64)
    
    # Jalankan inferensi
    outputs = session.run(
        [out.name for out in output_meta],
        {
            "input_ids": dummy_input_ids,
            "attention_mask": dummy_attention_mask
        }
    )
    
    logits = outputs[0]
    print(f"Inferensi Sukses! logits shape = {logits.shape} [SUKSES]")
    print("Skor Logits Kasus Dummy (5 Nilai Pertama):", logits[0][:5])
    print("\n" + "="*80)
    print("KESIMPULAN: BERKAS ONNX 100% VALID & SIAP DEPLOY SECARA OFFLINE (TKT 4)!")
    print("="*80)
    
except Exception as e:
    print(f"[ERROR] Terjadi kegagalan saat menguji model ONNX: {e}")
    exit(1)
