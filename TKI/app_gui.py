import os
import sys
import re
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import numpy as np
import pandas as pd
import sqlite3
import json

# Penanganan Pustaka Otomatis
try:
    import onnxruntime as ort
    from transformers import AutoTokenizer
except ImportError:
    import sys
    import os
    os.system(f'"{sys.executable}" -m pip install --user -q onnxruntime transformers')
    import onnxruntime as ort
    from transformers import AutoTokenizer

# Konfigurasi Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
ONNX_DIR = os.path.join(ROOT_DIR, "STKI", "onnx_model")
ONNX_FILE = os.path.join(ONNX_DIR, "multi_label_model.onnx")
DB_PATH = os.path.join(ROOT_DIR, "academic_metadata.db")
DB_REAL_PATH = os.path.join(ROOT_DIR, "academic_demo_real.db")

# Pastikan 3 Berkas Sampel Excel Sudah Terbuat
excel_files = [
    os.path.join(CURRENT_DIR, "data_mahasiswa.xlsx"),
    os.path.join(CURRENT_DIR, "data_sks.xlsx"),
    os.path.join(CURRENT_DIR, "daftar_dosen.xlsx")
]
if not all([os.path.exists(f) for f in excel_files]):
    # Jalankan generator sampel jika belum ada
    os.system(f"python {os.path.join(CURRENT_DIR, 'generate_samples.py')}")

# =====================================================================
# CORE ENGINE: ONNX & PARSING
# =====================================================================
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

# Fungsi Ekstraksi Makna Semantik via ONNX
def get_onnx_embedding(text):
    if session is None or tokenizer is None:
        return np.zeros(5)
    distilled_text = extract_key_sentences(text, num_sentences=5)
    inputs = tokenizer(distilled_text, return_tensors="np", padding="max_length", truncation=True, max_length=256)
    input_ids = inputs["input_ids"].astype(np.int64)
    attention_mask = inputs["attention_mask"].astype(np.int64)
    outputs = session.run(None, {"input_ids": input_ids, "attention_mask": attention_mask})
    logits = outputs[0].squeeze()
    # Terapkan aktivasi Sigmoid dengan Thresholding Kalibrasi Temperatur (T=2.0)
    # untuk meredam dominasi magnitudo bias pada OOD.
    probs = 1.0 / (1.0 + np.exp(-logits / 2.0))
    return probs


def init_onnx_engine():
    global session, tokenizer, v_null
    if not os.path.exists(ONNX_FILE):
        return False
    try:
        session = ort.InferenceSession(ONNX_FILE, providers=['CPUExecutionProvider'])
        tokenizer = AutoTokenizer.from_pretrained(ONNX_DIR)
        # Hitung null embedding untuk mendeteksi baseline bias model
        v_null = get_onnx_embedding("")
        return True
    except Exception as e:
        print(f"Error loading ONNX engine: {e}")
        return False

# Panggil mesin inisialisasi awal
onnx_ready = init_onnx_engine()

# Cosine Similarity
def get_cosine_similarity(v1, v2):
    global v_null
    if v_null is None:
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        return float(dot_product / (norm_v1 * norm_v2))
    
    # Thresholded Positive Deviation Cosine Similarity (TPD-Cosine Similarity)
    # Mengurangi baseline bias model (v_null) dan melakukan thresholding pada nilai deviasi positif
    v1_c = np.where(v1 - v_null >= 0.02, v1 - v_null, 0.0)
    v2_c = np.where(v2 - v_null >= 0.02, v2 - v_null, 0.0)
    norm_v1 = np.linalg.norm(v1_c)
    norm_v2 = np.linalg.norm(v2_c)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(np.dot(v1_c, v2_c) / (norm_v1 * norm_v2))

def has_keyword(text_lower, keyword):
    if len(keyword) <= 5:
        pattern = rf"\b{re.escape(keyword)}\b"
        return bool(re.search(pattern, text_lower))
    else:
        return keyword in text_lower

# Kelas BM25 untuk Sparse Lexical Retrieval
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
            # Formula IDF Standard dengan smoothing
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

# Inisialisasi & Seeding Database SQLite
def init_and_seed_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
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
    
    # Cek apakah kosong
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    
    if count == 0:
        print("[INFO] Database kosong. Melakukan seeding 1.000 dokumen akademik sampel...")
        samples = []
        mhs_pool = [
            "Budi Santoso", "Kurnia Putri", "Ahmad Fauzi", "Rina Wijaya", 
            "Hendra Wijaya", "Siti Aminah", "Dewi Lestari", "Rian Hidayat", 
            "Fajar Pratama", "Novi Anggraini", "Bambang Pamungkas", "Eka Sari", 
            "Adi Saputra", "Taufik Hidayat", "Lestari Putri", "Joko Widodo",
            "Megawati Sukarno", "SBY Susilo", "Prabowo Subianto", "Gibran Rakabuming"
        ]
        
        dosen_names = [
            "Dr. Eng. Hermawan", "Prof. Dr. Sri Utami", "Diana Putri M.T.",
            "Rudi Hermawan Ph.D.", "Dr. Ahmad Fauzan", "Siti Rahma M.Cs.",
            "Hadi Wijaya M.T.", "Indra Lesmana Ph.D.", "Fitri Handayani M.T.",
            "Prof. Dr. Anwar Ibrahim"
        ]
        
        # 1. Transkrip Nilai (250 Dokumen)
        for i in range(250):
            name = mhs_pool[i % len(mhs_pool)]
            ext = [".pdf", ".docx", ".xlsx", ".csv"][i % 4]
            nim = f"101230{i+1:03d}"
            gpa = round(3.0 + (i % 100) * 0.01, 2)
            if ext in [".xlsx", ".csv"]:
                content = f"TABEL DATA TRANSKRIP AKADEMIK. NIM: {nim} | Nama: {name}_{i} | Prodi: Informatika | IPK: {gpa} | Mata Kuliah: Aljabar Linier (A), Kalkulus 2 (B), Struktur Data (B+)."
            else:
                content = f"Dokumen Transkrip Nilai Resmi Mahasiswa atas nama {name}_{i} dengan NIM {nim} Program Studi Informatika. Meraih IPK kumulatif sebesar {gpa} dengan predikat sangat memuaskan."
            
            samples.append({
                "filename": f"transkrip_{name.lower().replace(' ', '_')}_{i}{ext}",
                "content": content,
                "labels": ["Akademik Mahasiswa", "Transkrip Nilai Lengkap"]
            })
            
        # 2. KRS SKS Kelas (250 Dokumen)
        for i in range(250):
            name = mhs_pool[i % len(mhs_pool)]
            ext = [".xlsx", ".csv", ".pdf", ".docx"][i % 4]
            courses = "Struktur Data, Matematika Diskrit, Pemrograman Web"
            sks = 18 + (i % 6)
            if ext in [".xlsx", ".csv"]:
                content = f"REKAP RENCANA STUDI MAHASISWA (KRS). Nama: {name}_{i} | SKS Total: {sks} | Daftar Mata Kuliah Diambil: {courses} | Status: Disetujui Dosen Wali."
            else:
                content = f"Formulir Rencana Studi Mahasiswa (KRS) untuk semester berjalan atas nama {name}_{i}. Mengambil total {sks} SKS yang terdiri dari beberapa mata kuliah utama: {courses}."
                
            samples.append({
                "filename": f"rencana_studi_{name.lower().replace(' ', '_')}_{i}{ext}",
                "content": content,
                "labels": ["Jadwal dan SKS Perkuliahan", "KRS SKS Kelas"]
            })
            
        # 3. Daftar Dosen Pengajar (250 Dokumen)
        for i in range(250):
            ext = [".pdf", ".xlsx", ".docx", ".csv"][i % 4]
            dos_name = dosen_names[i % len(dosen_names)]
            spec = ["Kecerdasan Buatan", "Kriptografi", "RPL", "Jaringan Komputer", "Basis Data"][i % 5]
            nip = f"198503122010121{i+1:03d}"
            if ext in [".xlsx", ".csv"]:
                content = f"DATABASE DOSEN JURUSAN. NIP: {nip} | Nama Dosen: {dos_name}_{i} | Bidang Spesialisasi: {spec} | Status Kepegawaian: Aktif Mengajar."
            else:
                content = f"Daftar NIP dan Nama Dosen Pengajar Fakultas Teknologi Informasi. Menugaskan {dos_name}_{i} dengan NIP {nip} selaku pengampu mata kuliah utama pada spesialisasi {spec}."
                
            samples.append({
                "filename": f"daftar_dosen_{dos_name.lower().replace('.', '').replace(' ', '_')}_{i}{ext}",
                "content": content,
                "labels": ["Administrasi Dosen", "Daftar Dosen Pengajar"]
            })
            
        # 4. Laporan Keuangan & Kurikulum (250 Dokumen)
        for i in range(250):
            ext = [".xlsx", ".csv", ".pdf", ".docx"][i % 4]
            if i % 2 == 0:
                val = 5000000 + (i * 10000)
                name = mhs_pool[i % len(mhs_pool)]
                if ext in [".xlsx", ".csv"]:
                    content = f"REKAPITULASI PEMBAYARAN UKT. Mahasiswa: {name}_{i} | Nominal: Rp {val:,} | Status: Lunas Terverifikasi Bank Mandiri."
                else:
                    content = f"Laporan Keuangan Pembayaran Uang Kuliah Tunggal (UKT) mahasiswa atas nama {name}_{i}. Tagihan sebesar Rp {val:,} dinyatakan lunas."
                    
                samples.append({
                    "filename": f"keuangan_ukt_{name.lower().replace(' ', '_')}_{i}{ext}",
                    "content": content,
                    "labels": ["Akademik Mahasiswa", "Laporan Keuangan"]
                })
            else:
                dept = ["Informatika", "Sistem Informasi", "Teknik Komputer"][i % 3]
                if ext in [".xlsx", ".csv"]:
                    content = f"STRUKTUR SILABUS DAN MATAKULIAH. Jurusan: {dept} | Kode: IF-30{i} | Capaian Pembelajaran: Lulusan kompeten bidang rekayasa teknologi."
                else:
                    content = f"Silabus Dokumen Kurikulum Akademik S1 Jurusan {dept}. Mengatur standar kompetensi kelulusan mahasiswa, silabus pembelajaran teori, serta penulisan skripsi akhir."
                    
                samples.append({
                    "filename": f"kurikulum_silabus_{dept.lower().replace(' ', '_')}_v{i}{ext}",
                    "content": content,
                    "labels": ["Jadwal dan SKS Perkuliahan", "Kurikulum Jurusan"]
                })
        
        for s in samples:
            emb = get_onnx_embedding(s["content"]).tolist()
            cursor.execute("""
                INSERT OR REPLACE INTO documents (filename, content, labels, embedding)
                VALUES (?, ?, ?, ?)
            """, (s["filename"], s["content"], json.dumps(s["labels"]), json.dumps(emb)))
            
        conn.commit()
        print(f"[SUKSES] Seeding {len(samples)} database selesai!")
    conn.close()

# Ekstraksi representasi semantik berkas Excel
def parse_excel_semantic(file_path):
    try:
        df = pd.read_excel(file_path)
        cols = ", ".join(df.columns.astype(str).tolist())
        row_samples = []
        if not df.empty:
            for idx, row in df.head(3).iterrows():
                row_str = " | ".join([f"{col}: {val}" for col, val in row.items() if pd.notna(val)])
                row_samples.append(f"Baris {idx+1}: {row_str}")
        sample_text = " // ".join(row_samples)
        semantic_summary = (
            f"Dokumen spreadsheet tabel akademis kampus. "
            f"Daftar kolom struktur metadata: {cols}. "
            f"Cuplikan sampel isi berkas: {sample_text}."
        )
        return semantic_summary, df.columns.tolist(), len(df)
    except Exception as e:
        return None, None, 0

# Taksonomi Kampus Multi-Layer (Skenario Utama & Demo Real)
TAXONOMY_UTAMA = {
    "Layer_1_Domain": ["Akademik Mahasiswa", "Administrasi Dosen", "Jadwal dan SKS Perkuliahan"],
    "Layer_2_Detail": ["Transkrip Nilai Lengkap", "KRS SKS Kelas", "Daftar Dosen Pengajar", "Laporan Keuangan", "Kurikulum Jurusan"]
}

TAXONOMY_DEMO = {
    "Layer_1_Domain": ["Publikasi Riset SINTA", "Kekayaan Intelektual Paten", "Pengabdian Masyarakat Abdimas"],
    "Layer_2_Detail": [
        "Jurnal Ilmiah Sinta 2", "Prosiding Konferensi IEEE", "Proposal Hibah Riset", 
        "Paten HAKI Terdaftar", "Laporan Pengabdian", "Hak Cipta Software", 
        "Jurnal Sinta 1 Gold", "Jurnal Sinta 3 Silver", "Prosiding Nasional", 
        "Paten Sederhana", "Desain Industri", "Abdimas Desa Binaan", 
        "Pelatihan Masyarakat", "Proposal Riset Mandiri", "Monograf Buku Ajar", 
        "Laporan Luaran Riset", "Reviewer Jurnal"
    ]
}

# Referensi Dinamis Global yang digunakan oleh mesin prediksi
TAXONOMY = {
    "Layer_1_Domain": list(TAXONOMY_UTAMA["Layer_1_Domain"]),
    "Layer_2_Detail": list(TAXONOMY_UTAMA["Layer_2_Detail"])
}

CHILD_TO_PARENT_MAP = {
    # Skenario Utama
    "Transkrip Nilai Lengkap": "Akademik Mahasiswa",
    "KRS SKS Kelas": "Akademik Mahasiswa",
    "Daftar Dosen Pengajar": "Administrasi Dosen",
    "Laporan Keuangan": "Akademik Mahasiswa",
    "Kurikulum Jurusan": "Jadwal dan SKS Perkuliahan",
    
    # Skenario Demo Real
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
    
    # UI Demo GUI
    "Jurnal Ilmiah Sinta 2": "Publikasi Riset SINTA",
    "Prosiding Konferensi IEEE": "Publikasi Riset SINTA",
    "Jurnal Sinta 1 Gold": "Publikasi Riset SINTA",
    "Jurnal Sinta 3 Silver": "Publikasi Riset SINTA",
    "Prosiding Nasional": "Publikasi Riset SINTA",
    "Monograf Buku Ajar": "Publikasi Riset SINTA",
    "Reviewer Jurnal": "Publikasi Riset SINTA",
    "Paten Sederhana": "Kekayaan Intelektual Paten",
    "Laporan Luaran Riset": "Kekayaan Intelektual Paten",
    "Abdimas Desa Binaan": "Pengabdian Masyarakat Abdimas",
    "Pelatihan Masyarakat": "Pengabdian Masyarakat Abdimas",
    "Proposal Riset Mandiri": "Pengabdian Masyarakat Abdimas"
}

# Premium Switch Canvas Widget
class PremiumSwitch(tk.Canvas):
    def __init__(self, parent, width=50, height=24, bg_color="#252526", active_color="#4ec9b0", inactive_color="#3e3e3f", thumb_color="#ffffff", command=None, **kwargs):
        super().__init__(parent, width=width, height=height, bg=bg_color, highlightthickness=0, cursor="hand2", **kwargs)
        self.active_color = active_color
        self.inactive_color = inactive_color
        self.thumb_color = thumb_color
        self.command = command
        self.is_active = False
        
        # Rounded pill background
        self.rect = self.create_rounded_rect(2, 2, width-2, height-2, radius=10, fill=self.inactive_color)
        # Thumb circle
        self.thumb = self.create_oval(4, 4, 20, 20, fill=self.thumb_color, outline="")
        
        self.bind("<Button-1>", self.toggle)
        
    def create_rounded_rect(self, x1, y1, x2, y2, radius=10, **kwargs):
        points = [x1+radius, y1,
                  x2-radius, y1,
                  x2, y1,
                  x2, y1+radius,
                  x2, y2-radius,
                  x2, y2,
                  x2-radius, y2,
                  x1+radius, y2,
                  x1, y2,
                  x1, y2-radius,
                  x1, y1+radius,
                  x1, y1]
        return self.create_polygon(points, **kwargs, smooth=True)

    def toggle(self, event=None):
        self.is_active = not self.is_active
        if self.is_active:
            self.itemconfig(self.rect, fill=self.active_color)
            self.coords(self.thumb, 30, 4, 46, 20)
        else:
            self.itemconfig(self.rect, fill=self.inactive_color)
            self.coords(self.thumb, 4, 4, 20, 20)
        if self.command:
            self.command(self.is_active)

# =====================================================================
# GUI DASHBOARD: PREMIUM DARK MODE
# =====================================================================
class ModernApp:
    def __init__(self, root):
        self.root = root
        self.root.title("STKI - Klasifikasi Excel Multi-Layer Offline")
        self.root.geometry("1000x720")
        self.root.resizable(False, False)
        
        # Palet Warna: VS Code Dark Mode Palette
        self.c_bg = "#1e1e1e"          # Background Utama VS Code
        self.c_card = "#252526"        # Sidebar / Frame Background VS Code
        self.c_accent_p = "#007acc"    # Biru VS Code (Primary Accent)
        self.c_accent_s = "#ce9178"    # Oranye VS Code (Secondary Accent)
        self.c_text = "#d4d4d4"        # Teks Terang Editor
        self.c_text_muted = "#858585"  # Teks Redup Line Numbers
        self.c_success = "#4ec9b0"     # Hijau-Sian VS Code (Success)
        self.c_danger = "#f48771"      # Coral Red VS Code (Error/Danger)
        
        self.root.configure(bg=self.c_bg)
        
        # Inisialisasi Database jika model ONNX siap
        if onnx_ready:
            init_and_seed_db()
        
        # Inisialisasi variabel internal
        self.selected_file_path = ""
        self.active_db_path = DB_PATH
        
        # Buat Interface
        self.build_ui()
        
        # Cek Keberadaan Model ONNX
        if not onnx_ready:
            messagebox.showerror(
                "Model ONNX Hilang!", 
                "Berkas 'multi_label_model.onnx' tidak ditemukan.\n"
                "Silakan jalankan 'test_onnx_local.py' terlebih dahulu untuk mengekstrak model."
            )

    def build_ui(self):
        # 1. HEADER PANEL
        header_frame = tk.Frame(self.root, bg=self.c_bg)
        header_frame.pack(fill="x", padx=25, pady=(15, 10))
        
        title_label = tk.Label(
            header_frame, 
            text="Sistem Klasifikasi Dokumen Excel Akademik", 
            font=("Segoe UI", 16, "bold"), 
            fg=self.c_success, 
            bg=self.c_bg
        )
        title_label.pack(anchor="w")
        
        subtitle_label = tk.Label(
            header_frame, 
            text="Penganalisis Semantik Multi-Layer Hibrida & Model Zero-Shot Berbasis ONNX (TKT 4)", 
            font=("Segoe UI", 9), 
            fg=self.c_text_muted, 
            bg=self.c_bg
        )
        subtitle_label.pack(anchor="w", pady=1)

        # 2. MAIN BENTO GRID CONTAINER
        bento_container = tk.Frame(self.root, bg=self.c_bg)
        bento_container.pack(fill="both", expand=True, padx=25, pady=(0, 15))
        
        # Configure Grid Rows and Columns
        bento_container.columnconfigure(0, weight=0, minsize=320)  # Left Panel (Input / Operations)
        bento_container.columnconfigure(1, weight=1)              # Right Column 1
        bento_container.columnconfigure(2, weight=1)              # Right Column 2
        
        bento_container.rowconfigure(0, weight=0, minsize=90)     # Row 0: Final Recommendation
        bento_container.rowconfigure(1, weight=1, minsize=220)    # Row 1: Layer 1 & Layer 2 Canvases
        bento_container.rowconfigure(2, weight=1, minsize=220)    # Row 2: Database Scanner & Utilities

        # =====================================================================
        # CARD 1: INPUT PANEL (Row 0 & 1, Column 0)
        # =====================================================================
        card_input = tk.Frame(bento_container, bg=self.c_card, bd=0, highlightthickness=1, highlightbackground="#313244")
        card_input.grid(row=0, column=0, rowspan=2, columnspan=1, padx=(0, 12), pady=(0, 12), sticky="nsew")
        
        lbl_input_title = tk.Label(
            card_input, 
            text="INPUT DOKUMEN SPREADSHEET", 
            font=("Segoe UI", 10, "bold"), 
            fg=self.c_accent_s, 
            bg=self.c_card
        )
        lbl_input_title.pack(anchor="w", padx=20, pady=(15, 8))
        
        # Browse Button
        btn_browse = tk.Button(
            card_input, 
            text="Pilih Berkas Excel / CSV", 
            font=("Segoe UI", 9, "bold"),
            fg="#11111b",
            bg=self.c_accent_p,
            activebackground="#b4befe",
            bd=0, 
            padx=15, 
            pady=8,
            cursor="hand2",
            command=self.browse_file
        )
        btn_browse.pack(fill="x", padx=20, pady=5)
        
        self.lbl_filepath = tk.Label(
            card_input, 
            text="Belum ada file yang dipilih", 
            font=("Segoe UI", 8, "italic"), 
            fg=self.c_text_muted, 
            bg=self.c_card,
            wraplength=280,
            justify="center"
        )
        self.lbl_filepath.pack(padx=20, pady=5)
        
        # Separator Line
        sep1 = tk.Frame(card_input, height=1, bg="#313244")
        sep1.pack(fill="x", padx=20, pady=10)
        
        # Info Metadata
        lbl_meta_title = tk.Label(
            card_input, 
            text="METADATA TERDETEKSI", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_text, 
            bg=self.c_card
        )
        lbl_meta_title.pack(anchor="w", padx=20, pady=5)
        
        self.lbl_rows = tk.Label(
            card_input, 
            text="Jumlah Baris Data : -", 
            font=("Segoe UI", 9), 
            fg=self.c_text_muted, 
            bg=self.c_card
        )
        self.lbl_rows.pack(anchor="w", padx=20, pady=2)
        
        self.lbl_cols = tk.Label(
            card_input, 
            text="Daftar Kolom       : -", 
            font=("Segoe UI", 9), 
            fg=self.c_text_muted, 
            bg=self.c_card,
            wraplength=280,
            justify="left"
        )
        self.lbl_cols.pack(anchor="w", padx=20, pady=2)
        
        # Separator Line 2
        sep2 = tk.Frame(card_input, height=1, bg="#313244")
        sep2.pack(fill="x", padx=20, pady=10)
        
        # Pencarian Teks Bebas (STKI Search)
        lbl_search_title = tk.Label(
            card_input, 
            text="PENCARIAN SEMANTIK (STKI)", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_success, 
            bg=self.c_card
        )
        lbl_search_title.pack(anchor="w", padx=20, pady=(0, 5))
        
        self.ent_search_query = tk.Entry(
            card_input, 
            font=("Segoe UI", 9), 
            bg="#313244", 
            fg=self.c_text, 
            bd=0, 
            insertbackground=self.c_text, 
            highlightthickness=1, 
            highlightbackground="#45475a"
        )
        self.ent_search_query.pack(fill="x", padx=20, ipady=6)
        self.ent_search_query.insert(0, "Ketik kueri pencarian...")
        self.ent_search_query.bind("<FocusIn>", lambda e: self.ent_search_query.delete(0, tk.END) if self.ent_search_query.get() == "Ketik kueri pencarian..." else None)
        self.ent_search_query.bind("<Return>", lambda e: self.run_text_search())
        
        btn_search = tk.Button(
            card_input, 
            text="CARI DOKUMEN DI DATABASE", 
            font=("Segoe UI", 9, "bold"),
            fg="#11111b",
            bg="#f9e2af",
            activebackground="#fae3b0",
            bd=0, 
            pady=6,
            cursor="hand2",
            command=self.run_text_search
        )
        btn_search.pack(fill="x", padx=20, pady=(5, 0))
        
        # Run Button
        self.btn_analyze = tk.Button(
            card_input, 
            text="JALANKAN ANALISIS SEMANTIK", 
            font=("Segoe UI", 10, "bold"),
            fg="#11111b",
            bg=self.c_success,
            activebackground="#a6e3a1",
            bd=0, 
            pady=12,
            cursor="hand2",
            state="disabled",
            command=self.run_semantic_analysis
        )
        self.btn_analyze.pack(fill="x", side="bottom", padx=20, pady=15)

        # =====================================================================
        # CARD 2: DATABASE UTILITY PANEL (Row 2, Column 0)
        # =====================================================================
        card_db_util = tk.Frame(bento_container, bg=self.c_card, bd=0, highlightthickness=1, highlightbackground="#313244")
        card_db_util.grid(row=2, column=0, rowspan=1, columnspan=1, padx=(0, 12), pady=(0, 0), sticky="nsew")
        
        lbl_db_title = tk.Label(
            card_db_util, 
            text="DATABASE OFFLINE (STKI)", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_accent_s, 
            bg=self.c_card
        )
        lbl_db_title.pack(anchor="w", padx=20, pady=(12, 8))
        
        # Interactive Switch
        db_switch_frame = tk.Frame(card_db_util, bg=self.c_card)
        db_switch_frame.pack(fill="x", padx=20, pady=4)
        
        lbl_switch_desc = tk.Label(
            db_switch_frame, 
            text="Database: ", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_text, 
            bg=self.c_card
        )
        lbl_switch_desc.pack(side="left")
        
        self.lbl_switch_status = tk.Label(
            db_switch_frame, 
            text="UTAMA (1k Default)", 
            font=("Segoe UI", 8, "bold"), 
            fg=self.c_accent_p, 
            bg=self.c_card
        )
        self.lbl_switch_status.pack(side="left", padx=(0, 10))
        
        def on_switch_toggle(is_active):
            if is_active:
                self.lbl_switch_status.configure(text="DEMO REAL (1k Asli)", fg=self.c_success)
                self.active_db_path = DB_REAL_PATH
                TAXONOMY["Layer_1_Domain"] = list(TAXONOMY_DEMO["Layer_1_Domain"])
                TAXONOMY["Layer_2_Detail"] = list(TAXONOMY_DEMO["Layer_2_Detail"])
                if not os.path.exists(DB_REAL_PATH):
                    messagebox.showwarning("Database Demo Belum Ada", "Membangkitkan Database Demo Real dari data SINTA/PDDikti...")
                    os.system(f'python "{os.path.join(CURRENT_DIR, "generate_real_demo.py")}"')
                messagebox.showinfo("Database Aktif", "Berhasil beralih ke: DATABASE DEMO REAL\n(1.000 Dokumen Asli PDDikti/SINTA aktif).")
            else:
                self.lbl_switch_status.configure(text="UTAMA (1k Default)", fg=self.c_accent_p)
                self.active_db_path = DB_PATH
                TAXONOMY["Layer_1_Domain"] = list(TAXONOMY_UTAMA["Layer_1_Domain"])
                TAXONOMY["Layer_2_Detail"] = list(TAXONOMY_UTAMA["Layer_2_Detail"])
                messagebox.showinfo("Database Aktif", "Berhasil beralih ke: DATABASE UTAMA\n(1.000 Dokumen Default terpasang).")
                
        self.switch_widget = PremiumSwitch(db_switch_frame, command=on_switch_toggle)
        self.switch_widget.pack(side="right")
        
        # Buttons
        btn_folder = tk.Button(
            card_db_util, 
            text="Buka Folder Berkas Sampel Kampus", 
            font=("Segoe UI", 8),
            fg=self.c_text,
            bg="#313244",
            activebackground="#45475a",
            bd=0, 
            pady=5,
            cursor="hand2",
            command=self.open_samples_folder
        )
        btn_folder.pack(fill="x", padx=20, pady=4)
        
        btn_manage_labels = tk.Button(
            card_db_util, 
            text="Kelola Taksonomi & Label DB", 
            font=("Segoe UI", 8, "bold"),
            fg="#11111b",
            bg="#f9e2af",
            activebackground="#fae3b0",
            bd=0, 
            pady=5,
            cursor="hand2",
            command=self.open_label_management
        )
        btn_manage_labels.pack(fill="x", padx=20, pady=4)

        btn_relabel = tk.Button(
            card_db_util, 
            text="Labeling Ulang Seluruh DB via Model", 
            font=("Segoe UI", 8, "bold"),
            fg="#11111b",
            bg=self.c_success,
            activebackground="#a6e3a1",
            bd=0, 
            pady=5,
            cursor="hand2",
            command=self.relabel_database
        )
        btn_relabel.pack(fill="x", padx=20, pady=4)
        
        btn_reset_db = tk.Button(
            card_db_util, 
            text="Reset & Regenerate Database Baru", 
            font=("Segoe UI", 8),
            fg=self.c_text,
            bg=self.c_accent_s,
            activebackground="#e09e85",
            bd=0, 
            pady=5,
            cursor="hand2",
            command=self.reset_and_seed_db
        )
        btn_reset_db.pack(fill="x", padx=20, pady=(4, 10))
        


        # =====================================================================
        # CARD 3: FINAL RECOMMENDATION (Row 0, Column 1 & 2)
        # =====================================================================
        card_final = tk.Frame(bento_container, bg="#181825", bd=0, highlightthickness=1, highlightbackground=self.c_success)
        card_final.grid(row=0, column=1, columnspan=2, padx=(0, 0), pady=(0, 12), sticky="nsew")
        
        lbl_final_title = tk.Label(
            card_final, 
            text="REKOMENDASI KATEGORI TERBAIK & DOKUMEN SERUPA DATABASE (HYBRID RETRIEVAL)", 
            font=("Segoe UI", 8, "bold"), 
            fg=self.c_text_muted, 
            bg="#181825"
        )
        lbl_final_title.pack(anchor="w", padx=20, pady=(12, 4))
        
        self.lbl_final_decision = tk.Label(
            card_final, 
            text="Silakan pilih berkas Excel dan tekan tombol 'JALANKAN ANALISIS SEMANTIK'...", 
            font=("Segoe UI", 10, "bold"), 
            fg=self.c_text, 
            bg="#181825",
            justify="left"
        )
        self.lbl_final_decision.pack(anchor="w", padx=20, pady=(2, 12))

        # =====================================================================
        # CARD 4: LAYER 1 - DOMAIN ANALYSIS (Row 1, Column 1)
        # =====================================================================
        card_l1 = tk.Frame(bento_container, bg=self.c_card, bd=0, highlightthickness=1, highlightbackground="#313244")
        card_l1.grid(row=1, column=1, rowspan=1, columnspan=1, padx=(0, 12), pady=(0, 12), sticky="nsew")
        
        lbl_l1_title = tk.Label(
            card_l1, 
            text="LAYER 1: DOMAIN / KONTEKS MAKRO", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_accent_p, 
            bg=self.c_card
        )
        lbl_l1_title.pack(anchor="w", padx=15, pady=(12, 4))
        
        l1_split_frame = tk.Frame(card_l1, bg=self.c_card)
        l1_split_frame.pack(fill="both", expand=True, padx=5)
        
        # Best Domain
        l1_left = tk.Frame(l1_split_frame, bg=self.c_card)
        l1_left.pack(side="left", fill="both", expand=True, padx=3)
        tk.Label(l1_left, text="Terbaik (Best)", font=("Segoe UI", 8, "bold"), fg=self.c_success, bg=self.c_card).pack(anchor="w")
        self.l1_canvas_best = tk.Canvas(l1_left, height=130, bg=self.c_card, highlightthickness=0)
        self.l1_canvas_best.pack(fill="both", expand=True)
        self.draw_empty_bars(self.l1_canvas_best, TAXONOMY["Layer_1_Domain"])
        
        # Worst Domain
        l1_right = tk.Frame(l1_split_frame, bg=self.c_card)
        l1_right.pack(side="right", fill="both", expand=True, padx=3)
        tk.Label(l1_right, text="Terendah (Worst)", font=("Segoe UI", 8, "bold"), fg=self.c_danger, bg=self.c_card).pack(anchor="w")
        self.l1_canvas_worst = tk.Canvas(l1_right, height=130, bg=self.c_card, highlightthickness=0)
        self.l1_canvas_worst.pack(fill="both", expand=True)
        self.draw_empty_bars(self.l1_canvas_worst, TAXONOMY["Layer_1_Domain"])

        # =====================================================================
        # CARD 5: LAYER 2 - DETAIL/FORMAT (Row 1, Column 2)
        # =====================================================================
        card_l2 = tk.Frame(bento_container, bg=self.c_card, bd=0, highlightthickness=1, highlightbackground="#313244")
        card_l2.grid(row=1, column=2, rowspan=1, columnspan=1, padx=(0, 0), pady=(0, 12), sticky="nsew")
        
        lbl_l2_title = tk.Label(
            card_l2, 
            text="LAYER 2: TIPE BERKAS / AKSI MIKRO", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_accent_p, 
            bg=self.c_card
        )
        lbl_l2_title.pack(anchor="w", padx=15, pady=(12, 4))
        
        l2_split_frame = tk.Frame(card_l2, bg=self.c_card)
        l2_split_frame.pack(fill="both", expand=True, padx=5)
        
        # Best Detail
        l2_left = tk.Frame(l2_split_frame, bg=self.c_card)
        l2_left.pack(side="left", fill="both", expand=True, padx=3)
        tk.Label(l2_left, text="Terbaik (Best - Top 3)", font=("Segoe UI", 8, "bold"), fg=self.c_success, bg=self.c_card).pack(anchor="w")
        self.l2_canvas_best = tk.Canvas(l2_left, height=130, bg=self.c_card, highlightthickness=0)
        self.l2_canvas_best.pack(fill="both", expand=True)
        self.draw_empty_bars(self.l2_canvas_best, TAXONOMY["Layer_2_Detail"][:3])
        
        # Worst Detail
        l2_right = tk.Frame(l2_split_frame, bg=self.c_card)
        l2_right.pack(side="right", fill="both", expand=True, padx=3)
        tk.Label(l2_right, text="Terendah (Worst)", font=("Segoe UI", 8, "bold"), fg=self.c_danger, bg=self.c_card).pack(anchor="w")
        self.l2_canvas_worst = tk.Canvas(l2_right, height=130, bg=self.c_card, highlightthickness=0)
        self.l2_canvas_worst.pack(fill="both", expand=True)
        self.draw_empty_bars(self.l2_canvas_worst, TAXONOMY["Layer_2_Detail"][3:])

        # =====================================================================
        # CARD 6: LAYER 3 - SIMILAR DOCUMENTS SCANNER (Row 2, Column 1 & 2)
        # =====================================================================
        card_l3 = tk.Frame(bento_container, bg=self.c_card, bd=0, highlightthickness=1, highlightbackground="#313244")
        card_l3.grid(row=2, column=1, rowspan=1, columnspan=2, padx=(0, 0), pady=(0, 0), sticky="nsew")
        
        lbl_l3_title = tk.Label(
            card_l3, 
            text="LAYER 3: DOKUMEN SERUPA DI DATABASE (STKI SCANNER)", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_accent_s, 
            bg=self.c_card
        )
        lbl_l3_title.pack(anchor="w", padx=20, pady=(12, 4))
        
        l3_split_frame = tk.Frame(card_l3, bg=self.c_card)
        l3_split_frame.pack(fill="both", expand=True, padx=5)
        
        # Best DB matches
        l3_left = tk.Frame(l3_split_frame, bg=self.c_card)
        l3_left.pack(side="left", fill="both", expand=True, padx=3)
        tk.Label(l3_left, text="Terbaik (Best Match)", font=("Segoe UI", 8, "bold"), fg=self.c_success, bg=self.c_card).pack(anchor="w")
        self.db_canvas_best = tk.Canvas(l3_left, height=130, bg=self.c_card, highlightthickness=0)
        self.db_canvas_best.pack(fill="both", expand=True)
        self.draw_empty_bars(self.db_canvas_best, ["Memuat...", "Memuat...", "Memuat..."])
        
        # Worst DB matches
        l3_right = tk.Frame(l3_split_frame, bg=self.c_card)
        l3_right.pack(side="right", fill="both", expand=True, padx=3)
        tk.Label(l3_right, text="Terendah (Worst Match)", font=("Segoe UI", 8, "bold"), fg=self.c_danger, bg=self.c_card).pack(anchor="w")
        self.db_canvas_worst = tk.Canvas(l3_right, height=130, bg=self.c_card, highlightthickness=0)
        self.db_canvas_worst.pack(fill="both", expand=True)
        self.draw_empty_bars(self.db_canvas_worst, ["Memuat...", "Memuat...", "Memuat..."])

    def draw_empty_bars(self, canvas, label_list):
        canvas.delete("all")
        n = len(label_list)
        if n == 0:
            return
        h = int(canvas.cget("height"))
        if n > 1:
            y_step = (h - 20) / (n - 1)
            y_offset = 10
        else:
            y_step = 0
            y_offset = h / 2
            
        for label in label_list:
            display_label = label if len(label) < 14 else label[:11] + "..."
            # Teks Label
            canvas.create_text(
                5, y_offset, 
                text=display_label, 
                anchor="w", 
                fill=self.c_text, 
                font=("Segoe UI", 8)
            )
            # Latar Belakang Progress Bar (VS Code grey)
            canvas.create_rectangle(
                110, y_offset - 5, 
                190, y_offset + 5, 
                fill="#3c3c3c", 
                outline=""
            )
            # Nilai Persen 0.00%
            canvas.create_text(
                195, y_offset, 
                text="0.00%", 
                anchor="w", 
                fill=self.c_text_muted, 
                font=("Segoe UI", 7)
            )
            y_offset += y_step

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            initialdir=CURRENT_DIR,
            title="Pilih Berkas Spreadsheet",
            filetypes=(("Excel Files", "*.xlsx *.xls"), ("CSV Files", "*.csv"), ("All Files", "*.*"))
        )
        if file_path:
            self.selected_file_path = file_path
            self.lbl_filepath.configure(text=os.path.basename(file_path), fg=self.c_accent_p)
            
            # Cek dan Parsing metadata berkas
            semantic_text, columns, rows = parse_excel_semantic(file_path)
            if semantic_text is not None:
                self.lbl_rows.configure(text=f"Jumlah Baris Data : {rows} Baris")
                self.lbl_cols.configure(text=f"Daftar Kolom       : {', '.join(columns)}")
                self.btn_analyze.configure(state="normal")
            else:
                messagebox.showerror("Error Parsing", "Berkas Excel tidak valid atau rusak.")
                self.btn_analyze.configure(state="disabled")

    def run_text_search(self):
        query = self.ent_search_query.get().strip()
        if not query or query == "Ketik kueri pencarian...":
            messagebox.showwarning("Kueri Kosong", "Masukkan kata kunci pencarian terlebih dahulu.")
            return
        try:
            conn = sqlite3.connect(self.active_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT filename, content, labels, embedding FROM documents")
            rows_db = cursor.fetchall()
            conn.close()
            if not rows_db:
                messagebox.showwarning("Database Kosong", "Tidak ada dokumen di database aktif.")
                return
            query_vector = get_onnx_embedding(query)
            corpus = [row[1] for row in rows_db]
            bm25 = BM25(corpus)
            query_words = query.lower().split()
            bm25_scores = [bm25.get_score(query_words, i) for i in range(len(corpus))]
            max_bm25 = max(bm25_scores) if bm25_scores else 0.0
            norm_bm25 = [s / max_bm25 if max_bm25 > 0 else 0.0 for s in bm25_scores]
            results = []
            for idx, (fname, content, labels, emb_str) in enumerate(rows_db):
                doc_vec = np.array(json.loads(emb_str))
                dense_sim = get_cosine_similarity(query_vector, doc_vec)
                sparse_score = norm_bm25[idx]
                # Hybrid Fusion dengan Penalty Absolut untuk dokumen OOD dan Temperatur 2.0
                if sparse_score <= 0.05:
                    hybrid_score = 0.0
                else:
                    hybrid_score = 0.70 * float(dense_sim)**2.0 + 0.30 * sparse_score
                final = max(0.0, min(1.0, hybrid_score)) * 100.0
                results.append((fname, json.loads(labels), final, content[:120]))
            results.sort(key=lambda x: x[2], reverse=True)
            # Tampilkan hasil di jendela baru
            res_win = tk.Toplevel(self.root)
            res_win.title(f"Hasil Pencarian: \"{query[:40]}\"")
            res_win.geometry("780x480")
            res_win.configure(bg=self.c_bg)
            res_win.transient(self.root)
            lbl_header = tk.Label(
                res_win,
                text=f"Hasil Pencarian Hybrid (Dense BERT 70% + BM25 30%)",
                font=("Segoe UI", 11, "bold"),
                fg=self.c_success, bg=self.c_bg
            )
            lbl_header.pack(anchor="w", padx=20, pady=(15, 3))
            lbl_query = tk.Label(
                res_win,
                text=f"Kueri: \"{query}\"  |  Ditemukan: {len(results)} Dokumen  |  Menampilkan Top-20",
                font=("Segoe UI", 9), fg=self.c_text_muted, bg=self.c_bg
            )
            lbl_query.pack(anchor="w", padx=20, pady=(0, 10))
            tree_frame = tk.Frame(res_win, bg=self.c_bg)
            tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))
            style = ttk.Style()
            style.theme_use("clam")
            style.configure("Search.Treeview", background="#1e1e2e", foreground="#d4d4d4",
                          fieldbackground="#1e1e2e", font=("Segoe UI", 9), rowheight=26)
            style.configure("Search.Treeview.Heading", background="#313244", foreground="#d4d4d4",
                          font=("Segoe UI", 9, "bold"))
            style.map("Search.Treeview", background=[("selected", "#007acc")])
            cols = ("rank", "filename", "labels", "score", "snippet")
            tree = ttk.Treeview(tree_frame, columns=cols, show="headings", style="Search.Treeview")
            tree.heading("rank", text="#")
            tree.heading("filename", text="Nama Berkas")
            tree.heading("labels", text="Label")
            tree.heading("score", text="Skor (%)")
            tree.heading("snippet", text="Cuplikan Isi")
            tree.column("rank", width=35, anchor="center")
            tree.column("filename", width=180)
            tree.column("labels", width=160)
            tree.column("score", width=70, anchor="center")
            tree.column("snippet", width=300)
            scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            tree.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            for i, (fname, labels, score, snippet) in enumerate(results[:20]):
                tree.insert("", "end", values=(
                    f"{i+1}",
                    fname,
                    " | ".join(labels) if labels else "-",
                    f"{score:.2f}",
                    snippet.replace("\n", " ")
                ))
            # Update panel utama juga
            top3_names = [r[0] for r in results[:3]]
            top3_scores = [r[2] for r in results[:3]]
            while len(top3_names) < 3:
                top3_names.append("- Tidak Ada -")
                top3_scores.append(0.0)
            self.update_progress_bars(self.db_canvas_best, top3_names, top3_scores, self.c_success)
            worst3 = sorted(results[3:20] if len(results) > 3 else results, key=lambda x: x[2])[:3]
            w_names = [r[0] for r in worst3]
            w_scores = [r[2] for r in worst3]
            while len(w_names) < 3:
                w_names.append("- Tidak Ada -")
                w_scores.append(0.0)
            self.update_progress_bars(self.db_canvas_worst, w_names, w_scores, self.c_danger)
            best = results[0] if results else None
            if best and best[2] > 30.0:
                self.lbl_final_decision.configure(
                    text=f"Pencarian: \"{query[:30]}\" => {best[0]} ({best[2]:.2f}%)",
                    fg=self.c_success
                )
        except Exception as e:
            messagebox.showerror("Error Pencarian", f"Gagal menjalankan pencarian: {e}")

    def open_samples_folder(self):
        try:
            os.startfile(CURRENT_DIR)
        except Exception as e:
            messagebox.showerror("Error", f"Gagal membuka folder: {e}")

    def switch_db(self):
        choice = self.db_var.get()
        if choice == "utama":
            self.active_db_path = DB_PATH
            messagebox.showinfo("Database Aktif", "Berhasil beralih ke: DATABASE UTAMA\n(1.000 Dokumen Default terpasang).")
        else:
            self.active_db_path = DB_REAL_PATH
            if not os.path.exists(DB_REAL_PATH):
                messagebox.showwarning("Database Demo Belum Ada", "Membangkitkan Database Demo Real dari data publik SINTA/PDDikti...")
                os.system(f'python "{os.path.join(CURRENT_DIR, "generate_real_demo.py")}"')
            messagebox.showinfo("Database Aktif", "Berhasil beralih ke: DATABASE DEMO REAL\n(1.000 Dokumen Asli PDDikti/SINTA aktif).")

    def reset_and_seed_db(self):
        try:
            if self.active_db_path == DB_REAL_PATH:
                import generate_real_demo
                generate_real_demo.generate_real_dataset()
                messagebox.showinfo("Sukses Reset", "Database DEMO REAL berhasil di-reset dengan 1.000 dokumen asli publik (SINTA/PDDikti)!")
                return
                
            conn = sqlite3.connect(self.active_db_path)
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
            
            # Generate 1000 dokumen akademik realistis secara programmatik lintas 4 ekstensi
            samples = []
            mhs_pool = [
                "Budi Santoso", "Kurnia Putri", "Ahmad Fauzi", "Rina Wijaya", 
                "Hendra Wijaya", "Siti Aminah", "Dewi Lestari", "Rian Hidayat", 
                "Fajar Pratama", "Novi Anggraini", "Bambang Pamungkas", "Eka Sari", 
                "Adi Saputra", "Taufik Hidayat", "Lestari Putri", "Joko Widodo",
                "Megawati Sukarno", "SBY Susilo", "Prabowo Subianto", "Gibran Rakabuming"
            ]
            
            dosen_names = [
                "Dr. Eng. Hermawan", "Prof. Dr. Sri Utami", "Diana Putri M.T.",
                "Rudi Hermawan Ph.D.", "Dr. Ahmad Fauzan", "Siti Rahma M.Cs.",
                "Hadi Wijaya M.T.", "Indra Lesmana Ph.D.", "Fitri Handayani M.T.",
                "Prof. Dr. Anwar Ibrahim"
            ]
            
            # 1. Transkrip Nilai (250 Dokumen)
            for i in range(250):
                name = mhs_pool[i % len(mhs_pool)]
                ext = [".pdf", ".docx", ".xlsx", ".csv"][i % 4]
                nim = f"101230{i+1:03d}"
                gpa = round(3.0 + (i % 100) * 0.01, 2)
                if ext in [".xlsx", ".csv"]:
                    content = f"TABEL DATA TRANSKRIP AKADEMIK. NIM: {nim} | Nama: {name}_{i} | Prodi: Informatika | IPK: {gpa} | Mata Kuliah: Aljabar Linier (A), Kalkulus 2 (B), Struktur Data (B+)."
                else:
                    content = f"Dokumen Transkrip Nilai Resmi Mahasiswa atas nama {name}_{i} dengan NIM {nim} Program Studi Informatika. Meraih IPK kumulatif sebesar {gpa} dengan predikat sangat memuaskan."
                
                samples.append({
                    "filename": f"transkrip_{name.lower().replace(' ', '_')}_{i}{ext}",
                    "content": content,
                    "labels": ["Akademik Mahasiswa", "Transkrip Nilai Lengkap"]
                })
                
            # 2. KRS SKS Kelas (250 Dokumen)
            for i in range(250):
                name = mhs_pool[i % len(mhs_pool)]
                ext = [".xlsx", ".csv", ".pdf", ".docx"][i % 4]
                courses = "Struktur Data, Matematika Diskrit, Pemrograman Web"
                sks = 18 + (i % 6)
                if ext in [".xlsx", ".csv"]:
                    content = f"REKAP RENCANA STUDI MAHASISWA (KRS). Nama: {name}_{i} | SKS Total: {sks} | Daftar Mata Kuliah Diambil: {courses} | Status: Disetujui Dosen Wali."
                else:
                    content = f"Formulir Rencana Studi Mahasiswa (KRS) untuk semester berjalan atas nama {name}_{i}. Mengambil total {sks} SKS yang terdiri dari beberapa mata kuliah utama: {courses}."
                    
                samples.append({
                    "filename": f"rencana_studi_{name.lower().replace(' ', '_')}_{i}{ext}",
                    "content": content,
                    "labels": ["Jadwal dan SKS Perkuliahan", "KRS SKS Kelas"]
                })
                
            # 3. Daftar Dosen Pengajar (250 Dokumen)
            for i in range(250):
                ext = [".pdf", ".xlsx", ".docx", ".csv"][i % 4]
                dos_name = dosen_names[i % len(dosen_names)]
                spec = ["Kecerdasan Buatan", "Kriptografi", "RPL", "Jaringan Komputer", "Basis Data"][i % 5]
                nip = f"198503122010121{i+1:03d}"
                if ext in [".xlsx", ".csv"]:
                    content = f"DATABASE DOSEN JURUSAN. NIP: {nip} | Nama Dosen: {dos_name}_{i} | Bidang Spesialisasi: {spec} | Status Kepegawaian: Aktif Mengajar."
                else:
                    content = f"Daftar NIP dan Nama Dosen Pengajar Fakultas Teknologi Informasi. Menugaskan {dos_name}_{i} dengan NIP {nip} selaku pengampu mata kuliah utama pada spesialisasi {spec}."
                    
                samples.append({
                    "filename": f"daftar_dosen_{dos_name.lower().replace('.', '').replace(' ', '_')}_{i}{ext}",
                    "content": content,
                    "labels": ["Administrasi Dosen", "Daftar Dosen Pengajar"]
                })
                
            # 4. Laporan Keuangan & Kurikulum (250 Dokumen)
            for i in range(250):
                ext = [".xlsx", ".csv", ".pdf", ".docx"][i % 4]
                if i % 2 == 0:
                    val = 5000000 + (i * 10000)
                    name = mhs_pool[i % len(mhs_pool)]
                    if ext in [".xlsx", ".csv"]:
                        content = f"REKAPITULASI PEMBAYARAN UKT. Mahasiswa: {name}_{i} | Nominal: Rp {val:,} | Status: Lunas Terverifikasi Bank Mandiri."
                    else:
                        content = f"Laporan Keuangan Pembayaran Uang Kuliah Tunggal (UKT) mahasiswa atas nama {name}_{i}. Tagihan sebesar Rp {val:,} dinyatakan lunas."
                        
                    samples.append({
                        "filename": f"keuangan_ukt_{name.lower().replace(' ', '_')}_{i}{ext}",
                        "content": content,
                        "labels": ["Akademik Mahasiswa", "Laporan Keuangan"]
                    })
                else:
                    dept = ["Informatika", "Sistem Informasi", "Teknik Komputer"][i % 3]
                    if ext in [".xlsx", ".csv"]:
                        content = f"STRUKTUR SILABUS DAN MATAKULIAH. Jurusan: {dept} | Kode: IF-30{i} | Capaian Pembelajaran: Lulusan kompeten bidang rekayasa teknologi."
                    else:
                        content = f"Silabus Dokumen Kurikulum Akademik S1 Jurusan {dept}. Mengatur standar kompetensi kelulusan mahasiswa, silabus pembelajaran teori, serta penulisan skripsi akhir."
                        
                    samples.append({
                        "filename": f"kurikulum_silabus_{dept.lower().replace(' ', '_')}_v{i}{ext}",
                        "content": content,
                        "labels": ["Jadwal dan SKS Perkuliahan", "Kurikulum Jurusan"]
                    })
            
            for s in samples:
                emb = get_onnx_embedding(s["content"]).tolist()
                cursor.execute("""
                    INSERT OR REPLACE INTO documents (filename, content, labels, embedding)
                    VALUES (?, ?, ?, ?)
                """, (s["filename"], s["content"], json.dumps(s["labels"]), json.dumps(emb)))
                
            conn.commit()
            conn.close()
            messagebox.showinfo("Sukses Reset", f"Database berhasil di-reset dengan {len(samples)} dokumen baru lintas 4 ekstensi!")
        except Exception as e:
            messagebox.showerror("Error Reset", f"Gagal mereset database: {e}")

    def open_label_management(self):
        # 1. Hitung total dokumen
        conn = sqlite3.connect(self.active_db_path)
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM documents")
        total_docs = c.fetchone()[0]
        conn.close()

        # 2. Hitung jumlah optimal label (Rice Rule)
        import math
        optimal_x = math.ceil(2 * (total_docs ** (1/3))) if total_docs > 0 else 0

        # 3. Buat Window Toplevel
        lbl_win = tk.Toplevel(self.root)
        lbl_win.title("Manajemen Taksonomi & Label DB (Rice Rule)")
        lbl_win.geometry("760x540")
        lbl_win.configure(bg=self.c_bg)
        lbl_win.resizable(False, False)
        lbl_win.transient(self.root)
        lbl_win.grab_set()

        # Premium Header
        header_frame = tk.Frame(lbl_win, bg="#1e1e2e", pady=10, highlightthickness=1, highlightbackground="#313244")
        header_frame.pack(fill="x")
        
        lbl_title = tk.Label(
            header_frame, 
            text="MANAJEMEN TAKSONOMI & LABEL SEMANTIK", 
            font=("Segoe UI", 12, "bold"), 
            fg=self.c_accent_s, 
            bg="#1e1e2e"
        )
        lbl_title.pack()

        # Rice Rule Info Panel
        info_text = f"Total Dokumen (N): {total_docs} Berkas  |  Rekomendasi Optimal Label (Rice Rule): X = 2 * N^(1/3) = {optimal_x} Label"
        lbl_formula = tk.Label(
            header_frame,
            text=info_text,
            font=("Segoe UI", 9, "italic"),
            fg=self.c_text_muted,
            bg="#1e1e2e",
            pady=4
        )
        lbl_formula.pack()

        # Main Workspace Split
        main_workspace = tk.Frame(lbl_win, bg=self.c_bg)
        main_workspace.pack(fill="both", expand=True, padx=20, pady=15)

        # Left Column: Listbox of Labels in DB
        left_col = tk.Frame(main_workspace, bg=self.c_bg)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        lbl_list_title = tk.Label(
            left_col, 
            text="Daftar Label Aktif di Database", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_text, 
            bg=self.c_bg
        )
        lbl_list_title.pack(anchor="w", pady=(0, 5))

        # Filter/Search Box
        search_frame = tk.Frame(left_col, bg=self.c_bg)
        search_frame.pack(fill="x", pady=(0, 5))
        
        lbl_search_icon = tk.Label(search_frame, text="🔍", fg=self.c_text_muted, bg=self.c_bg)
        lbl_search_icon.pack(side="left")
        
        ent_search = tk.Entry(
            search_frame, 
            font=("Segoe UI", 9), 
            bg="#313244", 
            fg=self.c_text, 
            bd=0, 
            insertbackground=self.c_text, 
            highlightthickness=1, 
            highlightbackground="#45475a"
        )
        ent_search.pack(side="left", fill="x", expand=True, padx=(5, 0), ipady=3)

        list_frame = tk.Frame(left_col, bg=self.c_bg)
        list_frame.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        lbl_listbox = tk.Listbox(
            list_frame, 
            yscrollcommand=scrollbar.set, 
            font=("Segoe UI", 9),
            bg="#1e1e2e", 
            fg=self.c_text, 
            selectbackground=self.c_success, 
            selectforeground="#11111b",
            bd=0, 
            highlightthickness=1, 
            highlightbackground="#313244"
        )
        lbl_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=lbl_listbox.yview)

        # Right Column: Controls and CRUD
        right_col = tk.Frame(main_workspace, bg=self.c_bg)
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        lbl_crud_title = tk.Label(
            right_col, 
            text="Panel Aksi Taksonomi", 
            font=("Segoe UI", 9, "bold"), 
            fg=self.c_text, 
            bg=self.c_bg
        )
        lbl_crud_title.pack(anchor="w", pady=(0, 5))

        # Card Panel for Inputs
        crud_card = tk.Frame(right_col, bg=self.c_card, padx=15, pady=15, highlightthickness=1, highlightbackground="#313244")
        crud_card.pack(fill="x", pady=5)

        # Input label name
        lbl_input_desc = tk.Label(
            crud_card, 
            text="Nama Label Terpilih / Baru:", 
            font=("Segoe UI", 8, "bold"), 
            fg=self.c_text_muted, 
            bg=self.c_card
        )
        lbl_input_desc.pack(anchor="w", pady=(0, 5))

        ent_label = tk.Entry(
            crud_card, 
            font=("Segoe UI", 10), 
            bg="#313244", 
            fg=self.c_text, 
            bd=0, 
            insertbackground=self.c_text, 
            highlightthickness=1, 
            highlightbackground="#45475a"
        )
        ent_label.pack(fill="x", ipady=5, pady=(0, 10))

        # CRUD Helper Functions
        def load_labels_into_listbox(filter_str=""):
            lbl_listbox.delete(0, tk.END)
            conn = sqlite3.connect(self.active_db_path)
            c = conn.cursor()
            c.execute("SELECT labels FROM documents")
            rows = c.fetchall()
            conn.close()
            
            unique_labels = set()
            for r in rows:
                if r[0]:
                    try:
                        lbls = json.loads(r[0])
                        for l in lbls:
                            unique_labels.add(l)
                    except:
                        pass
            
            # Sort alphabetically
            sorted_lbls = sorted(list(unique_labels))
            for l in sorted_lbls:
                if filter_str.lower() in l.lower():
                    lbl_listbox.insert(tk.END, l)

        def on_listbox_select(event):
            selection = lbl_listbox.curselection()
            if selection:
                selected_val = lbl_listbox.get(selection[0])
                ent_label.delete(0, tk.END)
                ent_label.insert(0, selected_val)

        lbl_listbox.bind("<<ListboxSelect>>", on_listbox_select)

        def search_labels(event=None):
            load_labels_into_listbox(ent_search.get())

        ent_search.bind("<KeyRelease>", search_labels)

        # 1. Edit / Update Label
        def update_label_action():
            selection = lbl_listbox.curselection()
            if not selection:
                messagebox.showwarning("Peringatan", "Pilih label dari daftar terlebih dahulu!")
                return
            old_name = lbl_listbox.get(selection[0])
            new_name = ent_label.get().strip()
            if not new_name:
                messagebox.showwarning("Peringatan", "Nama label baru tidak boleh kosong!")
                return
            if old_name == new_name:
                return

            try:
                conn = sqlite3.connect(self.active_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, labels FROM documents")
                rows = cursor.fetchall()
                
                updated_count = 0
                for doc_id, labels_str in rows:
                    if labels_str:
                        labels = json.loads(labels_str)
                        if old_name in labels:
                            # Replace old with new
                            new_labels = [new_name if l == old_name else l for l in labels]
                            cursor.execute("UPDATE documents SET labels = ? WHERE id = ?", (json.dumps(new_labels), doc_id))
                            updated_count += 1
                conn.commit()
                conn.close()
                
                # Update dynamic TAXONOMY global lists
                if old_name in TAXONOMY["Layer_1_Domain"]:
                    TAXONOMY["Layer_1_Domain"] = [new_name if x == old_name else x for x in TAXONOMY["Layer_1_Domain"]]
                if old_name in TAXONOMY["Layer_2_Detail"]:
                    TAXONOMY["Layer_2_Detail"] = [new_name if x == old_name else x for x in TAXONOMY["Layer_2_Detail"]]
                    
                messagebox.showinfo("Sukses Update", f"Berhasil memperbarui label '{old_name}' menjadi '{new_name}' di {updated_count} dokumen!")
                load_labels_into_listbox()
                ent_label.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal memperbarui label: {e}")

        # 2. Hapus Label
        def delete_label_action():
            selection = lbl_listbox.curselection()
            if not selection:
                messagebox.showwarning("Peringatan", "Pilih label dari daftar terlebih dahulu!")
                return
            lbl_to_delete = lbl_listbox.get(selection[0])
            
            confirm = messagebox.askyesno("Konfirmasi Hapus", f"Apakah Anda yakin ingin menghapus label '{lbl_to_delete}' dari semua dokumen?")
            if not confirm:
                return

            try:
                conn = sqlite3.connect(self.active_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT id, labels FROM documents")
                rows = cursor.fetchall()
                
                updated_count = 0
                for doc_id, labels_str in rows:
                    if labels_str:
                        labels = json.loads(labels_str)
                        if lbl_to_delete in labels:
                            # Filter out deleted label
                            new_labels = [l for l in labels if l != lbl_to_delete]
                            cursor.execute("UPDATE documents SET labels = ? WHERE id = ?", (json.dumps(new_labels), doc_id))
                            updated_count += 1
                conn.commit()
                conn.close()
                
                # Update global dynamic lists
                if lbl_to_delete in TAXONOMY["Layer_1_Domain"]:
                    TAXONOMY["Layer_1_Domain"].remove(lbl_to_delete)
                if lbl_to_delete in TAXONOMY["Layer_2_Detail"]:
                    TAXONOMY["Layer_2_Detail"].remove(lbl_to_delete)

                messagebox.showinfo("Sukses Hapus", f"Berhasil menghapus label '{lbl_to_delete}' dari {updated_count} dokumen!")
                load_labels_into_listbox()
                ent_label.delete(0, tk.END)
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menghapus label: {e}")

        # 3. Tambah Label Baru ke Taksonomi
        def add_label_action():
            new_lbl = ent_label.get().strip()
            if not new_lbl:
                messagebox.showwarning("Peringatan", "Nama label baru tidak boleh kosong!")
                return
            
            # Tentukan apakah masuk ke Layer 1 atau Layer 2
            confirm_l1 = messagebox.askyesno("Level Label", f"Apakah '{new_lbl}' merupakan label Domain Makro (Layer 1)?\nKlik No jika merupakan Detail Mikro (Layer 2).")
            
            if confirm_l1:
                if new_lbl not in TAXONOMY["Layer_1_Domain"]:
                    TAXONOMY["Layer_1_Domain"].append(new_lbl)
                else:
                    messagebox.showwarning("Peringatan", f"Label '{new_lbl}' sudah ada di Layer 1.")
                    return
            else:
                if new_lbl not in TAXONOMY["Layer_2_Detail"]:
                    TAXONOMY["Layer_2_Detail"].append(new_lbl)
                else:
                    messagebox.showwarning("Peringatan", f"Label '{new_lbl}' sudah ada di Layer 2.")
                    return
                    
            messagebox.showinfo("Sukses Tambah", f"Berhasil menambahkan '{new_lbl}' ke taksonomi aktif!\nJalankan regenerasi label di bawah agar model menggunakannya.")
            ent_label.delete(0, tk.END)

        # 4. Hapus dan Regenerasi Ulang via ONNX BERT (Batch classification)
        def batch_regenerate_action():
            confirm = messagebox.askyesno(
                "Konfirmasi Regenerasi", 
                "Apakah Anda yakin ingin menghapus seluruh label yang ada saat ini di database, "
                "dan melabeli ulang secara otomatis menggunakan model ONNX BERT berdasarkan taksonomi aktif?"
            )
            if not confirm:
                return
            
            lbl_win.destroy()  # Tutup jendela manajemen ini
            self.relabel_database()  # Jalankan regenerasi utama dengan progress bar!

        # Layout Buttons on the right column
        btn_update = tk.Button(
            crud_card, 
            text="Simpan Perubahan (Edit Label)", 
            font=("Segoe UI", 9, "bold"),
            fg="#11111b",
            bg="#f9e2af",
            activebackground="#fae3b0",
            bd=0, 
            pady=6,
            cursor="hand2",
            command=update_label_action
        )
        btn_update.pack(fill="x", pady=4)

        btn_delete = tk.Button(
            crud_card, 
            text="Hapus Label dari DB", 
            font=("Segoe UI", 9, "bold"),
            fg=self.c_text,
            bg=self.c_accent_s,
            activebackground="#e09e85",
            bd=0, 
            pady=6,
            cursor="hand2",
            command=delete_label_action
        )
        btn_delete.pack(fill="x", pady=4)

        btn_add = tk.Button(
            crud_card, 
            text="Tambah Label ke Taksonomi", 
            font=("Segoe UI", 9, "bold"),
            fg="#11111b",
            bg=self.c_accent_p,
            activebackground="#89b4fa",
            bd=0, 
            pady=6,
            cursor="hand2",
            command=add_label_action
        )
        btn_add.pack(fill="x", pady=4)

        # Large Neon Green Button at the bottom for Hapus & Regenerasi Ulang
        lbl_regen_desc = tk.Label(
            right_col, 
            text="TINDAKAN BATCH RADIKAL", 
            font=("Segoe UI", 8, "bold"), 
            fg=self.c_text_muted, 
            bg=self.c_bg
        )
        lbl_regen_desc.pack(anchor="w", pady=(15, 2))

        btn_batch_regen = tk.Button(
            right_col, 
            text="Hapus & Regenerasi Label via ONNX", 
            font=("Segoe UI", 10, "bold"),
            fg="#11111b",
            bg=self.c_success,
            activebackground="#a6e3a1",
            bd=0, 
            pady=12,
            cursor="hand2",
            command=batch_regenerate_action
        )
        btn_batch_regen.pack(fill="x", pady=4)

        # Initial loading
        load_labels_into_listbox()

    def relabel_database(self):
        try:
            conn = sqlite3.connect(self.active_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, content FROM documents")
            rows = cursor.fetchall()
            
            if not rows:
                messagebox.showwarning("Database Kosong", "Tidak ada dokumen untuk dilabeli ulang.")
                conn.close()
                return
                
            progress_win = tk.Toplevel(self.root)
            progress_win.title("Progres Labeling Ulang")
            progress_win.geometry("350x120")
            progress_win.configure(bg=self.c_bg)
            progress_win.resizable(False, False)
            progress_win.transient(self.root)
            progress_win.grab_set()
            
            lbl_progress = tk.Label(
                progress_win,
                text="Memulai labeling ulang...",
                font=("Segoe UI", 9),
                fg=self.c_text,
                bg=self.c_bg,
                pady=15
            )
            lbl_progress.pack()
            
            progress_bar = tk.Frame(progress_win, height=6, bg=self.c_success, width=0)
            progress_bar.pack(anchor="w", padx=25, pady=5)
            
            total = len(rows)
            for idx, (doc_id, content) in enumerate(rows):
                emb = get_onnx_embedding(content)
                text_lower = content.lower()
                
                # 1. Layer 2 Detail prediction
                l2_raw_sims = []
                for label in TAXONOMY["Layer_2_Detail"]:
                    lbl_vector = get_onnx_embedding(label)
                    sim = get_cosine_similarity(emb, lbl_vector)
                    l2_raw_sims.append(sim)
                    
                l2_boosts = [0.0] * len(TAXONOMY["Layer_2_Detail"])
                for i, label in enumerate(TAXONOMY["Layer_2_Detail"]):
                    lbl_lower = label.lower()
                    if "transkrip" in lbl_lower or "nilai" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["transkrip", "ipk", "kps", "khs", "grade", "lulus", "yudisium"]):
                            l2_boosts[i] += 0.20
                    elif "krs" in lbl_lower or "rencana studi" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["krs", "sks", "rencana studi", "matakuliah", "mata kuliah", "semester"]):
                            l2_boosts[i] += 0.20
                    elif "dosen" in lbl_lower or "pengajar" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["nip", "dosen", "pengajar", "nidn", "lektor", "profesor"]):
                            l2_boosts[i] += 0.20
                    elif "keuangan" in lbl_lower or "ukt" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["keuangan", "pembayaran", "spp", "ukt", "slip", "va", "nominal", "lunas", "tagihan", "bayar", "biaya", "jumlah", "transaksi", "kuitansi", "transfer"]):
                            l2_boosts[i] += 0.20
                    elif "kurikulum" in lbl_lower or "silabus" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["kurikulum", "silabus", "capaian", "prodi", "rps", "kkni"]):
                            l2_boosts[i] += 0.20
                    elif "skripsi" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["skripsi", "tugas akhir", "sarjana", "penelitian", "abstrak", "kesimpulan"]):
                            l2_boosts[i] += 0.20
                    elif "dataset" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["dataset", "sensor", "citra", "teks", "data", "sekunder", "primer"]):
                            l2_boosts[i] += 0.20
                    elif "paten" in lbl_lower or "haki" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["paten", "haki", "invensi", "software", "cipta", "hak cipta", "merek"]):
                            l2_boosts[i] += 0.20
                    elif "jurnal" in lbl_lower or "sinta" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["jurnal", "sinta", "akreditasi", "volume", "issn"]):
                            l2_boosts[i] += 0.20
                    elif "konferensi" in lbl_lower or "ieee" in lbl_lower or "prosiding" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["artikel", "ieee", "prosiding", "konferensi", "scopus", "proceeding"]):
                            l2_boosts[i] += 0.20
                
                for i in range(len(l2_raw_sims)):
                    if l2_boosts[i] > 0.0:
                        l2_raw_sims[i] += l2_boosts[i]
                    else:
                        if l2_raw_sims[i] < 0.92:
                            l2_raw_sims[i] = 0.0
                
                best_l2_label = "Tidak Terklasifikasi"
                if max(l2_raw_sims) > 0.0:
                    best_l2_idx = np.argmax(l2_raw_sims)
                    best_l2_label = TAXONOMY["Layer_2_Detail"][best_l2_idx]

                # 2. Layer 1 Domain prediction
                l1_raw_sims = []
                for label in TAXONOMY["Layer_1_Domain"]:
                    lbl_vector = get_onnx_embedding(label)
                    sim = get_cosine_similarity(emb, lbl_vector)
                    l1_raw_sims.append(sim)
                
                l1_boosts = [0.0] * len(TAXONOMY["Layer_1_Domain"])
                for i, label in enumerate(TAXONOMY["Layer_1_Domain"]):
                    lbl_lower = label.lower()
                    if "akademik" in lbl_lower or "mahasiswa" in lbl_lower or "skripsi" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["nim", "nilai", "transkrip", "ipk", "mahasiswa", "skripsi", "ta"]):
                            l1_boosts[i] += 0.15
                    if "dosen" in lbl_lower or "dataset" in lbl_lower or "riset" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["nip", "dosen", "pengajar", "nidn", "sinta", "dataset", "paten", "haki"]):
                            l1_boosts[i] += 0.15
                    if "sks" in lbl_lower or "jadwal" in lbl_lower or "jurnal" in lbl_lower or "artikel" in lbl_lower:
                        if any(has_keyword(text_lower, w) for w in ["krs", "sks", "jadwal", "perkuliahan", "kurikulum", "jurnal", "artikel"]):
                            l1_boosts[i] += 0.15
                
                # Apply Hierarchical Taxonomy Consistency boost to Layer 1
                if best_l2_label in CHILD_TO_PARENT_MAP:
                    parent_domain = CHILD_TO_PARENT_MAP[best_l2_label]
                    for i, label in enumerate(TAXONOMY["Layer_1_Domain"]):
                        if label == parent_domain:
                            l1_boosts[i] += 0.30

                for i in range(len(l1_raw_sims)):
                    if l1_boosts[i] > 0.0:
                        l1_raw_sims[i] += l1_boosts[i]
                    else:
                        if l1_raw_sims[i] < 0.92:
                            l1_raw_sims[i] = 0.0
                
                best_l1_label = "Tidak Terklasifikasi"
                if max(l1_raw_sims) > 0.0:
                    best_l1_idx = np.argmax(l1_raw_sims)
                    best_l1_label = TAXONOMY["Layer_1_Domain"][best_l1_idx]
                
                predicted_labels = [best_l1_label, best_l2_label]
                cursor.execute("UPDATE documents SET labels = ? WHERE id = ?", (json.dumps(predicted_labels), doc_id))
                
                if (idx + 1) % 10 == 0 or (idx + 1) == total:
                    pct = int(((idx + 1) / total) * 100)
                    lbl_progress.configure(text=f"Melabeli: {idx + 1}/{total} Dokumen ({pct}%)")
                    progress_bar.configure(width=int(pct * 3.0))
                    progress_win.update()
            
            conn.commit()
            conn.close()
            progress_win.destroy()
            messagebox.showinfo("Sukses Relabeling", f"Berhasil melabeli ulang {total} dokumen di database aktif menggunakan model ONNX!")
        except Exception as e:
            messagebox.showerror("Error Relabeling", f"Gagal melakukan labeling ulang: {e}")

    def run_semantic_analysis(self):
        if not self.selected_file_path:
            return
            
        semantic_text, columns, rows = parse_excel_semantic(self.selected_file_path)
        if semantic_text is None:
            return
            
        # Hitung Vector Embedding Dokumen via ONNX
        doc_vector = get_onnx_embedding(semantic_text)
        text_lower = semantic_text.lower()
              # Booster khusus Layer 2
        l2_boosts = [0.0] * len(TAXONOMY["Layer_2_Detail"])
        for i, label in enumerate(TAXONOMY["Layer_2_Detail"]):
            lbl_lower = label.lower()
            if "transkrip" in lbl_lower or "nilai" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["transkrip", "ipk", "kps", "khs", "grade", "lulus", "yudisium"]):
                    l2_boosts[i] += 0.20
            elif "krs" in lbl_lower or "rencana studi" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["krs", "sks", "rencana studi", "matakuliah", "mata kuliah", "semester"]):
                    l2_boosts[i] += 0.20
            elif "dosen" in lbl_lower or "pengajar" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["nip", "dosen", "pengajar", "nidn", "lektor", "profesor"]):
                    l2_boosts[i] += 0.20
            elif "keuangan" in lbl_lower or "ukt" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["keuangan", "pembayaran", "spp", "ukt", "slip", "va", "nominal", "lunas", "tagihan", "bayar", "biaya", "jumlah", "transaksi", "kuitansi", "transfer"]):
                    l2_boosts[i] += 0.20
            elif "kurikulum" in lbl_lower or "silabus" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["kurikulum", "silabus", "capaian", "prodi", "rps", "kkni"]):
                    l2_boosts[i] += 0.20
            elif "skripsi" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["skripsi", "tugas akhir", "sarjana", "penelitian", "abstrak", "kesimpulan"]):
                    l2_boosts[i] += 0.20
            elif "dataset" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["dataset", "sensor", "citra", "teks", "data", "sekunder", "primer"]):
                    l2_boosts[i] += 0.20
            elif "paten" in lbl_lower or "haki" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["paten", "haki", "invensi", "software", "cipta", "hak cipta", "merek"]):
                    l2_boosts[i] += 0.20
            elif "jurnal" in lbl_lower or "sinta" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["jurnal", "sinta", "akreditasi", "volume", "issn"]):
                    l2_boosts[i] += 0.20
            elif "konferensi" in lbl_lower or "ieee" in lbl_lower or "prosiding" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["artikel", "ieee", "prosiding", "konferensi", "scopus", "proceeding"]):
                    l2_boosts[i] += 0.20
        
        # 1. EVALUASI LAYER 2 (Raw Cosine Similarity Percentage)
        l2_raw_sims = []
        for label in TAXONOMY["Layer_2_Detail"]:
            lbl_vector = get_onnx_embedding(label)
            sim = get_cosine_similarity(doc_vector, lbl_vector)
            l2_raw_sims.append(sim)
            
        for idx in range(len(l2_raw_sims)):
            if l2_boosts[idx] > 0.0:
                l2_raw_sims[idx] += l2_boosts[idx]
            else:
                if l2_raw_sims[idx] < 0.92:
                    l2_raw_sims[idx] = 0.0
            
        # Konversi langsung ke Persentase Raw Cosine Similarity [0, 100%]
        l2_scores = [max(0.0, min(1.0, sim)) * 100.0 for sim in l2_raw_sims]
            
        # Sort Layer 2 descending
        l2_sorted = sorted(zip(TAXONOMY["Layer_2_Detail"], l2_scores), key=lambda x: x[1], reverse=True)
        # Best Layer 2 (Top 3)
        self.update_progress_bars(self.l2_canvas_best, [x[0] for x in l2_sorted[:3]], [x[1] for x in l2_sorted[:3]], self.c_success)
        # Worst Layer 2 (Bottom 2, sorted ascending)
        l2_sorted_worst = sorted(l2_sorted[3:], key=lambda x: x[1])
        self.update_progress_bars(self.l2_canvas_worst, [x[0] for x in l2_sorted_worst], [x[1] for x in l2_sorted_worst], self.c_danger)
        
        # Pilih Detail/Tipe Tertinggi
        best_l2_idx = np.argmax(l2_scores)
        best_l2_label = TAXONOMY["Layer_2_Detail"][best_l2_idx]
        best_l2_score = l2_scores[best_l2_idx]
        assigned_l2 = best_l2_label if l2_raw_sims[best_l2_idx] > 0.35 else "Tidak Terklasifikasi"
        
        # Penyelarasan Semantik Hibrida (Dense + Sparse/Lexical) dengan Parameter Lembut (Gentle Guidance)
        l1_boosts = [0.0] * len(TAXONOMY["Layer_1_Domain"])
        for i, label in enumerate(TAXONOMY["Layer_1_Domain"]):
            lbl_lower = label.lower()
            if "akademik" in lbl_lower or "mahasiswa" in lbl_lower or "skripsi" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["nim", "nilai", "transkrip", "ipk", "mahasiswa", "skripsi", "ta"]):
                    l1_boosts[i] += 0.15
            if "dosen" in lbl_lower or "dataset" in lbl_lower or "riset" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["nip", "dosen", "pengajar", "nidn", "sinta", "dataset", "paten", "haki"]):
                    l1_boosts[i] += 0.15
            if "sks" in lbl_lower or "jadwal" in lbl_lower or "jurnal" in lbl_lower or "artikel" in lbl_lower:
                if any(has_keyword(text_lower, w) for w in ["krs", "sks", "jadwal", "perkuliahan", "kurikulum", "jurnal", "artikel"]):
                    l1_boosts[i] += 0.15
                    
        # Apply Hierarchical Taxonomy Consistency boost to Layer 1
        if assigned_l2 in CHILD_TO_PARENT_MAP:
            parent_domain = CHILD_TO_PARENT_MAP[assigned_l2]
            for i, label in enumerate(TAXONOMY["Layer_1_Domain"]):
                if label == parent_domain:
                    l1_boosts[i] += 0.30
 
        # 2. EVALUASI LAYER 1 (Raw Cosine Similarity Percentage)
        l1_raw_sims = []
        for label in TAXONOMY["Layer_1_Domain"]:
            lbl_vector = get_onnx_embedding(label)
            sim = get_cosine_similarity(doc_vector, lbl_vector)
            l1_raw_sims.append(sim)
            
        for idx in range(len(l1_raw_sims)):
            if l1_boosts[idx] > 0.0:
                l1_raw_sims[idx] += l1_boosts[idx]
            else:
                if l1_raw_sims[idx] < 0.92:
                    l1_raw_sims[idx] = 0.0
            
        # Konversi langsung ke Persentase Raw Cosine Similarity [0, 100%]
        l1_scores = [max(0.0, min(1.0, sim)) * 100.0 for sim in l1_raw_sims]
            
        # Sort Layer 1 descending
        l1_sorted = sorted(zip(TAXONOMY["Layer_1_Domain"], l1_scores), key=lambda x: x[1], reverse=True)
        self.update_progress_bars(self.l1_canvas_best, [x[0] for x in l1_sorted], [x[1] for x in l1_sorted], self.c_success)
        # Worst Layer 1 (sorted ascending)
        l1_sorted_worst = sorted(l1_sorted, key=lambda x: x[1])
        self.update_progress_bars(self.l1_canvas_worst, [x[0] for x in l1_sorted_worst], [x[1] for x in l1_sorted_worst], self.c_danger)
        
        # Pilih Domain Tertinggi
        best_l1_idx = np.argmax(l1_scores)
        best_l1_label = TAXONOMY["Layer_1_Domain"][best_l1_idx]
        best_l1_score = l1_scores[best_l1_idx]
        assigned_l1 = best_l1_label if l1_raw_sims[best_l1_idx] > 0.30 else "Tidak Terklasifikasi"
        
        # 3. EVALUASI LAYER 3 (PENCARIAN DOKUMEN SERUPA DI DATABASE DENGAN HYBRID RETRIEVAL: DENSE + SPARSE BM25)
        db_docs = []
        try:
            conn = sqlite3.connect(self.active_db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT filename, labels, content, embedding FROM documents")
            rows_db = cursor.fetchall()
            conn.close()
            
            # Ekstrak korpus konten dokumen untuk inisialisasi BM25
            corpus = [row[2] for row in rows_db]
            filenames = [row[0] for row in rows_db]
            labels_list = [json.loads(row[1]) for row in rows_db]
            embeddings = [np.array(json.loads(row[3])) for row in rows_db]
            
            # Inisialisasi BM25 Engine
            bm25 = BM25(corpus)
            query_words = semantic_text.lower().split()
            
            # Hitung skor BM25 mentah untuk seluruh dokumen di corpus
            bm25_scores = []
            for idx in range(len(corpus)):
                bm25_scores.append(bm25.get_score(query_words, idx))
                
            # Normalisasi skor BM25 agar berskala [0.0, 1.0]
            max_bm25 = max(bm25_scores) if len(bm25_scores) > 0 else 0.0
            norm_bm25_scores = [score / max_bm25 if max_bm25 > 0.0 else 0.0 for score in bm25_scores]
            
            for idx in range(len(rows_db)):
                fname = filenames[idx]
                lbls = labels_list[idx]
                emb = embeddings[idx]
                
                # A. Dense Semantic Similarity via BERT Cosine (skala [0, 1])
                dense_sim = get_cosine_similarity(doc_vector, emb)
                
                # B. Sparse Lexical Score via BM25 (skala [0, 1])
                sparse_score = norm_bm25_scores[idx]
                
                # C. Hybrid Rank Fusion (Linear Combination): 70% Dense + 30% Sparse dengan Penalty OOD
                alpha = 0.70
                if sparse_score <= 0.05:
                    hybrid_score = 0.0
                else:
                    hybrid_score = alpha * dense_sim + (1.0 - alpha) * sparse_score
                
                # Batasi kesamaan geometris yang valid
                final_sim = max(0.0, min(1.0, hybrid_score))
                
                db_docs.append({
                    "filename": fname,
                    "labels": lbls,
                    "similarity": final_sim * 100.0
                })
        except Exception as e:
            print(f"Error reading database: {e}")
            
        # Urutkan berdasarkan similarity tertinggi (descending)
        db_sorted = sorted(db_docs, key=lambda x: x["similarity"], reverse=True)
        
        # Best Layer 3 (Top 3)
        top_db_names = [x["filename"] for x in db_sorted[:3]]
        top_db_scores = [x["similarity"] for x in db_sorted[:3]]
        while len(top_db_names) < 3:
            top_db_names.append("- Belum Ada Data -")
            top_db_scores.append(0.0)
        self.update_progress_bars(self.db_canvas_best, top_db_names, top_db_scores, self.c_success)
        
        # Worst Layer 3 (Bottom 3, sorted ascending)
        worst_db_docs = sorted(db_sorted[3:] if len(db_sorted) > 3 else db_sorted, key=lambda x: x["similarity"])
        worst_db_names = [x["filename"] for x in worst_db_docs[:3]]
        worst_db_scores = [x["similarity"] for x in worst_db_docs[:3]]
        while len(worst_db_names) < 3:
            worst_db_names.append("- Belum Ada Data -")
            worst_db_scores.append(0.0)
        self.update_progress_bars(self.db_canvas_worst, worst_db_names, worst_db_scores, self.c_danger)
        
        # Ambil dokumen database terdekat untuk memperkuat rekomendasi
        best_db_doc = db_docs[0] if len(db_docs) > 0 else None
        
        if best_db_doc and best_db_doc["similarity"] > 50.0:
            db_ref_text = f"Dokumen Serupa Terdeteksi di DB: {best_db_doc['filename']} ({best_db_doc['similarity']:05.2f}%)"
            decision_text = f"{assigned_l1} ({best_l1_score:05.2f}%)  ==>  {assigned_l2} ({best_l2_score:05.2f}%)\n{db_ref_text}"
        else:
            decision_text = f"{assigned_l1} ({best_l1_score:05.2f}%)  ==>  {assigned_l2} ({best_l2_score:05.2f}%)\nTidak ditemukan berkas serupa di database"
            
        # Update Teks Keputusan Akhir lengkap dengan persentase kemantapan/confidence
        self.lbl_final_decision.configure(text=decision_text, fg=self.c_success)
        
        messagebox.showinfo("Analisis Sukses", f"Berkas berhasil dianalisis terhadap database!")

    def update_progress_bars(self, canvas, label_list, scores, color):
        canvas.delete("all")
        n = len(label_list)
        if n == 0:
            return
        h = int(canvas.cget("height"))
        if n > 1:
            y_step = (h - 20) / (n - 1)
            y_offset = 10
        else:
            y_step = 0
            y_offset = h / 2
            
        for label, score in zip(label_list, scores):
            display_label = label if len(label) < 14 else label[:11] + "..."
            canvas.create_text(
                5, y_offset, 
                text=display_label, 
                anchor="w", 
                fill=self.c_text, 
                font=("Segoe UI", 8)
            )
            canvas.create_rectangle(
                110, y_offset - 5, 
                190, y_offset + 5, 
                fill="#3c3c3c", 
                outline=""
            )
            
            # Hitung Lebar Batang Aktif Berdasarkan Persentase (Maksimal 80 Pixel)
            bar_width = int((score / 100.0) * 80.0)
            if bar_width > 0:
                canvas.create_rectangle(
                    110, y_offset - 5, 
                    110 + bar_width, y_offset + 5, 
                    fill=color, 
                    outline=""
                )
                
            # Menuliskan Nilai Persen (Format 2 Angka Desimal)
            canvas.create_text(
                195, y_offset, 
                text=f"{score:05.2f}%", 
                anchor="w", 
                fill=self.c_text if score > 50 else self.c_text_muted, 
                font=("Segoe UI", 7, "bold" if score > 70 else "normal")
            )
            y_offset += y_step

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernApp(root)
    root.mainloop()
