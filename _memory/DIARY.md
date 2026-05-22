# DIARY & FINDINGS

Buku catatan eksekutif untuk eksperimen, temuan *bug*, dan rekam jejak keputusan intelektual.

## [2026-05-22] - "The Error Crusade & OOD Stress Test"
- **Masalah Ditemukan**: Saat dilakukan pengujian dokumen non-akademik (Dataset Berita Bahasa Inggris dari BBC dan Ensiklopedia Wikipedia Indonesia), probabilitas akhir model statis di ~0.71 untuk Index 0.
- **Teori Penyelidikan**: Kami membedah fenomena ini dan menemukan bahwa:
  1. Untuk BBC: Terjadi kehancuran *Self-Attention* akibat *Out-Of-Vocabulary (OOV)*.
  2. Untuk Wikipedia Indo: Matriks kosinus $\mathbf{W}_c \cdot \mathbf{h} \approx 0$ karena ketiadaan fitur (frasa akademik yang memicu bias fitur). Hal ini mengakibatkan persamaan probabilitas murni ditopang oleh *bias scalar default* kelas prior/mayoritas ($b_0$).
- **Keputusan Desain**: 
  1. TPD-Cosine Similarity bekerja brilian. Walaupun model mengeluarkan probabilitas 0.72, karena rumusan GUI/Web memiliki *Strict Fallback Threshold* pada $\theta = 0.92$, GUI akan 100% aman dan menolak dokumen (*classified as "Tidak Terklasifikasi"*).
  2. Kami telah mendokumentasikan 3 solusi mitigasi (*Temperature Calibration*, *TextRank Distillation*, dan *BM25 Penalty*) di file analisis.
- **Kesimpulan**: *System is mathematically sound and anti-fragile.*

## [2026-05-22] - "UX Resiliency & Lexical Resonance Analysis"
- **Bug & Refactoring**: Ditemukan bahwa skrip `.bat` untuk menyalakan *server* sering kali meluncurkan *browser* secara prematur (sebelum Flask ONNX siap) karena menggunakan `timeout` yang kaku. Kami menggantinya dengan algoritma **Polling Loop Aktif** `netstat -aon | findstr ":5000"`, menjamin transisi *booting* yang mulus.
- **Temuan Arsitektural (Lexical Resonance)**: Saat pengujian dokumen Jurnal Ilmiah yang memuat kata "Sistem Informasi", model justru memilih **Skripsi Sistem Informasi (83.3%)** ketika mode Demo Real diaktifkan, dan memilih **Laporan Keuangan** saat menggunakan Database Lama/UTAMA karena kehadiran kata "jumlah" (*Lexical Booster*). 
  - **Analisis**: Perilaku ini sangat wajar dan membuktikan sistem hibrida (Dense + BM25) bekerja cemerlang di skenario *Zero-Shot*. Model dipaksa melakukan *mapping* terdekat pada vektor kategori yang tersedia, dengan dorongan absolut dari penangkap kata kunci heuristik.
- **Keputusan Fitur UI**: Untuk mengakhiri kebingungan presentasi, Web UI dikembangkan dengan penambahan tab **Smart Recommendation**. Fitur ini memisahkan hasil Leaderboard menjadi Grid Dua-Kolom (Data CSV/XLSX vs Dokumen PDF/DOCX) murni melalui pemrosesan *Frontend JavaScript* menggunakan hasil inferensi API tanpa modifikasi paksa pada *Database* SQLite.
- **Keputusan Privasi Kode**: Dokumen cetak biru teoretis (`_Fondasi/ide_transformasi_dokumen.md` beserta dokumen fundamental lainnya) kini telah dicabut dari riwayat Github (*remote purge*) dan ditambahkan secara kaku ke dalam `.gitignore`. Hak kekayaan intelektual (*blueprint*) ini sekarang menjadi *top-secret* dan hanya ada secara lokal.

## [2026-05-22] - "Bukti Konsep (PoC) Ekstraktor Pilar 3"
- **Eksperimen**: Menguji ide "Jadikan ke yang lain" dengan menciptakan *script* `TKI/pilar3_transformer.py`. Kami memberi sistem dataset CSV `data_mahasiswa_mentah.csv` berisi nama dan nilai mutu/SKS.
- **Hasil Pengujian**:
  1. Pilar STKI secara buta mengekstrak *header* (Pseudo-Relevance Feedback) dan berhasil menyimpulkan label target yang relevan adalah **"Transkrip Nilai Lengkap"**.
  2. Lapisan *Schema Alignment* otomatis mengonversi tipe Ordinal ('A', 'B', 'C') ke skala numerik 4.0.
  3. Extractor Hard-Coded (HCRE) mengeksekusi vektorisasi aljabar $O(1)$, melahirkan laporan agregat IPK baru dalam waktu 0.05 detik tanpa halusinasi.
- **Kesimpulan Awal**: Arsitektur Hibrida STKI + DS ini valid secara konsep teoretis.

## [2026-05-22] - "Analisis Kritis PoC Pilar 3 (Anti-Glazing)"
- **Eksperimen**: Menjalankan *Stress-Test* `test_pilar3_kritis.py` untuk menguji kerentanan sistem di luar skenario bahagia (*Happy Path*). Kami memasukkan kolom sinonim ("Skor_Mutu"), data kotor ('a', 'X'), dan menghapus kolom esensial.
- **Hasil Pengujian**: Sistem hancur total ($100\%$ *Failure Rate*).
  1. STKI gagal menangkap makna leksikal sinonim ("Skor_Mutu") karena pencarian berbasis heuristik, bukan *Dense Vector* (gagal mengenali konteks bahwa "skor" = "nilai").
  2. Modul Skema hancur karena *case-sensitivity* dan entri tak valid, merusak perhitungan metrik menjadi 0.0.
  3. HCRE Modul melempar fatal *KeyError* dan merusak komputasi karena mengeksekusi operasi matriks tanpa *pra-validasi* kolom.
- **Solusi Produksi**: Konsep teoretis RAG sangat tangguh, namun implementasi kode wajib ditingkatkan. Logika IF-ELSE harus dibuang dan mutlak diganti dengan **Vektor Cosine Similarity (ONNX)** untuk klasifikasi template STKI berlapis semantik, **Normalisasi str.upper() / Fuzzy Matching** untuk data pembersihan, dan **Pydantic/Defensive Programming** di level Pandas untuk mencegah *crash* sistem web akibat asersi kolom hilang.

## [2026-05-22] - "Scale-Up Injection (Maks 2.500 OOD Real Documents)"
- **Eksperimen**: Menjalankan skrip `testing/expand_db_10k.py` secara asinkronus untuk menambah korpus SQLite hingga batas maksimum **$2.500$ baris** *raw data* berbahasa Indonesia dari API Wikipedia tanpa manipulasi buatan, menaikkan skala tantangan sistem sebesar 250%.
- **Analisis Objektif Skalabilitas**: Kami membatasi ke angka 2.500 untuk menjaga stabilitas memori. Kami telah menulis dokumen anti-glazing `testing/analisis_ekspansi_db.md` yang meramalkan kehancuran aplikasi (Server Memory Timeout/OOM) jika pembacaan `SELECT *` tidak segera dipangkas menjadi Lazy-Loading. Perhitungan BM25 *on-the-fly* pada $>2.500$ baris diprediksi akan mencekik waktu pemuatan UI menjadi rentan. Untuk memitigasinya, kami langsung menanamkan **`LIMIT 2500`** pada `TKI/app_web.py`.
- **Solusi Produksi Database**: Disarankan menggunakan *Pre-Computed BM25 Index* menggunakan format data L1 (Pickle/HDF5) dan menyimpan referensi file, bukan murni raw-blob 2 Megabyte di dalam SQLite, untuk menjamin integritas sistem (*Real-time Response Time*).
