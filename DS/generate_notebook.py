import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []

# =====================================================================
# 1. JUDUL & PENDAHULUAN
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
# Pelabelan Dokumen Otomatis (Multi-Label Classification) Skala Besar & Sistem Temu Kembali Informasi (STKI)
**Tahapan Eksperimen: TKT 3 (Data Science) & Persiapan TKT 4 (STKI/Offline)**

Notebook ini merupakan prototipe lengkap dan fungsional untuk mengelola dokumen civitas akademika menggunakan arsitektur Transformer kompak. Sistem ini mengintegrasikan 4 modul utama:
1. **Resilient Data Processing & Extraction:** Parsing dokumen format **CSV, DOCX, XLSX, dan PDF**.
2. **Hybrid & Dynamic Classifier:** Penggabungan klasifikasi multi-label terpadu dengan sistem *Zero-Shot Semantic Mapping* secara *real-time*.
3. **Penyimpanan Metadata Terpadu (SQLite):** Database lokal untuk menampung berkas, tag, serta representasi vektor dokumen.
4. **Pencarian Semantik (STKI):** Pencarian dokumen berbasis *Cosine Similarity* menggunakan *semantic embeddings*.
5. **Smart Data Transformer:** Mengubah berkas data mentah akademis menjadi laporan analisis siap pakai.
"""))

# =====================================================================
# 2. INSTALASI & DOWNLOAD DATA DENGAN RATE-LIMIT MITIGATION
# =====================================================================
cells.append(nbf.v4.new_code_cell("""\
# Instalasi library modern NLP, Deep Learning, & Document Parser di Google Colab
!pip install -q transformers datasets onnxruntime evaluate
!pip install -q torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
!pip install -q pandas requests tqdm xmltodict scikit-learn openpyxl python-docx pypdf onnx onnxscript

import urllib.request
import urllib.error
import xmltodict
import pandas as pd
from tqdm import tqdm
import time

def fetch_arxiv_with_retry(url, retries=5, backoff_factor=3):
    # Menggunakan User-Agent browser modern untuk menghindari pemblokiran/rate-limit default Python urllib
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    )
    for i in range(retries):
        try:
            with urllib.request.urlopen(req) as response:
                return response.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait_time = backoff_factor * (2 ** i)
                print(f"HTTP 429 (Too Many Requests). Menunggu {wait_time} detik sebelum mencoba kembali...")
                time.sleep(wait_time)
            else:
                raise e
    raise Exception("Gagal menarik data dari ArXiv API setelah beberapa kali percobaan karena batas rate limit.")

print("Mendownload sampel data dari ArXiv API dengan mekanisme pertahanan 429...")
# Kita tarik data dari berbagai domain akademik (AI, CL, statistika, ekonomi)
url = 'https://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.CL+OR+cat:stat.AP+OR+cat:q-fin.EC&start=0&max_results=1000&sortBy=submittedDate&sortOrder=descending'

try:
    data = fetch_arxiv_with_retry(url)
    parsed_data = xmltodict.parse(data)
    
    papers = []
    entries = parsed_data['feed'].get('entry', [])
    if isinstance(entries, dict):
        entries = [entries]
        
    for entry in tqdm(entries, desc="Parsing XML"):
        categories = entry.get('category', [])
        if isinstance(categories, dict):
            categories = [categories]
        
        tags = [cat['@term'] for cat in categories if '@term' in cat]
        abstract = entry.get('summary', '').replace('\\n', ' ').strip()
        
        papers.append({
            'teks_dokumen': abstract,
            'daftar_label': tags
        })

    df = pd.DataFrame(papers)
    print(f"\\nBerhasil mendownload {len(df)} dokumen.")
    display(df.head())
except Exception as e:
    print(f"Terjadi kesalahan saat download data: {e}")
    print("Menggunakan fallback data akademis sintetis multidisiplin untuk menjamin notebook tetap fungsional...")
    # Fallback jika server ArXiv sedang benar-benar down/maintenance
    df = pd.DataFrame([
        {"teks_dokumen": "Artificial intelligence and deep learning models are transforming computer vision tasks.", "daftar_label": ["cs.AI", "cs.CV"]},
        {"teks_dokumen": "Support vector machines and random forests are classic machine learning algorithms.", "daftar_label": ["cs.LG", "cs.AI"]},
        {"teks_dokumen": "Natural language processing systems utilize transformers to understand textual semantics.", "daftar_label": ["cs.CL", "cs.AI"]},
        {"teks_dokumen": "Reinforcement learning agents learn optimal policies through trial and error in simulation.", "daftar_label": ["cs.LG", "cs.AI", "cs.RO"]}
    ] * 250)
    print(f"Berhasil membuat fallback dataset dengan {len(df)} dokumen.")
"""))

# =====================================================================
# 3. SETUP HYPERPARAMETER BERDASARKAN TEORI
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 2. Setup Parameter Berdasarkan Teori (Wajib)
Pendefinisian hyperparameter krusial untuk fine-tuning Transformer (seperti `bert-mini` or `IndoBERT-Lite`). Parameter tidak menggunakan nilai default, melainkan diatur berdasarkan best practices fine-tuning Transformer untuk dataset teks yang tidak seimbang (multi-label).
"""))

cells.append(nbf.v4.new_code_cell("""\
import torch

# =====================================================================
# HYPERPARAMETER SETUP & JUSTIFICATION (THEORY-BASED)
# =====================================================================

# Model ringan untuk efisiensi komputasi dan deployment (TKT 4)
# Menggunakan pra-terlatih (pretrained) yang berukuran kecil untuk mempercepat konvergensi.
# Referensi: Turc et al., 2019 (Well-Read Students Learn Better: On the Importance of Pre-training Compact Models)
MODEL_CHECKPOINT = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Maximum sequence length: Dibutuhkan pemotongan teks karena arsitektur BERT memiliki limitasi 512 token.
# Nilai 256 dipilih untuk menyeimbangkan retensi informasi abstrak jurnal (biasanya ~200 kata) dan memori GPU (VRAM).
MAX_LENGTH = 128

# Batch Size: Berdampak langsung pada gradien estimasi. 
# 32 sangat direkomendasikan pada fine-tuning BERT base/mini untuk menghindari stochastic noise tinggi.
# Referensi: Devlin et al., 2018 (BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding)
BATCH_SIZE = 4

# Learning Rate: Untuk fine-tuning Transformer, learning rate yang terlalu tinggi merusak (catastrophic forgetting) pre-trained weights.
# Rentang optimal yang dibuktikan di makalah BERT adalah 2e-5, 3e-5, atau 5e-5.
LEARNING_RATE = 3e-5

# Epochs: Fine-tuning transformer biasanya hanya butuh 3-5 epochs. Lebih dari itu berisiko overfitting ekstrim,
# apalagi dengan model klasifikasi multi-label teks.
NUM_EPOCHS = 4

# Weight Decay: Digunakan dalam optimizer AdamW (Adam with Weight Decay) sebagai L2 Regularization.
# Nilai 0.01 efektif menekan model agar tidak overfit ke mayoritas kombinasi label tertentu (menjaga generalisasi bobot).
# Referensi: Loshchilov & Hutter, 2017 (Decoupled Weight Decay Regularization)
WEIGHT_DECAY = 0.01

# Warmup Steps ratio: Perlahan meningkatkan learning rate dari 0 ke LEARNING_RATE pada awal epoch (10% dari total iterasi).
# Ini mencegah pembaruan gradien awal yang terlalu agresif (menghindari ketidakstabilan training/gradien meledak).
WARMUP_RATIO = 0.1

print("Semua hyperparameter berhasil diinisialisasi.")
"""))

# =====================================================================
# 4. PEMODELAN & FINE-TUNING MULTI-LABEL
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 3. Pemodelan & Fine-Tuning Multi-Label
Mempersiapkan Dataset, Tokenizer, dan melakukan Fine-Tuning. Kita akan menggunakan `BCEWithLogitsLoss` dan fungsi aktivasi Sigmoid untuk mengevaluasi tiap label secara terpisah (probabilitas per label bukan Softmax).
"""))

cells.append(nbf.v4.new_code_cell("""\
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import numpy as np
import torch.nn as nn

# 1. Binarize Labels
mlb = MultiLabelBinarizer()
labels_encoded = mlb.fit_transform(df['daftar_label'])
num_labels = len(mlb.classes_)

# 2. Split Data
df_train, df_test, y_train, y_test = train_test_split(
    df['teks_dokumen'].values, labels_encoded, test_size=0.2, random_state=42
)

# 3. Inisialisasi Tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_CHECKPOINT)

# 4. Fungsi Preprocessing (Tokenisasi)
def preprocess_function(texts):
    return tokenizer(
        list(texts), 
        padding="max_length", 
        truncation=True, 
        max_length=MAX_LENGTH
    )

# 5. Konversi ke Format HuggingFace Dataset
train_dataset = Dataset.from_dict({
    "input_ids": preprocess_function(df_train)["input_ids"],
    "attention_mask": preprocess_function(df_train)["attention_mask"],
    "labels": y_train.astype(np.float32)
})

test_dataset = Dataset.from_dict({
    "input_ids": preprocess_function(df_test)["input_ids"],
    "attention_mask": preprocess_function(df_test)["attention_mask"],
    "labels": y_test.astype(np.float32)
})

# 6. Inisialisasi Model Transformer
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_CHECKPOINT, 
    num_labels=num_labels,
    problem_type="multi_label_classification"
)

# 7. Setup Training Arguments (Menggunakan parameter modern eval_strategy)
training_args = TrainingArguments(
    output_dir="./results",
    eval_strategy="epoch",
    learning_rate=LEARNING_RATE,
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=NUM_EPOCHS,
    weight_decay=WEIGHT_DECAY,
    warmup_ratio=WARMUP_RATIO,
    logging_steps=10,
    save_strategy="epoch",
    load_best_model_at_end=True,
    report_to="none"
)

# Custom Trainer untuk memastikan BCEWithLogitsLoss digunakan secara eksplisit (Dukungan **kwargs untuk v4.46+).
class MultiLabelTrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        logits = outputs.logits
        loss_fct = nn.BCEWithLogitsLoss()
        loss = loss_fct(logits.view(-1, self.model.config.num_labels), 
                        labels.view(-1, self.model.config.num_labels))
        return (loss, outputs) if return_outputs else loss

trainer = MultiLabelTrainer(
    model=model,
    args=training_args,
    train_dataset=train_dataset,
    eval_dataset=test_dataset,
)

print("Memulai Fine-Tuning...")
trainer.train()
print("Fine-Tuning Selesai!")
"""))

# =====================================================================
# 5. METADATA DATABASE INTEGRATION (FITUR 1: SIMPAN & LABELI)
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 4. Modul Database Terintegrasi (Simpan dan Labeli)
Modul ini mensimulasikan penyimpanan berkas kampus yang diupload ke basis data relasional **SQLite**. Dokumen disimpan lengkap bersama dengan metadata nama berkas, label hasil prediksi, serta representasi vektor maknanya (*embeddings*).
"""))

cells.append(nbf.v4.new_code_cell("""\
import sqlite3
import json
import os

# Fungsi mengekstrak representasi vektor dari model (Mean Pooling)
def get_document_embedding(text):
    model.eval()
    inputs = tokenizer(text, return_tensors="pt", padding="max_length", truncation=True, max_length=MAX_LENGTH)
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    with torch.no_grad():
        outputs = model.base_model(**inputs)
        # Ambil mean dari hidden states terakhir sebagai vektor representasi semantik
        embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
    return embeddings

# Inisialisasi Database SQLite lokal untuk demo
DB_PATH = "academic_metadata.db"

def init_academic_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(\"\"\"
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            content TEXT,
            labels TEXT,
            embedding TEXT
        )
    \"\"\")
    conn.commit()
    conn.close()
    print("Database SQLite Akademik siap.")

init_academic_db()

def save_and_label_document(filename, content, predicted_labels):
    \"\"\"
    Fungsi Fitur 1: Simpan dan Labeli dokumen ke SQLite Database.
    \"\"\"
    embedding = get_document_embedding(content).tolist()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute(\"\"\"
            INSERT OR REPLACE INTO documents (filename, content, labels, embedding)
            VALUES (?, ?, ?, ?)
        \"\"\", (filename, content, json.dumps(predicted_labels), json.dumps(embedding)))
        conn.commit()
        print(f"Berhasil Menyimpan & Melabeli: {filename}")
        print(f"Label Tersemat: {predicted_labels}\\n")
    except Exception as e:
        print(f"Gagal menyimpan berkas: {e}")
    finally:
        conn.close()
"""))

# =====================================================================
# 6. SEMANTIC SEARCH ENGINE (FITUR 2: CARIKAN MATERI YANG SESUAI)
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 5. Mesin Pencari Semantik STKI (Carikan Materi yang Sesuai)
Menggunakan perhitungan jarak matematis **Cosine Similarity** antara kueri pencarian dengan dokumen-dokumen yang tersimpan dalam basis data SQLite. Sistem akan menemukan dokumen yang memiliki kesamaan makna, bukan sekadar kesamaan kata mentah.
"""))

cells.append(nbf.v4.new_code_cell("""\
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def find_similar_materials(query_text, top_n=3):
    \"\"\"
    Fungsi Fitur 2: Carikan Materi yang Sesuai (Pencarian Semantik berbasis STKI)
    \"\"\"
    print(f"Mencari dokumen yang paling relevan dengan kueri: '{query_text}'\\n")
    query_vector = get_document_embedding(query_text).reshape(1, -1)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, content, labels, embedding FROM documents")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("Belum ada dokumen yang terdaftar di database. Silakan unggah dokumen terlebih dahulu.")
        return
        
    results = []
    for filename, content, labels, emb_str in rows:
        doc_vector = np.array(json.loads(emb_str)).reshape(1, -1)
        sim_score = cosine_similarity(query_vector, doc_vector)[0][0]
        results.append({
            "filename": filename,
            "content": content,
            "labels": json.loads(labels),
            "similarity": sim_score
        })
        
    # Urutkan berdasarkan kemiripan tertinggi
    results = sorted(results, key=lambda x: x["similarity"], reverse=True)
    
    print(f"Ditemukan {min(top_n, len(results))} materi paling relevan:")
    print("="*80)
    for i, res in enumerate(results[:top_n]):
        print(f"Peringkat {i+1:02d} | Berkas: {res['filename']} (Kemiripan: {res['similarity']*100:05.2f}%)")
        print(f"Label Kategori: {res['labels']}")
        print(f"Cuplikan Isi   : {res['content'][:150]}...")
        print("-"*80)
"""))

# =====================================================================
# 7. HYBRID SEMANTIC LABEL MAPPING (PREDIKSI DINAMIS)
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 6. Klasifikasi Dinamis (Hybrid Zero-Shot Semantic Mapping)
Untuk memfasilitasi demo sidang menggunakan dokumen kampus riil tanpa merubah arsitektur model, kita membandingkan vektor makna dokumen dengan vektor makna daftar label dinamis yang Anda inputkan secara *real-time* menggunakan Cosine Similarity.
"""))

cells.append(nbf.v4.new_code_cell("""\
def predict_dynamic_labels(text, candidate_labels, top_k=3):
    \"\"\"
    Melabeli dokumen baru secara 100% dinamis dengan membandingkan kesamaan semantik
    antara isi teks dengan teks label kandidat yang dimasukkan pengguna secara real-time.
    \"\"\"
    doc_embedding = get_document_embedding(text).reshape(1, -1)
    
    scores = []
    for label in candidate_labels:
        # Ekstrak makna dari label kandidat
        label_embedding = get_document_embedding(label).reshape(1, -1)
        similarity = cosine_similarity(doc_embedding, label_embedding)[0][0]
        scores.append((label, float(similarity)))
        
    # Urutkan label dari yang terdekat
    sorted_scores = sorted(scores, key=lambda x: x[1], reverse=True)
    
    print("="*80)
    print("PROSES PREDIKSI DINAMIS HIBRIDA (ZERO-SHOT):")
    print("="*80)
    for i, (label, score) in enumerate(sorted_scores[:top_k]):
        print(f"Kandidat {i+1:02d} | Label: {label: <25} | Confidence: {score*100:05.2f}%")
    print("="*80 + "\\n")
    
    # Ambil label yang memiliki kemiripan di atas ambang batas (threshold 30%)
    active_labels = [label for label, score in sorted_scores if score > 0.3]
    return active_labels
"""))

# =====================================================================
# 8. PARSING FILE & SMART DATA TRANSFORMER (FITUR 3: JADIKAN KE YANG LAIN)
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 7. Parsing Dokumen & Smart Data Transformer (Jadikan ke yang Lain)
Fungsi `extract_text_from_file` membaca dokumen multi-format. Ketika dokumen spreadsheet (CSV/XLSX) terdeteksi membawa label terstruktur, fitur **Jadikan ke yang Lain** akan berjalan dengan mentransformasi data mentah mahasiswa menjadi laporan analisis perkembangan prestasi.
"""))

cells.append(nbf.v4.new_code_cell("""\
import os
import docx
import pypdf
import pandas as pd

def extract_text_from_file(file_path):
    \"\"\"
    Ekstraksi teks mentah dari PDF, Word (docx), Excel, dan CSV.
    \"\"\"
    ext = os.path.splitext(file_path)[1].lower()
    text = ""
    
    try:
        if ext == '.csv':
            df = pd.read_csv(file_path)
            text_cols = df.select_dtypes(include=['object']).columns
            text = " ".join(df[text_cols[0]].dropna().astype(str).tolist()[:50]) if len(text_cols) > 0 else " ".join(df.iloc[:, 0].dropna().astype(str).tolist()[:50])
                
        elif ext in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)
            text_cols = df.select_dtypes(include=['object']).columns
            text = " ".join(df[text_cols[0]].dropna().astype(str).tolist()[:50]) if len(text_cols) > 0 else " ".join(df.iloc[:, 0].dropna().astype(str).tolist()[:50])
                
        elif ext == '.docx':
            doc = docx.Document(file_path)
            text = '\\n'.join([para.text for para in doc.paragraphs])
            
        elif ext == '.pdf':
            reader = pypdf.PdfReader(file_path)
            text = '\\n'.join([page.extract_text() for page in reader.pages if page.extract_text()])
            
        else:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                text = f.read()
    except Exception as e:
        print(f"Error parsing file {file_path}: {e}")
        
    return text.strip()

def transform_academic_data(file_path, transformation_type):
    \"\"\"
    Fungsi Fitur 3: Jadikan ke yang Lain (Smart Data Transformer)
    Mentransformasi data mentah akademis menjadi laporan analitis baru.
    \"\"\"
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in ['.csv', '.xlsx', '.xls']:
        print("Fitur 'Jadikan ke yang lain' hanya mendukung format terstruktur (CSV/Excel).")
        return
        
    print(f"Menginisialisasi Fitur 'Jadikan ke yang lain' untuk berkas: {os.path.basename(file_path)}")
    print(f"Tipe Transformasi Terpilih: {transformation_type}\\n")
    
    try:
        df = pd.read_csv(file_path) if ext == '.csv' else pd.read_excel(file_path)
        
        # Validasi kolom contoh data akademis tiruan untuk demo presentasi
        required_cols = ['Nama', 'Semester', 'Mata_Kuliah', 'Nilai', 'SKS']
        # Jika kolom tidak cocok dengan dataset demo, kita generate simulasi data akademis di Pandas untuk demo visual
        if not all(col in df.columns for col in required_cols):
            print("Struktur kolom dokumen tidak standar. Membuat simulasi dataset akademis civitas akademika untuk presentasi...")
            df = pd.DataFrame({
                'Nama': ['Budi', 'Budi', 'Budi', 'Ani', 'Ani', 'Ani', 'Cici', 'Cici'],
                'Semester': [1, 2, 3, 1, 2, 3, 1, 2],
                'Mata_Kuliah': ['Aljabar', 'Kalkulus', 'Struktur Data', 'Aljabar', 'Fisika', 'Struktur Data', 'Kalkulus', 'Fisika'],
                'Nilai': [85, 90, 78, 92, 88, 85, 70, 75],
                'SKS': [3, 4, 3, 3, 3, 3, 4, 3]
            })
            print("Simulasi Dataset Akademik Sukses Dibuat:")
            display(df)
            print("-" * 80)
            
        # Eksekusi Transformasi Data berbasis Pandas secara efisien
        if transformation_type == "perkembangan_ipk":
            # Rumus IPK = Rata-rata Nilai dibobot SKS per Semester
            df['Bobot_Nilai'] = df['Nilai'] * df['SKS']
            agg = df.groupby(['Nama', 'Semester']).agg({'Bobot_Nilai': 'sum', 'SKS': 'sum'}).reset_index()
            agg['IPK_Semester'] = agg['Bobot_Nilai'] / agg['SKS']
            # Konversi skala 100 ke skala 4.0
            agg['IPK_Skala_4'] = (agg['IPK_Semester'] / 100) * 4.0
            
            print("HASIL TRANSFORMASI: PERKEMBANGAN PRESTASI (IPK) MAHASISWA PER SEMESTER")
            display(agg[['Nama', 'Semester', 'SKS', 'IPK_Skala_4']])
            
        elif transformation_type == "mata_kuliah_paling_diminati":
            # Menghitung mata kuliah paling populer / sering diambil mahasiswa
            diminati = df.groupby('Mata_Kuliah').agg({'Nama': 'count', 'Nilai': 'mean'}).reset_index()
            diminati.columns = ['Mata_Kuliah', 'Jumlah_Peminat', 'Rata_Rata_Nilai_Kelas']
            diminati = diminati.sort_values(by='Jumlah_Peminat', ascending=False)
            
            print("HASIL TRANSFORMASI: TINGKAT MINAT MATA KULIAH & RATA-RATA NILAI KELAS")
            display(diminati)
            
        else:
            print("Tipe transformasi tidak dikenal.")
    except Exception as e:
        print(f"Gagal melakukan transformasi data: {e}")
"""))

# =====================================================================
# 9. INTEGRATED DEMO PIPELINE RUNNER
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 8. Demo Kasus Pengujian Sidang (Civitas Academica)
Simulasi ujung-ke-ujung (end-to-end) yang menunjukkan bagaimana dokumen baru diproses secara semantik, dimasukkan ke database terstruktur, dicari relevansinya, hingga diubah bentuk datanya.
"""))

cells.append(nbf.v4.new_code_cell("""\
# Skenario Demo Sidang:
print("="*80)
print("MEMULAI SIMULASI DEMO END-TO-END UNTUK CIVITAS ACADEMICA")
print("="*80 + "\\n")

# 1. Dokumen Baru yang Masuk (Simulasi berkas transkrip kelulusan)
dokumen_kampus = \"\"\"
Transkrip Akademik Resmi. Nama Mahasiswa: Budi Santoso. NIM: 10123001. 
Telah menyelesaikan perkuliahan dengan hasil sebagai berikut: Semester 1 meraih nilai tinggi pada mata kuliah Aljabar Linier dan Pemrograman Dasar. 
Semester 2 berprestasi di Kalkulus 2 dan Struktur Data dengan nilai sangat memuaskan. 
Menunjukkan minat besar pada rekayasa perangkat lunak dan komputasi sains.
\"\"\"

# 2. Definisikan label dinamis bebas saat presentasi (Fitur Zero-Shot)
label_presentasi = ["Administrasi Akademik", "Laporan Keuangan Kampus", "Proposal Penelitian Dosen", "Hasil Studi Mahasiswa"]

# 3. Jalankan Klasifikasi Dinamis Semantik
label_terdeteksi = predict_dynamic_labels(dokumen_kampus, label_presentasi, top_k=2)

# 4. Fitur 1: Simpan dan Labeli ke Database SQLite
save_and_label_document("transkrip_budi.pdf", dokumen_kampus, label_terdeteksi)

# 5. Fitur 2: Carikan Materi yang Sesuai (Semantic Search STKI)
find_similar_materials("Saya ingin mencari dokumen laporan hasil belajar mahasiswa angkatan baru")

# 6. Fitur 3: Jadikan ke yang Lain (Smart Data Transformer)
# Menggunakan berkas dummy csv untuk demonstrasi pengolahan IPK
with open("simulasi_nilai.csv", "w") as f:
    f.write("Nama,Semester,Mata_Kuliah,Nilai,SKS\\n") # write header dummy
    
transform_academic_data("simulasi_nilai.csv", "perkembangan_ipk")
"""))

# =====================================================================
# 9A. EVALUASI MODEL KLASIFIKASI MULTI-LABEL
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 9. Evaluasi Model Klasifikasi Multi-Label
Mengukur performa model secara kuantitatif menggunakan metrik **Precision**, **Recall**, dan **F1-Score** untuk kelas positif maupun negatif, serta menampilkan **Confusion Matrix** dan **Classification Report** per label.

**Referensi:** Manning, Raghavan & Schütze (2008) — *Introduction to Information Retrieval*, Cambridge University Press.
"""))

cells.append(nbf.v4.new_code_cell("""\
from sklearn.metrics import classification_report, confusion_matrix, multilabel_confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Prediksi pada test set
model.eval()
all_preds = []
all_labels = []

for i in range(0, len(test_dataset), BATCH_SIZE):
    batch_end = min(i + BATCH_SIZE, len(test_dataset))
    batch = test_dataset[i:batch_end]
    input_ids = torch.tensor(batch["input_ids"]).to(next(model.parameters()).device)
    attention_mask = torch.tensor(batch["attention_mask"]).to(next(model.parameters()).device)
    labels_batch = torch.tensor(batch["labels"])

    with torch.no_grad():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask)
        logits = outputs.logits.cpu()
        preds = (torch.sigmoid(logits) > 0.5).int()

    all_preds.append(preds)
    all_labels.append(labels_batch.int())

y_pred = torch.cat(all_preds, dim=0).numpy()
y_true = torch.cat(all_labels, dim=0).numpy()

# 2. Classification Report (Precision, Recall, F1 per label)
label_names = list(mlb.classes_)
print("=" * 80)
print("CLASSIFICATION REPORT (Per Label - Positif & Negatif)")
print("=" * 80)
print(classification_report(y_true, y_pred, target_names=label_names, zero_division=0))

# 3. Multilabel Confusion Matrix
mcm = multilabel_confusion_matrix(y_true, y_pred)

# Hitung metrik positif & negatif secara manual per label
print("\\n" + "=" * 80)
print("METRIK POSITIF & NEGATIF PER LABEL")
print("=" * 80)
for idx, label in enumerate(label_names):
    tn, fp, fn, tp = mcm[idx].ravel()
    prec_pos = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec_pos = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1_pos = 2 * prec_pos * rec_pos / (prec_pos + rec_pos) if (prec_pos + rec_pos) > 0 else 0.0
    prec_neg = tn / (tn + fn) if (tn + fn) > 0 else 0.0
    rec_neg = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    f1_neg = 2 * prec_neg * rec_neg / (prec_neg + rec_neg) if (prec_neg + rec_neg) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
    fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0
    acc = (tp + tn) / (tp + tn + fp + fn)

    print(f"\\nLabel: {label}")
    print(f"  TP={tp}, FP={fp}, TN={tn}, FN={fn}")
    print(f"  Precision+ = {prec_pos:.4f} | Recall+ = {rec_pos:.4f} | F1+ = {f1_pos:.4f}")
    print(f"  Precision- = {prec_neg:.4f} | Recall- = {rec_neg:.4f} | F1- = {f1_neg:.4f}")
    print(f"  Accuracy   = {acc:.4f}  | FPR = {fpr:.4f} | FNR = {fnr:.4f}")

# 4. Visualisasi Confusion Matrix (Top 5 Label)
fig, axes = plt.subplots(1, min(5, len(label_names)), figsize=(4 * min(5, len(label_names)), 4))
if len(label_names) == 1:
    axes = [axes]
for idx in range(min(5, len(label_names))):
    cm = mcm[idx]
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[idx],
                xticklabels=['Pred 0', 'Pred 1'], yticklabels=['True 0', 'True 1'])
    axes[idx].set_title(label_names[idx][:15], fontsize=9)
plt.suptitle("Confusion Matrix per Label (Top 5)", fontsize=12, fontweight='bold')
plt.tight_layout()
plt.show()

# 5. Akurasi Keseluruhan (Exact Match Ratio)
exact_match = np.all(y_pred == y_true, axis=1).mean()
print(f"\\nExact Match Ratio (Akurasi Keseluruhan): {exact_match*100:.2f}%")
"""))

# =====================================================================
# 9B. EVALUASI PENCARIAN STKI (10 QUERY + GROUND TRUTH)
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 10. Evaluasi Pencarian Semantik STKI (Precision@K, MAP, NDCG@K)
Mengevaluasi kualitas peringkat hasil pencarian menggunakan **10 kueri pengujian** dengan ground truth yang telah didefinisikan. Metrik yang dihitung: **Precision@5**, **MAP**, dan **NDCG@5**.

**Referensi:** Järvelin & Kekäläinen (2002) — *Cumulated Gain-Based Evaluation of IR Techniques*, ACM TOIS.
"""))

cells.append(nbf.v4.new_code_cell("""\
import math

# Fungsi evaluasi IR
def precision_at_k(retrieved_relevance, k):
    return sum(retrieved_relevance[:k]) / k

def average_precision(retrieved_relevance, total_relevant):
    if total_relevant == 0:
        return 0.0
    ap, hits = 0.0, 0
    for i, rel in enumerate(retrieved_relevance):
        if rel == 1:
            hits += 1
            ap += hits / (i + 1)
    return ap / total_relevant

def dcg_at_k(relevance, k):
    return sum((2**relevance[i] - 1) / math.log2(i + 2) for i in range(min(k, len(relevance))))

def ndcg_at_k(retrieved_relevance, k, total_relevant):
    dcg = dcg_at_k(retrieved_relevance, k)
    ideal = sorted(retrieved_relevance, reverse=True)
    if total_relevant > len(ideal):
        ideal = [1] * total_relevant + [0] * (k - total_relevant)
    idcg = dcg_at_k(ideal, k)
    return dcg / idcg if idcg > 0 else 0.0

# Ambil seluruh dokumen dari database untuk evaluasi pencarian
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("SELECT filename, content, labels, embedding FROM documents")
all_docs = cursor.fetchall()
conn.close()

if len(all_docs) == 0:
    print("Database kosong, tidak dapat menjalankan evaluasi STKI.")
else:
    # 10 Kueri pengujian dengan konteks berbeda
    test_queries = [
        {"query": "transkrip nilai mahasiswa informatika IPK cumlaude",
         "relevant_keywords": ["transkrip"]},
        {"query": "rencana studi KRS semester genap mata kuliah",
         "relevant_keywords": ["rencana_studi", "krs"]},
        {"query": "daftar nama dosen pengajar fakultas teknologi",
         "relevant_keywords": ["dosen", "pengajar"]},
        {"query": "pembayaran UKT keuangan mahasiswa lunas",
         "relevant_keywords": ["keuangan", "ukt"]},
        {"query": "kurikulum silabus jurusan informatika",
         "relevant_keywords": ["kurikulum", "silabus"]},
        {"query": "nilai akademik mahasiswa predikat memuaskan",
         "relevant_keywords": ["transkrip", "nilai"]},
        {"query": "jadwal perkuliahan semester berjalan SKS",
         "relevant_keywords": ["krs", "sks", "rencana_studi"]},
        {"query": "NIP dosen spesialisasi kecerdasan buatan",
         "relevant_keywords": ["dosen"]},
        {"query": "IPK kumulatif mahasiswa program studi",
         "relevant_keywords": ["transkrip", "ipk"]},
        {"query": "struktur mata kuliah capaian pembelajaran",
         "relevant_keywords": ["kurikulum", "silabus"]},
    ]

    K = 5
    all_precisions, all_aps, all_ndcgs = [], [], []

    print("=" * 90)
    print(f"EVALUASI PENCARIAN STKI — {len(test_queries)} KUERI PENGUJIAN (K={K})")
    print("=" * 90)

    for qi, tq in enumerate(test_queries):
        query_text = tq["query"]
        query_embedding = get_document_embedding(query_text).reshape(1, -1)

        # Hitung similarity dan ranking
        scored_docs = []
        for fname, content, labels, emb_str in all_docs:
            doc_vec = np.array(json.loads(emb_str)).reshape(1, -1)
            sim = cosine_similarity(query_embedding, doc_vec)[0][0]
            scored_docs.append((fname, content, labels, sim))

        scored_docs.sort(key=lambda x: x[3], reverse=True)
        top_k = scored_docs[:K]

        # Tentukan relevansi berdasarkan ground truth keywords
        relevance = []
        for fname, content, labels, sim in top_k:
            is_relevant = any(kw in fname.lower() or kw in content.lower()
                            for kw in tq["relevant_keywords"])
            relevance.append(1 if is_relevant else 0)

        # Hitung total dokumen relevan di seluruh korpus
        total_rel = sum(1 for fname, content, _, _ in all_docs
                       if any(kw in fname.lower() or kw in content.lower()
                             for kw in tq["relevant_keywords"]))

        p_at_k = precision_at_k(relevance, K)
        ap = average_precision(relevance, min(total_rel, K))
        ndcg = ndcg_at_k(relevance, K, min(total_rel, K))

        all_precisions.append(p_at_k)
        all_aps.append(ap)
        all_ndcgs.append(ndcg)

        print(f"\\nQ{qi+1}: \\"{query_text[:50]}...\\"")
        print(f"  Relevansi Top-{K}: {relevance}")
        print(f"  Precision@{K}={p_at_k:.4f} | AP={ap:.4f} | NDCG@{K}={ndcg:.4f}")

    # Ringkasan keseluruhan
    mean_p = np.mean(all_precisions)
    map_score = np.mean(all_aps)
    mean_ndcg = np.mean(all_ndcgs)

    print("\\n" + "=" * 90)
    print("RINGKASAN EVALUASI STKI")
    print("=" * 90)
    print(f"  Mean Precision@{K}  : {mean_p*100:.2f}%")
    print(f"  MAP                : {map_score*100:.2f}%")
    print(f"  Mean NDCG@{K}       : {mean_ndcg*100:.2f}%")
    print("=" * 90)
"""))


# =====================================================================
# 10. EKSPOR ONNX DENGAN AUTO-DEPENDENCY CHECK
# =====================================================================
cells.append(nbf.v4.new_markdown_cell("""\
## 9. Ekspor Model ke ONNX (Persiapan TKT 4 - Latensi Rendah)
Model diekspor ke dalam format ONNX agar graf komputasi teroptimasi, sehingga dapat dijalankan dengan cepat di CPU server kampus secara offline tanpa membutuhkan ketergantungan PyTorch pada tahap produksi.
"""))

cells.append(nbf.v4.new_code_cell("""\
import os

# Mengatasi error ModuleNotFoundError: No module named 'onnxscript' di beberapa versi PyTorch/Colab secara dinamis
try:
    import onnxscript
except ModuleNotFoundError:
    print("onnxscript tidak ditemukan. Menginstall secara otomatis...")
    get_ipython().system("pip install -q onnxscript onnx")
    import onnxscript

print("Mengekspor model PyTorch ke format ONNX...")

output_dir = "./onnx_model"
os.makedirs(output_dir, exist_ok=True)
onnx_path = os.path.join(output_dir, "multi_label_model.onnx")

dummy_input = {
    "input_ids": torch.zeros((1, MAX_LENGTH), dtype=torch.long).to(next(model.parameters()).device),
    "attention_mask": torch.zeros((1, MAX_LENGTH), dtype=torch.long).to(next(model.parameters()).device)
}
# --- SURGICAL FIX: Bypass Bug SDPA Transformers v4.46+ pada PyTorch Tracer ---
# Patch ini memaksa BERT menggunakan standar mask 4D ketimbang sdpa_mask yang memecah JIT Tracer
def onnx_friendly_create_attention_masks(*args, **kwargs):
    self = args[0]
    attention_mask = args[1] if len(args) > 1 else kwargs.get('attention_mask')
    extended_attention_mask = attention_mask.unsqueeze(1).unsqueeze(2)
    extended_attention_mask = extended_attention_mask.to(dtype=self.dtype)
    extended_attention_mask = (1.0 - extended_attention_mask) * -10000.0
    return extended_attention_mask, None

import types
model.base_model._create_attention_masks = types.MethodType(onnx_friendly_create_attention_masks, model.base_model)
# -----------------------------------------------------------------------------

# Ekspor base_model dengan Wrapper untuk menghindari error JIT tracing (got multiple values for argument 'use_cache')
class ONNXExportWrapper(torch.nn.Module):
    def __init__(self, base_model):
        super().__init__()
        self.base_model = base_model
        
    def forward(self, input_ids, attention_mask):
        # Force kwargs to bypass PyTorch positional tracer bugs on HF Models
        # Set return_dict=False to prevent "tuple index out of range" during PyTorch JIT tracing
        outputs = self.base_model(
            input_ids=input_ids, 
            attention_mask=attention_mask,
            return_dict=False
        )
        # outputs[0] corresponds to the last_hidden_state
        return outputs[0]

export_model = ONNXExportWrapper(model.base_model).cpu()

torch.onnx.export(
    export_model,
    (dummy_input["input_ids"], dummy_input["attention_mask"]),
    onnx_path,
    export_params=True,
    opset_version=14,
    do_constant_folding=True,
    input_names=["input_ids", "attention_mask"],
    output_names=["last_hidden_state"],
    dynamic_axes={
        "input_ids": {0: "batch_size", 1: "sequence_length"},
        "attention_mask": {0: "batch_size", 1: "sequence_length"},
        "last_hidden_state": {0: "batch_size", 1: "sequence_length"}
    }
)

# Simpan tokenizer untuk kebutuhan deploy
tokenizer.save_pretrained(output_dir)

print(f"Berhasil! Model diekspor ke: {onnx_path}")
print(f"Tokenizer disimpan di direktori: {output_dir}")
print("Pondasi eksperimen TKT 3 selesai. Model siap diimplementasikan pada sistem offline (TKT 4) kampus!")
"""))

nb['cells'] = cells
with open('c:/laragon/www/_NotWeb/_TemuKembaliInformasi/UAS/DS/Sistem_Temu_Kembali_Informasi.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print("DS/Sistem_Temu_Kembali_Informasi.ipynb berhasil dibuat!")
