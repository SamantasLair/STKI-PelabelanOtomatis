# Arsitektur Fungsional Sistem Terintegrasi (DS + STKI)

Dokumen ini membedah rancangan ide awal mengenai evolusi sistem menjadi tiga pilar utama yang saling melengkapi. Pilar ini memisahkan secara tegas mana wilayah ranah *Data Science* (Klasifikasi/Transformasi) dan mana wilayah *Information Retrieval* (Pencarian Teks), serta bagaimana keduanya dilebur pada pilar ketiga.

## 1. Tabel Perbandingan Paradigma Fitur

| Aspek | 1. "Simpan & Labeli" (Murni DS) | 2. "Carikan Materi" (Murni STKI) | 3. "Jadikan ke yang Lain" (Hibrida DS + STKI) |
| :--- | :--- | :--- | :--- |
| **Definisi Utama** | Pemetaan otomatis (*Zero-Shot Classification*) dari dokumen mentah ke dalam label/taksonomi struktur ruang vektor. | Mesin pencari (*Search Engine*) dan sistem rekomendasi berbasis kueri pengguna terhadap korpus dokumen. | Transformasi generatif dokumen mentah menjadi bentuk/laporan turunan berdasarkan cetak biru dokumen lain yang relevan. |
| **Fokus Algoritma** | **Klasifikasi Node**: *Neural Network* ONNX, *Sigmoid Calibration*, *Argmax*. | **Jarak Vektor**: TPD-Cosine Similarity (Dense) + BM25 (Sparse Leksikal). | **Sistem Rantai (Pipeline)**: Temu-Kembali (*Retrieval*) $\rightarrow$ Transformasi/Ekstraksi Konten (*Extraction*). |
| **Input Data** | Teks mentah / Berkas PDF/DOCX murni. | Kata kunci (kueri panjang/pendek). | Berkas Data Penuh (*Raw Dump* csv/xlsx). |
| **Output Sistem** | Metadata & Label (contoh: *Jurnal Ilmiah $\rightarrow$ Sinta 2*). | Daftar Dokumen Rekomendasi (Papan Peringkat / *Leaderboard*). | Laporan Baru (contoh: *Data Penuh $\rightarrow$ IPK per Semester*). |
| **Aksi Terhadap Database** | **WRITE** (Menulis dokumen & label ke SQLite). | **READ** (Membaca vektor dan menghitung jarak). | **READ & GENERATE** (Mencari dokumen acuan, lalu membentuk data baru). |
| **Kecepatan Waktu Nyata**| Relatif Lambat (butuh propagasi *neural network* per berkas). | Sangat Cepat (hanya hitung aljabar matriks $\mathbf{A} \cdot \mathbf{B}$). | Paling Lambat (butuh pencarian STKI $\rightarrow$ klasifikasi DS $\rightarrow$ pembentukan data). |

---

## 2. Analisis & Saran Desain Sistem

### Pilar 1: Simpan & Labeli (Klasifikasi DS)
Ini adalah "Gerbang Utama" sistem Anda. Model murni bekerja menebak isi dokumen.
* **Status Saat Ini:** Telah terimplementasi dengan baik via `Batch Classifier` menggunakan BERT ONNX Zero-Shot.
* **Saran:** Pastikan proses ini berjalan di latar belakang (*background job* atau via fitur *Regenerate Label Batch*). Jangan jadikan ini proses *blocking* saat presentasi, karena proses iterasi *neural net* pada ratusan data akan memakan waktu.

### Pilar 2: Carikan Materi (Mesin Pencari STKI)
Ini adalah "Etalase" sistem Anda. Sistem merekomendasikan bahan.
* **Status Saat Ini:** Terimplementasi kokoh via tab `Leaderboard Search` dan `Smart Recommendation` (Grid 2-Kolom Data vs Dokumen).
* **Saran:** Karena murni perhitungan matematika aljabar (Cosine) dan pencocokan teks (BM25), pastikan matriks pramuat (*pre-loaded embeddings*) disimpan di RAM aplikasi (Flask) agar transisi UI terasa seketika (*seamless zero-latency*).

### Pilar 3: Jadikan ke yang Lain (Ekstraksi Transformasional Hibrida)
Ini adalah tingkat lanjut (*Advanced Tier*) dari sistem. Gagasan Anda sangat cerdas dan mirip dengan paradigma ***Retrieval-Augmented Generation (RAG)***. 
* **Cara Kerjanya secara Sistem:**
  1. Pengguna memasukkan data XLSX Mahasiswa mentah ("Data Penuh").
  2. Pengguna memencet tombol *"Ubah ke Format Laporan X"*.
  3. **STKI Bekerja:** Sistem STKI mencari dokumen di *database* yang paling mirip dengan format target (misal: mencari template "Laporan Rata-rata Mata Kuliah").
  4. **DS Bekerja:** Setelah format template ditemukan dan dilabeli, model DS (seperti *Transformer* atau *Rule-based extractor*) mengekstraksi kolom-kolom spesifik dari data mentah mahasiswa untuk disuntikkan ke format yang baru.
* **Saran Tantangan Teknis:**
  - *Data Transformation* sangat sulit dilakukan dengan sekadar model klasifikasi statis (seperti BERT-mini Anda sekarang). 
  - **Opsi Realistis:** Alih-alih menggunakan AI/DS murni untuk "mengubah" data (*yang rawan halusinasi bentuk tabel*), gunakan **STKI untuk menemukan *Template Mapping***. Jadi, setiap label di database Anda dikaitkan dengan skrip ekstraksi Pandas. Jika STKI menebak pengguna ingin "IPK per Semester", STKI akan memanggil skrip *Data Science* khusus (contoh: `df.groupby('Semester')['Nilai'].mean()`).
  - **UX Seamless:** Di UI, Anda bisa menambahkan tombol **"⚡ Generate Insight"** di setiap kartu hasil pencarian tab Rekomendasi. Jika tombol itu ditekan, sistem otomatis menyedot format acuan dokumen tersebut dan menerapkannya pada data mentah yang ada di *clipboard* pengguna.

## 3. Kesimpulan Presentasi
Jika Anda membawa tabel dan konsep ini ke sidang, Anda secara de facto memisahkan tanggung jawab ilmu (*Separation of Concerns*). 
- Dosen yang bertanya soal **Data Science**, akan Anda jawab dengan Pilar 1 & 3 (Ekstraksi, Klasifikasi, Agregasi).
- Dosen yang bertanya soal **Information Retrieval**, akan Anda jawab dengan Pilar 2 & 3 (BM25, Cosine Similarity, TF-IDF). 
Ini memberikan justifikasi logis bahwa proyek Anda benar-benar memenuhi irisan dua mata kuliah secara sempurna.

---

## 4. Kajian Teoretis Pilar 3 (Transformasi Hibrida STKI + DS)

Pilar ketiga (*"Jadikan ke yang Lain"*) pada dasarnya adalah wujud arsitektur **Retrieval-Augmented Generation (RAG)** yang berakar kuat pada cabang ilmu **Information Extraction (IE)**. 

Berdasarkan tinjauan literatur ilmiah (Lewis et al., 2020 dalam *"Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks"*), sebuah sistem tidak diwajibkan untuk merepresentasikan cara menyusun laporan menggunakan parameter statis internal model. Sebaliknya, sistem hibrida memanfaatkan STKI (*non-parametric memory*) secara efisien untuk menjemput referensi format cetak biru/*template*, kemudian komponen DS (seperti *Transformer* terpadu atau *Pandas-based Extractor*) bertugas menyarikan data (agregasi, pemfilteran, pembagian kelompok) agar data mentah termanipulasi sesuai dengan kerangka/struktur hasil temuan STKI tersebut.

## 5. Empat Hipotesis Kerentanan Arsitektur Pilar 3 & Solusi Ilmiah

Mewujudkan ide penyatuan pilar STKI dengan DS menuntut pendekatan matematis yang tangguh. Berikut adalah 4 hipotesis kerentanan sistem jika rancangan ini diimplementasikan, beserta peta solusi yang bersandar pada landasan literatur ilmiah:

### Hipotesis 1: Kegagalan Resolusi Temu-Kembali Template (Bottleneck STKI)
* **Hipotesis**: Sistem gagal menemukan referensi *template* laporan yang tepat di *database* karena representasi *query* teks (dataset XLSX mentah) tidak memiliki *overlap* leksikal/semantik yang cukup dengan metadata struktur laporan yang ada (kesenjangan kosakata).
* **Teori Ilmiah**: Kelemahan ini dikenal sebagai fenomena *Lexical Chasm* pada ruang vektor terisolasi (Manning, Raghavan & Schütze, 2008).
* **Solusi Hibrida**: Menerapkan **Pseudo-Relevance Feedback (PRF)** melalui adaptasi **Algoritma Rocchio**. Sistem tidak mencocokkan baris per baris data ke STKI. Alih-alih, DS mengekstraksi 5 pilar nama *header* kolom utama secara statistik (menggunakan *Term Frequency*), merangkumnya menjadi kueri teks bayangan (*pseudo-query*), lalu mengumpankan kueri padat tersebut ke ruang vektor pencarian (*Dense Embedding* BERT).

### Hipotesis 2: Mismatch Tipe Data pada Translasi DS
* **Hipotesis**: Komponen klasifikasi (*DS Extractor*) akan mengalami galat matematis (*error*). Hal ini terjadi ketika STKI menemukan laporan bertema "Rata-rata IPK Mahasiswa" (yang menuntut tipe data rasio/kontinu), namun kolom dataset aslinya berisi nilai mutu berupa huruf (A, B, C) (tipe data ordinal).
* **Teori Ilmiah**: Dikenal sebagai *Data Heterogeneity and Schema Matching Error* (Rahm & Bernstein, 2001).
* **Solusi Hibrida**: Mengimplementasikan lapisan **Semantic Schema Alignment**. Sebelum transformasi bentuk dieksekusi, klasifikator menjalankan *Fuzzy C-Means Clustering* atau matriks pemetaan kamus heuristik (contoh: A = 4.0, B = 3.0) untuk mendeteksi *nature* kolom. Jika kolom gagal ditranslasikan, sistem akan melakukan *Graceful Rejection* (menolak mengubah bentuk laporan secara rapi, alih-alih meledak melempar *fatal error*).

### Hipotesis 3: Ledakan Beban Komputasi Algoritmik (O(N²) vs O(1))
* **Hipotesis**: Apabila dataset XLSX awal dari mahasiswa tersebut memiliki 50.000 baris observasi, proses mencocokkan tiap baris secara iteratif ke fungsi *template* target akan mengkonsumsi waktu komputasi yang merusak *user experience* aplikasi waktu-nyata (*latency spike*).
* **Teori Ilmiah**: Masalah kurva eksponensial kompleksitas waktu (*Big-O*) pada arsitektur pencarian *brute-force* sekuensial (Cormen et al., 2009).
* **Solusi Hibrida**: Penggunaan integrasi **Vectorized Query Execution (Cython C-Backend)** dan implementasi **Locality-Sensitive Hashing (LSH)** pada lapisan STKI. Dengan teknik vektorisasi, operasi transformasi bentuk (`df.groupby().agg()`) tidak dihitung per elemen, melainkan diparalelkan pada level aljabar matriks $\mathbf{M}^T$. Hal ini meredam lonjakan beban komputasi dari laju eksponensial $O(N \log N)$ ke konstan deterministik $O(1)$ untuk komputasi inti.

### Hipotesis 4: Halusinasi Penyajian Data Baru (AI Generative Halucination)
* **Hipotesis**: Jika pilar ketiga diotomatisasi secara gegabah menggunakan jaringan saraf tiruan penuh (*fully deep learning generator*), sistem dapat 'mengarang bebas' agregasi rata-rata IPK maupun kalkulasi mata kuliah, melenceng dari data mentah aslinya hanya demi memenuhi kerangka *template* yang terambil.
* **Teori Ilmiah**: Dikenal sebagai *Parametric Knowledge Over-reliance in Generative Models* / Masalah Fakta Sintetis Semu (Bender et al., 2021).
* **Solusi Hibrida**: Mengikat *output* dengan **Hard-Coded Rule-Based Extractor (HCRE)**. DS tidak boleh memprediksi angka. Sebaliknya, klasifikator STKI + DS hanya berwenang untuk meramalkan **skrip/fungsi matematika apa yang akan dieksekusi**. Komputasi angka sesungguhnya dikerjakan mutlak oleh fungsi aljabar murni *Python*. Kombinasi "Penalaran Semantik (STKI) + Komputasi Aljabar Deteministik (DS)" ini menggaransi kebenaran matematis $100\%$ mutlak yang tak bisa dihalusinasikan.
