# PROJECT INDEX (STATE MAP)

## 1. Arsitektur Proyek
- **TKI/ & STKI/**: Sistem utama (Flask Web/GUI Desktop) hibrida (Dense BERT + BM25 Sparse). Alur arsitektur lengkap didokumentasikan di [[PRESENTASI_SISTEM_STKI]].
  - Web UI mencakup 4 fitur utama: **Leaderboard Search**, **Batch Classifier**, **Taxonomy Editor**, dan **Smart Recommendation Engine**.
- **_UIUX/**: Direktori eksperimental (*inkubasi*) untuk *frontend* bergaya Pembukuan/Ledger dengan arsitektur MVVM (Model-View-ViewModel) Vanilla JS yang modular.
- **DS/**: Ruang Data Science (Notebook MLOps & eksperimen). Spesifikasi teknis berada di [[spesifikasi_teknis]].
- **_Fondasi/**: Dokumentasi landasan teori, rumus matematika, metodologi pelatihan, dan standar QA Metrik ([[teori_qa_metrics]]). Rujukan dimensional collapse ada di [[dimensional_collapse_stki]].
- **_Quality_Assurance/**: Mesin evaluasi cerdas (*Automated Evaluator*) untuk 12 QA Metrik berbasis sains yang menskor Sistem & Model (lihat [[METRICS_THEORY]]).

## 2. Core Logic & Variables
- `academic_demo_real.db`: SQLite DB untuk corpus utama 1.000 dokumen akademik Indonesia (Skripsi, Jurnal, Dataset).
- `academic_metadata.db`: SQLite DB paralel untuk metadata.
- `multi_label_model.onnx`: Model klasifikasi 20-kelas *Zero-Shot* (berdasarkan Rice Rule).

## 3. Aturan Taksonomi
Berdasarkan *Rice Rule*, $N=1000 \rightarrow \lceil 2 \times 1000^{1/3} \rceil = 20$ Label Kelas (3 Domain L1, 17 Detail L2).

## 4. Evaluasi Matematis
Sistem menggunakan `TPD-Cosine Similarity` ($\theta=0.92$) & `Hybrid Fusion` ($\alpha=0.70$) untuk penalaran.

*Hub Sentral Log: Lihat riwayat di [[CHANGELOG]] dan pemikiran teknis di [[DIARY]].*
