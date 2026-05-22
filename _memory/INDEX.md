# PROJECT INDEX (STATE MAP)

## 1. Arsitektur Proyek
- **TKI/ & STKI/**: Sistem utama (Flask Web/GUI Desktop) hibrida (Dense BERT + BM25 Sparse).
  - Web UI mencakup 4 fitur utama: **Leaderboard Search**, **Batch Classifier**, **Taxonomy Editor**, dan **Smart Recommendation Engine**.
- **DS/**: Ruang Data Science (Notebook MLOps & eksperimen).
- **_Fondasi/**: Dokumentasi landasan teori, rumus matematika, metodologi pelatihan. 
- **testing/**: Skrip dan dataset uji OOD (Out-of-Distribution) seperti artikel Wikipedia Indonesia untuk stress-test.

## 2. Core Logic & Variables
- `academic_demo_real.db`: SQLite DB untuk corpus utama 1.000 dokumen akademik Indonesia (Skripsi, Jurnal, Dataset).
- `academic_metadata.db`: SQLite DB paralel untuk metadata.
- `multi_label_model.onnx`: Model klasifikasi 20-kelas *Zero-Shot* (berdasarkan Rice Rule).

## 3. Aturan Taksonomi
Berdasarkan *Rice Rule*, $N=1000 \rightarrow \lceil 2 \times 1000^{1/3} \rceil = 20$ Label Kelas (3 Domain L1, 17 Detail L2).

## 4. Evaluasi Matematis
Sistem menggunakan `TPD-Cosine Similarity` ($\theta=0.92$) & `Hybrid Fusion` ($\alpha=0.70$) untuk penalaran.
