# [L3] Arsitektur ETL (Extract, Transform, Load) & Mitigasi Dimensional Collapse

_Konteks: Bagian dari Topologi Presentasi Data Pipeline_

Dokumen ini disusun sebagai **Panduan Pertahanan (Defense Document)** apabila dipertanyakan mengapa sistem Ingesti Data Hukum (HAKI) dari API eksternal (*Pasal.id*) tidak diintegrasikan langsung ke dalam antarmuka *Dropzone/Upload GUI* di Halaman Command Center Data Science (DS), melainkan menggunakan *Pipeline Script Python* terpisah di terminal.

## 1. Ancaman Dimensional Collapse akibat Parsing JSON
Antarmuka GUI dirancang dengan modul ekstraktor dokumen standar (PyPDF2, python-docx, CSV parser) yang mengasumsikan aliran teks kohesif manusiawi. 

Jika GUI menerima dan mem-parsing berkas JSON (JavaScript Object Notation) mentah hasil respons API yang mengandung struktur *nested arrays* dan sintaks metadata, seperti:

```json
{
  "work": {
    "frbr_uri": "/akn/id/act...",
    "status": "berlaku"
  },
  "articles": [...]
}
```

Sistem akan membaca simbol kurung kurawal `{`, kutip ganda `"`, dan label *key* bahasa pemrograman sebagai bagian integral dari teks hukum tersebut. Saat dilempar ke model **Dense MiniLM-L12-v2**, hal ini akan memicu polusi ruang vektor semantik (Semantic Vector Pollution), di mana kata kunci pemrograman ("work", "id", "status") akan mengaburkan inti dari teks hukum yang sebenarnya. Fenomena degradasi representasi matematis inilah yang disebut sebagai **Dimensional Collapse** pada arsitektur temu kembali.

Skrip `vectorize_hukum.py` bertindak sebagai lapisan **Transform (ETL)** yang secara bedah (*surgical*) mengekstraksi nilai `title` dan `content` dari pohon JSON, mengabaikan seluruh sintaks metadata, sehingga hanya kemurnian Teks Hukum (Legal Corpus) yang disuntikkan ke dalam model AI.

## 2. Pengekangan I/O (I/O Bottleneck) & Rate Limit Compliance
Menyuntikkan $\ge 1.000$ berkas secara bersamaan ke dalam Flask backend melalui antarmuka web memicu antrean *Blocking HTTP Request*. 
Model asinkronus (CLI Pipeline) dirancang untuk memisahkan **I/O Network** dengan **I/O CPU**:
1. **Fase Extract (`ingest_pasal.py`)**: Mematuhi batas *Rate Limit* server eksternal (60 permintaan/menit) tanpa membuat peramban Web (*browser*) pengguna mengalami *Timeout (HTTP 504)* karena *long-polling* berjam-jam.
2. **Fase Load (`vectorize_hukum.py`)**: Mengeksekusi generasi *Embedding* matriks (384-Dimensi) memanfaatkan utilitas *multi-threading* CPU level sistem operasi yang terisolasi dari proses web-server (Flask), memastikan RAM server utama tidak terkena ancaman *Out of Memory (OOM)*.

## 3. Isolasi Polymorphic Database (B-Tree Efficiency)
Pemaksaan penggabungan data Skripsi/Jurnal dengan Hukum Undang-Undang dalam 1 tabel yang sama (tanpa pemisahan domain) akan menghasilkan *Sparse Table* (banyak nilai `NULL` di kolom metadata). 
Melalui sistem ETL ini, pembentukan file **`db_hukum.db`** dilakukan secara sentralistik di belakang layar. Proses pencarian (B-Tree Indexing) oleh SQLite SQLite akan beroperasi secara optimum dengan laju kecepatan $O(\log N)$ tanpa terbebani oleh metadata lintas-domain.
