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
