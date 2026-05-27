# Spesifikasi Teknis: Arsitektur & Justifikasi Sistem
**Tahapan Eksperimen: TKT 3 (Data Science)**

Dokumen ini memuat justifikasi teoretis berbasis bukti (*evidence-based*) mengenai pemilihan model, penyiapan dataset, mitigasi error yang pernah terjadi, serta metodologi klasifikasi dinamis untuk sistem kecerdasan dokumen civitas akademika.

---

## 1. Pemilihan Model: Mengapa Menggunakan MiniLM Multilingual?

Kami menetapkan **`paraphrase-multilingual-MiniLM-L12-v2`** (Sentence-Transformers) sebagai model dasar pembelajaran. Pemilihan ini didasarkan pada argumen teoretis dan praktis berikut (yang memicu transisi dari model indobert-mini sebelumnya):

* **Ketahanan Semantik Multilingual & Latensi Rendah (Kebutuhan TKT 4):**
  Model ini dirancang khusus untuk pencocokan makna (*Semantic Textual Similarity*) dan mendukung lebih dari 50 bahasa, termasuk Bahasa Indonesia. Model ini sangat tangguh terhadap typo atau penggunaan sinonim. Meskipun memiliki kemampuan SOTA (*State-of-the-Art*), proses ekspor ke format **ONNX** menghasilkan arsitektur yang ringan dan efisien untuk dijalankan di CPU lokal kampus secara offline pada tahap STKI (TKT 4).
* **Dual-Utility (Klasifikasi & Representasi Vektor):**
  Selain bertindak sebagai classifier multi-label, model ini mampu mengekstrak *pooled embeddings* (vektor berdimensi 384 melalui *Mean Pooling*) dari lapisan tersembunyinya. Vektor representasi semantik ini sangat kaya akan makna kontekstual yang digunakan untuk mengaktifkan fitur pencarian semantik (STKI) dan klasifikasi dinamis.

---

## 2. Pemilihan Dataset: ArXiv API (Multidisiplin & Publik)

Untuk menghindari penggunaan data sintetis/buatan yang kurang representatif atau dataset Kaggle yang sering kali *out-of-date*, kami menggunakan **ArXiv API** secara murni dengan kueri multidisiplin:
* **Mengapa ArXiv API?** 
  ArXiv menyediakan akses gratis ke ribuan dokumen sains, matematika, ekonomi, dan komputer yang ditulis oleh civitas akademika global secara *real-time*.
* **Representasi Kampus:** 
  Dengan menarik data dari kategori `cs.AI` (AI), `cs.CY` (Komputer dan Masyarakat - Pendidikan), `stat.AP` (Statistika Terapan), dan `q-fin` (Ekonomi/Keuangan), kita mensimulasikan tipe-tipe dokumen di lingkungan universitas (proposal penelitian, laporan administratif, silabus, dan data nilai/statistika).

---

## 3. Metodologi Klasifikasi Dinamis (Hybrid Zero-Shot)

Untuk mengatasi keterbatasan model klasifikasi terbimbing (*supervised*) yang labelnya terkunci setelah dilatih, kami menerapkan arsitektur **Hybrid Zero-Shot Classification**:

1. **Model MiniLM** dilatih di Colab menggunakan dataset ArXiv untuk menguasai representasi semantik bahasa.
2. Ketika berkas baru (misal: PDF/CSV civitas akademika) diunggah saat presentasi, model mengekstrak **vektor embedding** dari teks dokumen tersebut.
3. Pengguna memasukkan kata kunci label kampus apa saja secara dinamis (`["Administrasi", "Laporan Nilai", "Skripsi"]`).
4. Sistem menghitung tingkat kedekatan semantik (**Cosine Similarity**) antara vektor dokumen dengan vektor label dinamis tersebut.
5. Dokumen diklasifikasikan ke label dengan skor kemiripan tertinggi secara *real-time*, memberikan fleksibilitas penuh saat presentasi tanpa perlu melatih ulang model dari awal!

---

## 4. Mitigasi Error yang Pernah Terjadi & Solusinya

Berikut adalah rangkuman masalah teknis yang telah dimitigasi dan diselesaikan di dalam rancangan kode terbaru kami:

| Masalah / Error | Deskripsi / Penyebab | Solusi Teknis yang Diterapkan |
|---|---|---|
| **HTTP Error 429** | ArXiv API mendeteksi kueri beruntun dari server Google Colab dan memblokirnya. | Menambahkan header `User-Agent` browser modern dan menerapkan fungsi `fetch_arxiv_with_retry` dengan mekanisme *Exponential Backoff* (menunggu otomatis sebelum mencoba kembali). |
| **TypeError: TrainingArguments ... 'evaluation_strategy'** | Pustaka `transformers` versi terbaru di Colab telah menghapus parameter usang tersebut. | Mengubah parameter tersebut menjadi **`eval_strategy`** agar kompatibel secara native dengan pustaka modern. |
| **TypeError: compute_loss() got 'num_items_in_batch'** | Terdapat perubahan *signature* internal pada metode `Trainer.compute_loss` di Hugging Face v4.46+. | Memodifikasi *signature* fungsi custom trainer menjadi `compute_loss(self, model, inputs, return_outputs=False, **kwargs)` untuk menampung argumen ekstra secara aman. |
| **ModuleNotFoundError: 'onnxscript'** | Versi terbaru ekspor ONNX di PyTorch membutuhkan paket `onnxscript` dan `onnx` secara eksplisit. | Menyematkan instalasi paket tersebut di cell pertama, serta menambahkan blok *try-except auto-installer* dinamis di dalam cell ekspor ONNX. |
