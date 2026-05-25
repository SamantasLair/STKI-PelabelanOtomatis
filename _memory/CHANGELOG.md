# CHANGELOG

Semua perubahan teknis dan arsitektural yang signifikan harus dicatat di sini.

## [v4.2.0] - 2026-05-24
### Added
- **Multi-Domain Database Architect**: Mengganti dua tombol statis (*Utama* & *Demo Real*) pada antarmuka pengguna (`index.html`) menjadi sebuah *Dropdown Menu* yang secara otomatis melayani 6 cabang korpus independen (Akademik, Politik, Ekonomi, Peraturan Bisnis, Peraturan Etika, Demo Real Dataset). Sistem akan melakukan instansiasi file `.db` dan taksonomi yang berbeda secara dinamis.
- **Injeksi Corpus Sintetis (Auto-Seeding)**: Menciptakan skrip `testing/seed_domain_dbs.py` yang berhasil menyuntikkan puluhan dokumen proksimal lengkap dengan vektor leksikalnya langsung ke dalam *database* Politik, Ekonomi, Bisnis, dan Etika. Ini memungkinkan GUI bisa langsung diuji coba.
- **Transisi ke Skala Enterprise (Full-Text Retrieval)**: Menghapus batas artifisial (`content[:1000]`) pada naskah *seeding* Wikipedia Indonesia (`insert_and_test_indo.py`). Sistem kini secara agresif menyimpan teks asli sepenuhnya (*Full-Text*, ~15.000 kata per dokumen) alih-alih abstrak dangkal. Ini disokong oleh pertahanan ganda: *SQL Pre-Filtering* (anti-OOM) dan *TextRank* (anti-token truncation BERT). Bukti matematis didokumentasikan pada `_Fondasi/kepadatan_semantik_full_text.md`.
- **Massive Scale Ingestion (24.000 Dokumen)**: Melakukan pompa masif (*Massive Data Pump*) dengan menciptakan dan mengeksekusi `_Quality_Assurance/testing/massive_pump.py`. Skrip ini menyuntikkan 4.000 dokumen khusus/relevan (diambil secara dinamis dari API Wikipedia) ke masing-masing 6 pangkalan data (total 24.000 dokumen).
- **Teori Skalabilitas Baru**: Pembuatan dokumen `_Fondasi/skalabilitas_database_stki.md` yang merincikan solusi matematika untuk *Memory Shrinkage* dan penanganan *OOM Killer*.
- **Endpoint Pagination API**: Pembuatan endpoint khusus `/api/recommend` di `app_web.py` yang mendukung parameter `limit` dan `offset` untuk partisi data.

### Fixed
- **Pemusnahan Ancaman OOM (Out-of-Memory)**: Mencabut klausa statis `LIMIT 2500` pada `/api/search` `app_web.py`. Menggantinya dengan **SQL Dynamic Pre-Filtering** (`LIKE`) berdasarkan irisan kata kueri. Hal ini mencegah ekstraksi ribuan vektor ke RAM (*Python Heap*) untuk dokumen yang secara matematis tidak mungkin mendapat skor BM25 > 0.
- **Penyembuhan Frontend Lag**: Memindahkan logika *Grid-2-Col file partitioning* (pemisahan `.csv` dan `.pdf`) dari skrip klien `main.js` ke pemrosesan *Server-Side* di `/api/recommend` `app_web.py`. Ini memangkas Payload JSON yang tidak relevan.
- **Stop-Word Penalty pada Gatekeeper**: Mengganti perhitungan `overlap` mentah dengan sistem bobot pseudo-IDF. Kata hubung (*stop-words*) seperti "dan", "atau", "di" kini dipenalti menjadi bobot $0.05$ alih-alih $1.0$, mencegah bias *similarity* dokumen sampah yang hanya memiliki kesamaan preposisi.

## [v4.1.0] - 2026-05-22
### Added
- Pembuatan folder `_memory/` (INDEX, DIARY, CHANGELOG) sesuai protokol ANTIGRAVITY v4.0.
- Skrip *stress-testing* OOD berbahasa Indonesia (`testing/generate_indo_real_docs.py`) untuk membangkitkan 1.000 PDF/DOCX/XLSX masif dari API Wikipedia.
- Penambahan sub-bab **Solusi Matematis & Integrasi Sistem** pada dokumen analisis Wikipedia.
- Penambahan menu/tab UI **Smart Recommendation Engine** di `index.html` dan `main.js`. Menggunakan pola *Grid-2-Col* yang secara mulus memisahkan (*filter*) rekomendasi berformat Data (CSV/XLSX) dan Dokumen Literatur Akademik (PDF/DOCX) menggunakan pengolahan di sisi *frontend Javascript*.
- Penciptaan `TKI/pilar3_transformer.py` dan `testing/data_mahasiswa_mentah.csv` sebagai pembuktian konsep (PoC) arsitektur RAG Hibrida (STKI + DS), yang memvalidasi suksesnya 4 hipotesis kelemahan sistem.
- Skrip ekspansi asinkronus `testing/expand_db_10k.py` diubah targetnya untuk menginjeksi batas keras maksimal **2.500** raw data asli Wikipedia berbahasa Indonesia ke dalam SQLite.
- Laporan Analisis Kritis (Anti-Glazing) kelemahan PoC Pilar 3 (`testing/analisis_kritis_pilar3.md`) dan peringatan ancaman skalabilitas DB masif 2.500+ dokumen (`testing/analisis_ekspansi_db.md`).
- Implementasi 10 Uji Fundamental Ekstrem (*Edge Cases*) pada `testing/test_10_fundamental.py` dan dokumentasi audit arsitektur di `testing/analisis_10_fundamental.md`.

### Fixed
- Pencegahan Anomali *Dimensional Collapse*: Menyelesaikan kasus teoretis di mana teks OOV mendapatkan Cosine Similarity 99% dengan label klasifikasi. Ini disebabkan oleh ruang keluaran model yang hanya berdimensi 5.
- **Penyelesaian Mutlak**: Modul `TKI/app_web.py` telah saya bedah ekstrim: seluruh kode `l1_boosts` dan `l2_boosts` **dimusnahkan**. Model kini dibiarkan bernapas dengan murni Cosine Similarity ONNX (*Raw Logits* tanpa Sigmoid dan tanpa v_null thresholding).
- **The Sparse Gatekeeper (Hard Penalty -> Soft Lexical Gatekeeper)**: Awalnya dipasang proteksi $0.0$ untuk dokumen $<50$ karakter. Namun, pada iterasi Looping Audit, ditemukan bahwa *Dimensional Collapse* juga terjadi pada dokumen tebal ($> 1000$ karakter) seperti teks Jurnal Ilmiah yang malah dideteksi sebagai "Monograf Buku Ajar". Oleh karena itu, arsitektur diubah menjadi **Soft Lexical Gatekeeper** yang berjalan untuk semua dokumen: Jika tidak ada irisan leksikal, skor Dense dipenalti ($sim \times 0.80$), sedangkan jika ada irisan, skor di-boost secara natural ($sim \times (1.0 + overlap \times 0.15)$). Hal ini terbukti matematis menyelesaikan kasus salah prediksi pada teks panjang. Penjelasan arsitektur dicatat di `_fondasi/dimensional_collapse_stki.md`.
- **Perbaikan "Score Saturation" (Tie at 100%)**: Penambahan *Lexical Boost* (multiplier $1.15$) dicabut dari `app_web.py` karena memicu nilai mentok (saturasi) ke $100\%$ secara seragam pada semua kandidat yang memiliki minimal 1 irisan kata (*overlap*). Kode diperbarui ke *Calibrated Hybrid Formula* di mana *Base Cosine Similarity* dipertahankan secara murni ($sim \times 1.0$) bagi yang memiliki *overlap* $>0$, dan ditekuk mutlak ke bawah ambang batas tayang ($\times 0.80$) bagi yang tidak memilikinya. Ini memulihkan kemampuan *ranking* natural dari model.
- Pemusnahan *Heuristic Keyword Boosting*: Menghapus algoritma `l1_boosts` dan `l2_boosts` (+0.20 flat rate) di `app_web.py` yang terbukti secara matematis merusak distribusi probabilitas.
- Perbaikan *FutureWarning* Pandas: Menambahkan argumen `include_groups=False` pada metode `apply` dalam perhitungan IPK Kumulatif di `pilar3_transformer.py`.
- Pencegahan Memori *Server Crash* (OOM): Menanamkan klausul *Hard Limit* `LIMIT 2500` pada kueri `SELECT *` di backend `app_web.py` `/api/search` untuk memblokir pembacaan *blob* SQLite tanpa batas dan menyelamatkan stabilitas komputasi *on-the-fly* BM25.
- Implementasi *Temperature Calibration* ($T=2.0$) pada aktivasi Sigmoid di `app_web.py` untuk menekan bias awal prediksi kelas *default* terhadap dokumen *Out-of-Distribution* (OOD).
- Implementasi *Hybrid Retrieval Penalty* mutlak (menjadi $0.0$) pada `app_gui.py` dan `app_web.py` jika dokumen tidak mencapai ambang batas $\text{Score}_{BM25} \le 0.05$.
- Dimensi rumus di `_Fondasi/perhitungan_stki.md` dikoreksi dari $n=5$ ke $n=20$ agar selaras dengan output ONNX model.
- Kalimat contoh pada `_Fondasi/kasus_perhitungan_stki.md` diralat (*truncation 5 elemen dari 20 kelas*) untuk kohesi logika akademik.
- Sinkronisasi teori matematis OOD Penalty dan Temperature Calibration ke dalam `_Fondasi/perhitungan_stki.md`.
- Refaktorisasi `restart_server.bat`. Mengganti statik `timeout` menjadi *Active Polling Loop* dengan `netstat` untuk mendeteksi kesiapan *port* 5000 (*Flask/ONNX boot-up*) sebelum membuka browser, mencegah *error connection refused*.
- Transformasi `TKI/pilar3_transformer.py` dari PoC ke tingkat *Production-Ready*: Mengganti Hardcoded Rule dengan Inferensi Vektor ONNX murni, Filter Schema *Case-Insensitive*, dan lapisan pelindung *Graceful Exit* Pandas.

### Purged
- Folder `_Fondasi/` telah dihapus dari pelacakan repositori Github secara *remote* melalui `git rm -r --cached` dan dimasukkan ke dalam `.gitignore` sesuai instruksi. Repositori Github sekarang hanya diisi oleh implementasi sistem (TKI, STKI, DS, memory), sedangkan teori dirahasiakan secara lokal.
- Dataset BBC berbahasa Inggris yang salah klasifikasi dihapus karena memicu kegagalan bahasa (*OOV mismatch*).
