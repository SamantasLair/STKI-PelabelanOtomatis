# CHANGELOG

Semua perubahan teknis dan arsitektural yang signifikan harus dicatat di sini.

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
- Perbaikan Cacat Logika *False Positive* Fuzzy Pilar 3: Memasang konstrain negatif (`nama`, `agama`, `darah`) pada detektor kolom nilai agar algoritma tidak merampas kolom identitas berisikan huruf ordinal.
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
