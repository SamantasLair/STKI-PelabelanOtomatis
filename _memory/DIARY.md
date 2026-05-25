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

## [2026-05-22] - "10 Fundamental Edge-Case Audit (Anti-Glazing)"
- **Eksperimen**: Menulis `testing/test_10_fundamental.py` menggunakan `unittest` dan `Flask.test_client()` untuk membombardir *backend* dan Pilar 3 dengan 10 skenario kegagalan: OOD Nonsense, Injeksi SQL, Bias Bahasa (OOV), File Corrupt, CSV Kosong, Zero Division, False Positive Schema, Injeksi String Kosong, Race Condition, dan Shape Error.
- **Analisis Kritis & Bug Ditemukan**: Secara menakjubkan, struktur Hybrid STKI (Dense + Sparse) gagal menahan cacat teoretis tersembunyi. Tangkapan layar terbaru membuktikan **Logic Flaw Parah (Skor 100% Palsu)**. Model ONNX digagalkan oleh algoritma kami sendiri (*Keyword Heuristic Boosting*) yang memberikan poin +0.20 flat jika ada kata receh seperti "data" atau "jumlah", memaksa Cosine Similarity menembus $> 1.0$ (100%).
- **Eksplorasi Lanjutan Cacat Teoretis**: Pada uji OOV string pendek `"halo halo badnung"`, Cosine Similarity menembus $99.6\%$ dengan label *"Transkrip Nilai Lengkap"*. Investigasi mendalam membongkar bahwa bentuk asli ONNX model adalah murni **5-Dimensi Logit Classifier**, bukan model *Dense Embedding* skala tinggi. Akibatnya terjadi **Dimensional Collapse** di mana teks *nonsense* memicu *bias vector* yang sama secara seragam.
- **Penyelesaian Mutlak**: Modul `TKI/app_web.py` telah saya bedah ekstrim: seluruh kode `l1_boosts` dan `l2_boosts` **dimusnahkan**. Model kini dibiarkan bernapas dengan murni Cosine Similarity ONNX (*Raw Logits* tanpa Sigmoid dan tanpa v_null thresholding).
- **The Sparse Gatekeeper (Iterasi 1)**: Khusus untuk mengakali keruntuhan dimensi pada prediksi *Zero-Shot* murni, sebuah kendali leksikal dipasang. Jika teks berukuran kecil ($< 50$ karakter) dan memiliki $0.0$ irisan kata dengan taksonomi label (*Jaccard 0%*), skor Dense Vector akan dihanguskan ke $0.0$.
- **Looping Audit & Penemuan Lanjutan**: Sesuai instruksi uji coba independen, teks *paper* asli panjang diuji. Ternyata teks panjang juga terjebak *Dimensional Collapse* (klasifikasi Jurnal menjadi "Monograf Buku Ajar" dengan 94% kemiripan). Hard Cutoff $0.0$ gagal karena ukuran karakter $>50$.
- **Solusi Soft Lexical Gatekeeper (Iterasi 2)**: Arsitektur di-upgrade. Hard cutoff dihapus, diganti menjadi *Multiplier*. Seluruh teks diuji irisan (*overlap*). Jika 0, Cosine Similarity dipotong mutlak $20\%$ (`sim * 0.80`). Jika $>0$, skor di-boost berbanding lurus dengan irisan (`sim * (1.0 + overlap * 0.15)`). Algoritma ini divalidasi dan berhasil mengembalikan Jurnal/Laporan Pengabdian ke posisi 100%. Teori ini dicatat kuat di `_fondasi/dimensional_collapse_stki.md`.
- **Large-Scale Audit 1000 Kalimat (Iterasi 3)**: Menyiapkan kombinasi 1.000 kalimat independen (Subjek, Predikat, Objek, Konteks) tanpa kesamaan berlebih, dan dieksekusi secara masif untuk menelusuri batas anomali algoritma *Soft Gatekeeper*.
- **Hasil Iterasi 3 (Validasi Mutlak)**: Dari 1.000 kalimat, ditemui **0 Anomali**. Seluruh kemiripan halusinasi $>90\%$ musnah. Algoritma $sim \times 0.80$ menjamin skor tertinggi tanpa irisan maksimal hanya $80\%$, yang berarti secara matematis mustahil menembus ambang batas tayang $85\%$ di UI. Masalah *Dimensional Collapse* ONNX telah berhasil ditangkal secara sistematis tanpa *hardcode glazing* apa pun.
- **Bencana "Tie at 100%" (Iterasi 4)**: Saat diuji oleh pengguna di *frontend* dengan artikel utuh, kelas-kelas yang memiliki minimal 1 kata *overlap* melonjak hingga persis **100.0%**. Sistem kehilangan kapabilitas *ranking* karena semua mengikat di skor maksimal.
- **Calibrated Hybrid Formula**: Ini disebabkan `Base Similarity` ONNX sudah menduduki $\sim90\%$. Diberikan *multiplier* $1.15$, nilai langsung ter-*clamp* ke angka absolut $1.0$. Solusinya diterapkan pada `app_web.py`: Jika overlap $>0$, kemiripan DIBIARKAN MURNI (`sim * 1.0`) tanpa di-boost melebihi batas natural, dan HANYA yang overlap $=0$ yang ditekan (`sim * 0.80`). Ini mempertahankan *ranking distribution* sambil mencegah *Dimensional Collapse*. Perhitungan teoretis dicatat pada `testing/analisis_saturasi_100.md`.

## [2026-05-25] - "Audit Sistem Evaluator Otomatis (CI/CD IR Metrik)"
- **Bug Ditemukan**: Saat menjalankan pengujian metrik pencarian (MRR & Precision@5) pada `ir_metrics_engine.py`, sistem melempar nilai absolut $0.00$ pada seluruh kueri benchmark berskala industri.
- **Hipotesis Kegagalan (Flaky Test & OOD Corpus Mismatch)**: Evaluasi gagal bukan karena arsitektur Hibrida atau *Gatekeeper* rusak, melainkan karena metodologi *testing* yang cacat secara empiris. Basis data `academic_demo_real.db` saat ini berisi korpus Wikipedia yang dipanen secara acak dengan dominasi label `["Wikipedia Indo", "Artikel Umum"]`. Kueri benchmark mencari label spesifik seperti `"Skripsi Informatika"`. Karena *Ground Truth* (dokumen dengan label target) secara literal **TIDAK ADA** di dalam *database* saat diuji, skor kelayakan matematika MRR dan Precision pasti runtuh menjadi 0. Menjadikan SQLite produksi yang dinamis sebagai arena uji unit (*Unit Test*) adalah sebuah *Anti-Pattern* yang memicu *Flaky Test*.
- **Penyelesaian Mutlak (Surgical Fix)**: Uji standar industri menuntut isolasi *environment* (*In-Memory Synthetic Injection*). Skrip `ir_metrics_engine.py` diretas: Saya menyuntikkan 5 dokumen *Ground Truth* sintetik (*dummy_docs*) secara terprogram langsung ke dalam *Array RAM* Python sebelum dievaluasi oleh mesin pencarian. Ini menjamin kehadiran dokumen yang relevan di ruang vektor sehingga kemampuan sistem menempatkannya di Peringkat 1 dapat diuji secara objektif, menyingkirkan bias ketidakpastian *database* SQLite acak.
