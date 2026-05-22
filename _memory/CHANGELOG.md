# CHANGELOG

Semua perubahan teknis dan arsitektural yang signifikan harus dicatat di sini.

## [v4.1.0] - 2026-05-22
### Added
- Pembuatan folder `_memory/` (INDEX, DIARY, CHANGELOG) sesuai protokol ANTIGRAVITY v4.0.
- Skrip *stress-testing* OOD berbahasa Indonesia (`testing/generate_indo_real_docs.py`) untuk membangkitkan 1.000 PDF/DOCX/XLSX masif dari API Wikipedia.
- Penambahan sub-bab **Solusi Matematis & Integrasi Sistem** pada dokumen analisis Wikipedia.

### Fixed
- Implementasi *Temperature Calibration* ($T=2.0$) pada aktivasi Sigmoid di `app_gui.py` dan `app_web.py` untuk menekan bias awal prediksi kelas *default* terhadap dokumen *Out-of-Distribution* (OOD).
- Implementasi *Hybrid Retrieval Penalty* mutlak (menjadi $0.0$) pada `app_gui.py` dan `app_web.py` jika dokumen tidak mencapai ambang batas $\text{Score}_{BM25} \le 0.05$.
- Dimensi rumus di `_Fondasi/perhitungan_stki.md` dikoreksi dari $n=5$ ke $n=20$ agar selaras dengan output ONNX model.
- Kalimat contoh pada `_Fondasi/kasus_perhitungan_stki.md` diralat (*truncation 5 elemen dari 20 kelas*) untuk kohesi logika akademik.
- Sinkronisasi teori matematis OOD Penalty dan Temperature Calibration ke dalam `_Fondasi/perhitungan_stki.md`.

### Purged
- Dataset BBC berbahasa Inggris yang salah klasifikasi dihapus karena memicu kegagalan bahasa (*OOV mismatch*).
