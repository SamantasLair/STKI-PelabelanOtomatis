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
