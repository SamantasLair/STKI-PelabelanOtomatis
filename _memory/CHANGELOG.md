# CHANGELOG

Semua perubahan teknis dan arsitektural yang signifikan harus dicatat di sini.
## [v4.5.1] - 2026-05-27
### Added
- **Interactive Data Pipeline Graph**: Merombak total laman `_UIUX/ds/index.html` dengan grafik alur kerja interaktif (*nodes & edges*). Grafik berfungsi sebagai alat navigasi dinamis; mengklik node tertentu (seperti *Data Source* atau *K-Means Engine*) akan memunculkan panel fungsionalitas yang sesuai. Efek animasi *marching ants* (`@keyframes flow`) diaktifkan saat proses generasi taksonomi berjalan untuk indikasi *real-time*.
- **Database Explorer Accordion**: Mengimplementasikan endpoint `GET /api/documents` untuk memuat data dari *database* aktif (dibatasi 500 dokumen untuk performa) pada laman Data Science. Antarmuka menggunakan desain *Accordion* murni via CSS, memungkinkan peninjauan isi dokumen (*full-text*) secara ringkas tanpa merusak tabel.
- **File-Based Recommendation Engine (STKI)**: Menambah kapabilitas unggah dokumen (`.pdf`, `.docx`, `.csv`, `.xlsx`) menggunakan pola antarmuka *Drag & Drop* ke tab "Rekomendasi Terkait" di sisi pengguna. Sistem otomatis mengekstrak vektor semantik dari file (*file-to-text-to-vector*) lalu mencocokkannya ke database untuk melakukan *Information Retrieval* murni tanpa memerlukan input teks manual.

## [v4.5.0] - 2026-05-27
### Added
- **UIUX Bifurcation**: Memecah arsitektur frontend web secara fisik menjadi dua modul terpisah, `/stki` (Ruang Pencarian End-User) dan `/ds` (Ruang Komando Data Science). Mencegah *spaghetti UI* dan menyediakan laman terdedikasi untuk integrasi alat peneliti tingkat lanjut (*Google Looker Studio*).
- **Unsupervised Dynamic Taxonomy**: Menghapus seluruh sistem label *hardcoded*. Sistem kini menggunakan algoritma **K-Means Clustering** terhadap *dense embeddings* (384D) seluruh dokumen di *database*, dipadukan dengan **TF-IDF** (*Term Frequency-Inverse Document Frequency*) untuk mengekstrak kata kunci dan menciptakan "Nama Label" secara otomatis dan murni *data-driven*.
- **Otomasi Jumlah Kelompok (Rice Rule)**: Pengelompokan K-Means secara dinamis menentukan jumlah target klaster berdasarkan metrik jumlah dokumen aktual menggunakan rumus $X = \lceil 2 \cdot N^{1/3} \rceil$.
- **Seamless Document Ingestion**: Membangun modul "Unggah Arsip" (Ingesti) di ruang `/stki` yang langsung membaca file (PDF/Docx/CSV/TXT), mengekstrak teks, menembak model ONNX, memprediksi klasifikasi berdasarkan taksonomi dinamis, lalu langsung melakukan `INSERT` ke SQLite secara *real-time*.

## [v4.4.0] - 2026-05-27
### Added
- **Arsitektur Frontend MVVM**: Membangun ulang seluruh arsitektur *frontend* web dari struktur statis monolitik menjadi pola *Model-View-ViewModel (MVVM)* menggunakan Vanilla Javascript di dalam ruang inkubasi baru `_UIUX/`. Perubahan ini memisahkan secara ketat modul `models` (API Fetch), `views` (Manipulasi DOM), dan `viewmodels` (Logika Penengah), mencegah *spaghetti code*.
- **Desain UI Pembukuan (Ledger Theme)**: Merombak antarmuka pengguna menjadi gaya dokumen resmi/pembukuan. Desain mengadopsi palet warna kertas (*off-white/cream*), border garis tegas, tanpa elemen *glow/shadow* berlebihan, dan eliminasi total seluruh Emoji demi estetika akademik murni.
- **Show, Don't Tell Telemetry**: Menanamkan baris telemetri metrik *real-time* (seperti Latensi Pencarian, Target Rice Rule, Kalkulasi Dimensi, Rasio Hybrid) secara implisit dan langsung ke dalam layar hasil (*ledger rows*). Hal ini menggantikan teks deskriptif panjang yang sebelumnya digunakan untuk mendemonstrasikan keunggulan sistem.
- **Flask Routing Integration**: Mengarahkan modul *backend* `app_web.py` dan skrip `restart_server.bat` untuk secara langsung menyajikan `_UIUX/` sebagai folder templat dan aset statis utamanya, meresmikan transisi dari UI lama ke desain Pembukuan (*Ledger Theme*).

## [v4.3.0] - 2026-05-27
### Added
- **12 Scientific QA Metrics**: Menambahkan total 12 *Quality Assurance Tests* (6 untuk Sistem, 6 untuk Model) berbasis teori *Information Retrieval* dan *NLP* yang valid (Manning, Baeza-Yates, Ethayarajh, dll) ke dalam skrip evaluasi (referensi teori lengkap di [[teori_qa_metrics]]).
- **Teori QA Metrik**: Mencatat seluruh referensi ilmiah, jurnal, dan rumus kalkulasi metrik seperti *MRR, MAP, Latency, NDCG, Anisotropy, OOV Robustness, Polysemy* ke dalam [[teori_qa_metrics]] (hubungkan dengan [[METRICS_THEORY]]).

### Changed
- **Download Real Docs**: Mengubah target unduhan pada `download_real_docs.py` menjadi benar-benar representatif (4 format file merata: PDF, DOCX, CSV, XLSX) dengan jaminan file asli bertekstur penuh (*full-text*, bukan sekadar abstrak) dan masing-masing wajib berukuran di bawah 1MB untuk menghindari potensi *bottleneck* RAM.

### Fixed
- **Testing Logic Correction (Dimension Mismatch)**: Memperbaiki *bug* krusial (`ValueError: shapes (384,) and (5,) not aligned`) pada `ir_metrics_engine.py` yang menggagalkan eksekusi evaluasi multi-domain. *Bug* dipicu oleh keberadaan residu *dummy embeddings* (berdimensi 5) pada pangkalan data tertentu. Solusi yang diimplementasikan adalah *on-the-fly embedding recalculation* (melakukan inferensi ulang *real-time* ke ukuran 384 dimensi) pada saat proses pengujian jika mendeteksi dimensi yang salah, sehingga evaluasi sistem dapat diselesaikan dengan 100% *pass rate*.
- **Dimensional Collapse (Semantic Anisotropy)**: Menyelesaikan *bug* kritis pada model lama (`indobert-mini`) yang memicu Anisotropy ekstrim (kemiripan "struktur data" dan "sayur bayam" $\approx 93\%$, lihat analisis di [[dimensional_collapse_stki]]). Masalah diselesaikan dengan menginjeksikan skrip `export_sota_model.py` yang mengekstrak `paraphrase-multilingual-MiniLM-L12-v2` lengkap dengan *Mean Pooling* murni secara langsung ke format `.onnx`. Evaluasi membuktikan Anisotropy hancur total, dan *contextual polysemy* kembali sehat. Alur lengkap lihat [[PRESENTASI_SISTEM_STKI]].


### Removed
- **Pembuangan Skrip Usang (Cleanup)**: Membersihkan dan menghapus skrip pembangkit sintesis (`generate_indo_real_docs.py`, `generate_presentation_docs.py`, `seed_domain_dbs.py`, `massive_pump.py`) serta skrip evaluasi purba/legacy untuk membebaskan repositori dari penumpukan (*Tech Debt*).

## [v4.2.1] - 2026-05-26
### Fixed
- **Testing Logic Correction**: Memperbaiki asersi logika pada `test_10_logic_flaws.py` (`test_09_null_vector_collapse`) yang sebelumnya gagal karena salah mengasumsikan ketiadaan penanganan teks kosong. Asersi diubah untuk memvalidasi *error message* (`'Konten teks kosong'`) yang secara fungsional ditangkap dan dikembalikan oleh Flask dengan benar.
- **Race Condition Testing**: Menganalisis dan menyimpulkan *sqlite3.OperationalError: database is locked* pada saat *testing* diakibatkan oleh eksekusi paralel ganda (Race Condition saat `async_relabel_task` mengunci *database*), sehingga pengujian dire-eksekusi secara linear dan *pass* 100%.

### Changed
- **Documentation Update**: Memperbarui spesifikasi teknis pada [[spesifikasi_teknis]] untuk menghilangkan referensi statis pada `indobert-mini`/`bert-mini` dan menggantinya dengan dokumen landasan teoretis untuk model *State-of-the-Art* terbaru, yaitu `paraphrase-multilingual-MiniLM-L12-v2`. Hub terkait ada di [[INDEX]].

## [v4.2.0] - 2026-05-24
### Added
- **Multi-Domain Database Architect**: Mengganti dua tombol statis (*Utama* & *Demo Real*) pada antarmuka pengguna (`index.html`) menjadi sebuah *Dropdown Menu* yang secara otomatis melayani 6 cabang korpus independen (Akademik, Politik, Ekonomi, Peraturan Bisnis, Peraturan Etika, Demo Real Dataset). Sistem akan melakukan instansiasi file `.db` dan taksonomi yang berbeda secara dinamis.
- **Injeksi Corpus Sintetis (Auto-Seeding)**: Menciptakan skrip `testing/seed_domain_dbs.py` yang berhasil menyuntikkan puluhan dokumen proksimal lengkap dengan vektor leksikalnya langsung ke dalam *database* Politik, Ekonomi, Bisnis, dan Etika. Ini memungkinkan GUI bisa langsung diuji coba.
- **Transisi ke Skala Enterprise (Full-Text Retrieval)**: Menghapus batas artifisial (`content[:1000]`) pada naskah *seeding* Wikipedia Indonesia (`insert_and_test_indo.py`). Sistem kini secara agresif menyimpan teks asli sepenuhnya (*Full-Text*, ~15.000 kata per dokumen) alih-alih abstrak dangkal. Ini disokong oleh pertahanan ganda: *SQL Pre-Filtering* (anti-OOM) dan *TextRank* (anti-token truncation BERT). Bukti matematis didokumentasikan pada `_Fondasi/kepadatan_semantik_full_text.md`.
- **Massive Scale Ingestion (24.000 Dokumen)**: Melakukan pompa masif (*Massive Data Pump*) dengan menciptakan dan mengeksekusi `_Quality_Assurance/testing/massive_pump.py`. Skrip ini menyuntikkan 4.000 dokumen khusus/relevan (diambil secara dinamis dari API Wikipedia) ke masing-masing 6 pangkalan data (total 24.000 dokumen).
- **Multi-Domain IR Metrics Engine**: Menulis ulang sistem evaluasi mandiri `ir_metrics_engine.py` untuk bermanuver dan mengevaluasi 6 pangkalan data secara asinkronus (Loop Metrics). Pengujian dilakukan dengan memutar 300 sampel teks asli per-domain dan memberikan target taksonomi unik per kueri. MRR Akhir diuji pada angka stabil 0.9167. Bukti analitis tercatat di `_Fondasi/evaluasi_multi_domain.md`.
- **NDCG & Semantic Robustness Update (Sentence-Transformers)**: Sistem dievaluasi menggunakan skenario Typo/Sinonim (Test #2) via `ndcg_robustness_engine.py` yang menyingkap kelemahan komprehensi `indobert-mini`. Menyelesaikan limitasi ini dengan membuang `indobert-mini` dan menggantinya dengan model kelas berat `paraphrase-multilingual-MiniLM-L12-v2` (State-of-the-Art Semantic Model). Mengubah arsitektur Notebook (`DS/Sistem_Temu_Kembali_Informasi.ipynb`) untuk mengekspor murni `last_hidden_state` dan menanamkan algoritma *Mean Pooling* pada `app_web.py` demi mengekstrak representasi vektor makna sejati (384-Dimensi).
- **Teori Skalabilitas Baru**: Pembuatan dokumen `_Fondasi/skalabilitas_database_stki.md` yang merincikan solusi matematika untuk *Memory Shrinkage* dan penanganan *OOM Killer*.
- **Endpoint Pagination API**: Pembuatan endpoint khusus `/api/recommend` di `app_web.py` yang mendukung parameter `limit` dan `offset` untuk partisi data.

### Fixed
- **Pemusnahan Ancaman OOM (Out-of-Memory)**: Mencabut klausa statis `LIMIT 2500` pada `/api/search` `app_web.py`. Menggantinya dengan **SQL Dynamic Pre-Filtering** (`LIKE`) berdasarkan irisan kata kueri. Hal ini mencegah ekstraksi ribuan vektor ke RAM (*Python Heap*) untuk dokumen yang secara matematis tidak mungkin mendapat skor BM25 > 0.
- **Penyembuhan Frontend Lag**: Memindahkan logika *Grid-2-Col file partitioning* (pemisahan `.csv` dan `.pdf`) dari skrip klien `main.js` ke pemrosesan *Server-Side* di `/api/recommend` `app_web.py`. Ini memangkas Payload JSON yang tidak relevan.
- **Stop-Word Penalty pada Gatekeeper**: Mengganti perhitungan `overlap` mentah dengan sistem bobot pseudo-IDF. Kata hubung (*stop-words*) seperti "dan", "atau", "di" kini dipenalti menjadi bobot $0.05$ alih-alih $1.0$, mencegah bias *similarity* dokumen sampah yang hanya memiliki kesamaan preposisi.
- **Sinkronisasi Total Arsitektur GUI (`app_gui.py`)**: Melakukan perombakan *surgikal* pada modul GUI desktop untuk menyelaraskannya dengan Data Science dan backend web (`app_web.py`).
  - Menghapus ekstraksi sentimen *v_null* dan aktivasi Sigmoid *Temperatur Kalibrasi*.
  - Mengimplementasikan ekstraksi vektor *Mean Pooling* (384-D) yang valid untuk model *MiniLM*.
  - Memusnahkan aturan heuristik kuno (`l1_boosts` dan `l2_boosts`) dan menggantinya dengan logika **Soft Lexical Gatekeeper**.
- **Koreksi Threshold Klasifikasi Multi-Layer**: Memperbaiki logika peredaman (*clipping*) pada skor akhir di `app_web.py` dan `app_gui.py`. Ambang batas pengakuan label dipulihkan dari `0.85` menjadi nilai aslinya sesuai `rencana_implementasi.md` (30% untuk Domain L1 dan 35% untuk Detail L2), memastikan model tidak terlalu konservatif atau pun membuang kemiripan yang valid.

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

### Fixed
- **PyTorch JIT vs Transformers v4.46+ Tracing Bug**: Memperbaiki kegagalan ekspor ONNX pada `BertModel` (MiniLM) di `DS/generate_notebook.py` yang ditandai dengan *Silent Crash (OOM)* dan error beruntun (`multiple values for 'use_cache'`, `tuple index out of range`, serta `sdpa_mask dimension extraction failure`). 
  - **Surgical Solution 1**: Mengimplementasikan `ONNXExportWrapper` dengan `return_dict=False` dan *keyword argument mapping* (kwargs) paksa untuk menstabilkan struktur parameter *forward pass*.
  - **Surgical Solution 2**: Menginjeksi *Runtime Monkey-Patch* pada fungsi internal `_create_attention_masks` milik model sebelum *tracing*. Ini secara paksa me-*bypass* implementasi *Scaled Dot Product Attention* (SDPA) dan mengembalikan masker atensi 4D tradisional (`[batch_size, 1, 1, seq_length]`) yang 100% didukung oleh ONNX C++ *backend*.
