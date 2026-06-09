# PROJECT INDEX (STATE MAP)

## 1. Arsitektur Proyek
- **_Presentasi/**: Node presentasi graf L1-L2-L3 (Topologi: [[L1_STKI_CORE]] & [[L1_DATA_SCIENCE]]). Dilengkapi juga dengan dokumen pertahanan arsitektural seperti [[L3_PRACTICE_JSON_ETL]] dan [[L3_PRACTICE_POLYMORPHIC_DB]].
- **TKI/ & STKI/**: Sistem utama (Flask Web/GUI Desktop) hibrida (Dense MiniLM + BM25 Sparse).
- **_UIUX/stki/**: Ruang Pencarian End-User. Memiliki fitur Pencarian Hibrida, Ingesti Berkas, dan Rekomendasi Terkait (Berbasis Teks & File).
- **_UIUX/ds/**: Command Center Data Science. Memiliki grafik alur data interaktif (*Node Pipeline*), Database Explorer bergaya *Accordion*, dan panel generasi Taksonomi K-Means. Desain berlandaskan [[teori_uiux_neobrutalism]].
- **DS/**: Ruang Data Science (Notebook MLOps & eksperimen). Spesifikasi teknis berada di [[spesifikasi_teknis]].
- **_Fondasi/**: Dokumentasi landasan teori, metodologi, dan QA. Rujukan dimensional collapse ada di [[dimensional_collapse_stki]], dan panduan antarmuka di [[teori_uiux_neobrutalism]].
- **_Quality_Assurance/**: Mesin evaluasi cerdas untuk 12 QA Metrik berbasis sains yang menskor Sistem & Model (lihat [[METRICS_THEORY]]).

## 2. Core Logic & Variables
- `stki_master.db`: Pangkalan Data Sentral (Central Database) berarsitektur *B-Tree Polymorphic* yang menampung seluruh korpus secara terisolasi via penamaan tabel (`tb_docs_{domain}`, `tb_tax_{domain}`). Menggantikan arsitektur Multi-DB lawas demi minimalisasi *I/O Bottleneck*.
- `multi_label_model.onnx`: Model klasifikasi 384-D Dense `paraphrase-multilingual-MiniLM-L12-v2`.

## 3. Aturan Taksonomi Dinamis (Multi-Label Venn Architecture)
Sistem tidak lagi menggunakan label kaku (*Hard Clustering*). K-Means Clustering + TF-IDF dijalankan murni untuk **menemukan** topik (*Topic Discovery*). Jumlah optimal topik digali menggunakan **Rice Rule**: $X = \lceil 2 \cdot N^{1/3} \rceil$.
Setelah itu, pelabelan menggunakan **Cosine Thresholding** ($\tau \ge 0.50$), memungkinkan dokumen memiliki banyak irisan label secara dinamis (Venn Diagram) atau Outlier Fallback. Metrik tumpang tindih (*Cardinality*) dan Outlier secara presisi divisualisasikan melalui **Telemetry Matrix** di *Command Center*.

## 4. Evaluasi Matematis & Optimasi Latensi
Sistem menggunakan `TPD-Cosine Similarity` ($\theta=0.92$) & `Hybrid Fusion` ($\alpha=0.70$) untuk penalaran.
Untuk pencarian skala industri, implementasi **In-Memory Semantic Caching** mem- *bypass* parsial JSON SQLite, menyajikan kecepatan akses vektor dengan kompleksitas $O(1)$.

*Hub Sentral Log: Lihat riwayat di [[CHANGELOG]] dan pemikiran teknis di [[DIARY]].*
