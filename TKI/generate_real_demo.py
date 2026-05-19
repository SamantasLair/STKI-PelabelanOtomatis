import os
import sqlite3
import json
import numpy as np

# Konfigurasi Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
ONNX_DIR = os.path.join(ROOT_DIR, "STKI", "onnx_model")
ONNX_FILE = os.path.join(ONNX_DIR, "multi_label_model.onnx")
DB_REAL_PATH = os.path.join(ROOT_DIR, "academic_demo_real.db")

# Inisialisasi ONNX Engine Lokal untuk generate embedding
import onnxruntime as ort
from transformers import AutoTokenizer

session = ort.InferenceSession(ONNX_FILE, providers=['CPUExecutionProvider'])
tokenizer = AutoTokenizer.from_pretrained(ONNX_DIR)

def get_onnx_embedding(text):
    inputs = tokenizer(
        text,
        return_tensors="np",
        padding="max_length",
        truncation=True,
        max_length=256
    )
    input_ids = inputs["input_ids"].astype(np.int64)
    attention_mask = inputs["attention_mask"].astype(np.int64)
    outputs = session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
    logits = outputs[0].squeeze()
    probs = 1.0 / (1.0 + np.exp(-logits))
    return probs

def generate_real_dataset():
    print("[INFO] Menghimpun data skripsi, dataset riset, jurnal sinta, dan artikel konferensi asli...")
    
    real_researchers = [
        {"name": "Prof. Dr. Eng. Wisnu Jatmiko", "spec": "Kecerdasan Artifisial, Deep Learning", "univ": "Universitas Indonesia"},
        {"name": "Prof. Dr. Ir. Riri Fitri Sari", "spec": "Jaringan Komputer, Internet of Things", "univ": "Universitas Indonesia"},
        {"name": "Dr. Eng. Ayu Purwarianti", "spec": "Natural Language Processing", "univ": "Institut Teknologi Bandung"},
        {"name": "Prof. Dr. Eng. Khairurrijal", "spec": "Fisika Komputasi, Material Maju", "univ": "Institut Teknologi Bandung"},
        {"name": "Dr. Techn. Khabib Mustofa", "spec": "Sistem Informasi, Semantic Web", "univ": "Universitas Gadjah Mada"},
        {"name": "Prof. Dr. Edi Winarko", "spec": "Data Mining, Big Data Analytics", "univ": "Universitas Gadjah Mada"},
        {"name": "Dr. Eng. Wahyudi Hasbi", "spec": "Teknologi Satelit, Sensor Telekomunikasi", "univ": "LAPAN / BRIN"},
        {"name": "Dr. Oky Dwi Nurhayati", "spec": "Pengolahan Citra Digital, Sistem Pakar", "univ": "Universitas Diponegoro"},
        {"name": "Prof. Ir. Zainal Arifin Hasibuan Ph.D.", "spec": "Tata Kelola TI, Enterprise Architecture", "univ": "Universitas Indonesia"},
        {"name": "Dr. Ahmad Ridwan M.T.", "spec": "Cloud Computing, IoT Terdistribusi", "univ": "Universitas Sebelas Maret"}
    ]

    # Taksonomi Eksklusif Skenario Demo Real (Total 20 Label sesuai Rice Rule untuk N=1000)
    # L1 (3 kelas), L2 (17 kelas)
    l1_labels = [
        "Skripsi & Tugas Akhir", 
        "Dataset & Publikasi Riset", 
        "Jurnal & Artikel Ilmiah"
    ]
    
    l2_labels = [
        "Skripsi Informatika", "Skripsi Sistem Informasi", "Skripsi Teknik Komputer",
        "Dataset Citra Medis", "Dataset Teks Indonesia", "Dataset Sensor IoT",
        "Jurnal Sinta 1 Gold", "Jurnal Sinta 2 Silver", "Jurnal Sinta 3 Bronze",
        "Artikel Konferensi IEEE", "Artikel Prosiding Nasional", "Laporan Pengabdian",
        "Proposal Hibah Riset", "Monograf Buku Ajar", "Paten HAKI Terdaftar",
        "Hak Cipta Software", "Desain Industri"
    ]

    samples = []
    
    # KATEGORI 1: Skripsi & Tugas Akhir (350 Berkas)
    # L1: Skripsi & Tugas Akhir
    # L2: Skripsi Informatika, Skripsi Sistem Informasi, Skripsi Teknik Komputer (3 L2 Classes)
    for i in range(350):
        res = real_researchers[i % len(real_researchers)]
        ext = [".pdf", ".docx", ".xlsx", ".csv"][i % 4]
        
        l2_choice = [
            "Skripsi Informatika", "Skripsi Sistem Informasi", "Skripsi Teknik Komputer"
        ][i % 3]
        
        title_topic = [
            "Analisis Sentimen Ulasan Kampus Menggunakan Arsitektur Long Short-Term Memory",
            "Perancangan Enterprise Architecture Sistem Akademik Kampus Menggunakan TOGAF ADM",
            "Prototipe Sistem Deteksi Kebocoran Gas Berbasis IoT dan Protokol MQTT",
            "Optimasi Algoritma Genetika untuk Penjadwalan Mata Kuliah S1 Otomatis",
            "Implementasi Kriptografi AES-256 untuk Pengamanan Berkas Transkrip Mahasiswa",
            "Penerapan Metode K-Means untuk Klasterisasi Kelayakan Penerimaan Beasiswa UKT",
            "Klasifikasi Citra X-Ray Paru-Paru dengan Convolutional Neural Network MobileNet",
            "Rancang Bangun Aplikasi Monitoring Kesehatan Berbasis Flutter dan Firebase",
            "Implementasi Algoritma Dijkstra untuk Pencarian Rute Terpendek Jalur Distribusi",
            "Analisis Perbandingan Kinerja Protokol Routing OSPF dan EIGRP pada Jaringan Kampus"
        ][i % 10]

        if ext in [".xlsx", ".csv"]:
            content = f"METADATA TUGAS AKHIR MAHASISWA. Nama Peneliti: {res['name']}_{i} | Prodi TA: {l2_choice} | Judul Skripsi: {title_topic} | Tahun: 2026."
        else:
            content = f"Dokumen Skripsi dan Tugas Akhir Sarjana S1. Dikerjakan oleh {res['name']}_{i} dari program studi {l2_choice}. Karya ilmiah ini berjudul '{title_topic}' dan diserahkan secara resmi untuk memenuhi syarat kelulusan gelar Sarjana."
            
        samples.append({
            "filename": f"skripsi_{res['name'].lower().replace(' ', '_').replace('.', '')}_{i}{ext}",
            "content": content,
            "labels": ["Skripsi & Tugas Akhir", l2_choice]
        })

    # KATEGORI 2: Dataset & Publikasi Riset (350 Berkas)
    # L1: Dataset & Publikasi Riset
    # L2: Dataset Citra Medis, Dataset Teks Indonesia, Dataset Sensor IoT, Paten HAKI Terdaftar, Hak Cipta Software, Desain Industri, Proposal Hibah Riset (7 L2 Classes)
    for i in range(350):
        res = real_researchers[i % len(real_researchers)]
        ext = [".xlsx", ".csv", ".pdf", ".docx"][i % 4]
        
        l2_choice = [
            "Dataset Citra Medis", "Dataset Teks Indonesia", "Dataset Sensor IoT",
            "Paten HAKI Terdaftar", "Hak Cipta Software", "Desain Industri", "Proposal Hibah Riset"
        ][i % 7]
        
        inv_topic = [
            "Dataset Citra CT-Scan Otak untuk Klasifikasi Tumor Ganas 3D",
            "Korpus 10.000 Kalimat Percakapan Bahasa Gaul Terjemahan Formal Indonesia",
            "Dataset Log Sensor Suhu Kelembaban Tanah Pertanian Cerdas 12 Bulan",
            "Metode Pemrosesan Sinyal Multikalibrasi untuk Sensor Kimia Elektroda",
            "Aplikasi Mobile Asisten Virtual AI Pendeteksi Kualitas Tidur",
            "Casing Ergonomis Perangkat IoT Sensor Tanah untuk Pertanian Cerdas",
            "Proposal Hibah Riset Pendeteksian Kebocoran Pipa Minyak Bawah Tanah"
        ][i % 7]
        
        if ext in [".xlsx", ".csv"]:
            content = f"REKAPITULASI ASET RISET. Inventor: {res['name']}_{i} | Klasifikasi: {l2_choice} | Judul Aset/Dataset: {inv_topic} | Registrasi resmi."
        else:
            content = f"Dokumen Rekapitulasi Dataset dan Kekayaan Intelektual Peneliti. Penulis Utama {res['name']}_{i} terafiliasi dengan {res['univ']}. Luaran riset fungsional ini berupa {l2_choice} dengan nama aset '{inv_topic}' yang memiliki nilai keilmuan tinggi."
            
        samples.append({
            "filename": f"dataset_riset_{res['name'].lower().replace(' ', '_').replace('.', '')}_{i}{ext}",
            "content": content,
            "labels": ["Dataset & Publikasi Riset", l2_choice]
        })

    # KATEGORI 3: Jurnal & Artikel Ilmiah (300 Berkas)
    # L1: Jurnal & Artikel Ilmiah
    # L2: Jurnal Sinta 1 Gold, Jurnal Sinta 2 Silver, Jurnal Sinta 3 Bronze, Artikel Konferensi IEEE, Artikel Prosiding Nasional, Laporan Pengabdian, Monograf Buku Ajar (7 L2 Classes)
    for i in range(300):
        res = real_researchers[i % len(real_researchers)]
        ext = [".xlsx", ".csv", ".pdf", ".docx"][i % 4]
        
        l2_choice = [
            "Jurnal Sinta 1 Gold", "Jurnal Sinta 2 Silver", "Jurnal Sinta 3 Bronze",
            "Artikel Konferensi IEEE", "Artikel Prosiding Nasional", "Laporan Pengabdian", "Monograf Buku Ajar"
        ][i % 7]
        
        dev_topic = [
            "Sintesis Nanomaterial Karbon Aktif untuk Superkapasitor Berdaya Tinggi",
            "Ekstraksi Entitas Bernama Bahasa Indonesia dengan Arsitektur BERT",
            "Analisis Penyeimbangan Beban Jaringan Komputasi Awan Edge Computing",
            "Robust Cryptographic Keys for Satellite Communication Node Nodes",
            "Penerapan Pembangkit Listrik Tenaga Surya di Dusun Terpencil",
            "Pelatihan Literasi Digital dan Keamanan Transaksi E-Commerce bagi UMKM",
            "Buku Ajar Pengantar Sistem Temu Kembali Informasi Semantik"
        ][i % 7]
        
        if ext in [".xlsx", ".csv"]:
            content = f"REKAP PUBLIKASI ILMIAH. Pelaksana: {res['name']}_{i} | Penerbit Jurnal: {l2_choice} | Judul Publikasi: {dev_topic} | Indeks Prestasi."
        else:
            content = f"Laporan Publikasi Hasil Penelitian Ilmiah Dosen Tetap. Penulis Utama {res['name']}_{i} terafiliasi dengan {res['univ']}. Makalah ilmiah ini berjudul '{dev_topic}' dan telah resmi diterbitkan dalam {l2_choice}."
            
        samples.append({
            "filename": f"jurnal_artikel_{res['name'].lower().replace(' ', '_').replace('.', '')}_{i}{ext}",
            "content": content,
            "labels": ["Jurnal & Artikel Ilmiah", l2_choice]
        })

    # Simpan ke Database
    print(f"[INFO] Menyimpan {len(samples)} data asli ke database {DB_REAL_PATH}...")
    conn = sqlite3.connect(DB_REAL_PATH)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS documents")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            content TEXT,
            labels TEXT,
            embedding TEXT
        )
    """)
    conn.commit()
    
    # Batched inserts
    for idx, s in enumerate(samples):
        emb = get_onnx_embedding(s["content"]).tolist()
        cursor.execute("""
            INSERT OR REPLACE INTO documents (filename, content, labels, embedding)
            VALUES (?, ?, ?, ?)
        """, (s["filename"], s["content"], json.dumps(s["labels"]), json.dumps(emb)))
        if (idx + 1) % 100 == 0:
            print(f"[INFO] Terproses: {idx + 1}/1000 dokumen...")
            
    conn.commit()
    conn.close()
    print("[SUKSES] Database Demo Real 1.000 data berhasil dibangkitkan dengan 20 taksonomi unik skripsi/dataset/jurnal/artikel!")

if __name__ == "__main__":
    generate_real_dataset()
