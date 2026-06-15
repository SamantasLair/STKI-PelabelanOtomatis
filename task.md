# TASK TRACKER

## [TIER 1] JARAK DEKAT (FOKUS SAAT INI)
- [x] BUAT_PANDUAN_PASAL_ID: Membuat dokumen operasional tim (`PANDUAN_INGEST_API_PASAL.md`).
- [x] BUAT_PIPELINE_POSTGRES_MENTAH: Membuat skrip Python khusus (`ETL_HAKI/ingest_raw_postgres.py`) untuk menyimpan file unduhan API (`.json`) ke PostgreSQL secara utuh (*unprocessed JSONB*).
- [x] PEMBERSIHAN_ROOT: Memindahkan semua file `.md`, `.py`, `.log`, dan dokumen sisa dari root direktori ke `_Dokumentasi`, `_Scripts`, dan `_Logs`.
- [x] PENGHAPUSAN_GIT_TRACKING: Menghapus pelacakan Git (GitHub/HF Space) dari file-file internal tersebut via update `.gitignore` dan eksekusi `git rm -r --cached`.

## [TIER 2] PENTING (STRATEGI UTAMA)
- [/] PROSES_DATA_HAKI: Unduh dan simpan data hukum dari REST API Pasal.id (Skrip ingest_pasal.py siap, menunggu eksekusi User).
- [x] RISET_API_HAKI: Platform pasal.id dipilih sebagai sumber data valid. Web scraping dibatalkan.
- [x] GENERASI_DOKUMEN_PRESENTASI: Direktori _Presentasi/ beserta struktur L1-L2-L3 selesai dibuat.
- [/] INTEGRASI_DATA_HAKI: Eksekusi Ingesti Data ke dalam PostgreSQL via `ingest_raw_postgres.py` menunggu otorisasi User (Database URL dihubungkan ke Supabase).

## [TIER 3] UMUM & REPEATABLE (RUTINITAS)
- [ ] CEK_TAMPILAN_UI: Pastikan desain warna dan animasi tombol tetap berjalan normal tanpa gangguan visual.
- [ ] CEK_LOGIKA_PENCARIAN: Tes sistem pencarian untuk memastikan akurasi data dan tidak ada pesan error.
- [ ] CEK_KECEPATAN_SISTEM: Pastikan pencarian dan perpindahan halaman tetap instan tanpa loading lambat.
- [ ] CEK_BATAS_KLASIFIKASI: Tinjau ulang angka akurasi penamaan otomatis jika mulai meleset.
