# [L2] SUB-SYSTEM: TAXONOMY ENGINE & VENN ARCHITECTURE

Berakar pada [[L1_DATA_SCIENCE]], *Taxonomy Engine* menghancurkan paradigma kategorisasi korpus ortodoks yang memaksakan satu dokumen hanya berdiam pada satu wadah klaster absolut (*Hard Clustering*). Sub-sistem ini memberlakukan arsitektur irisan berbasis himpunan (*Venn Architecture*), memungkinkan korpus memiliki ikatan taksonomi jamak yang bersifat probabilitas dinamis. Mesin tidak berasumsi bahwa sebuah paper ilmiah tentang "Natural Language Processing dalam Diagnosa Medis" eksklusif milik klaster "Informatika" tanpa probabilitas lintasan ke "Ilmu Kedokteran".

Proses otonom diinisialisasi melalui algoritma *K-Means Clustering* konvensional. Namun, ia diregulasi keras oleh *Rice Rule* untuk menentukan batasan ideal $K$, menghapuskan tebakan jumlah kelompok secara sewenang-wenang berdasarkan insting manusia. *K-Means* ini murni berfungsi sebagai ekstraktor *Centroid Topic Space* (koordinat ruang vektor), sedangkan penamaan teks labelnya (seperti "Pajak Daerah" atau "Pendidikan") diekstrak secara otomatis menggunakan probabilitas kata kunci tertinggi dari **TF-IDF Vectorizer**. 

Setelah ruang topik dan namanya terbentuk, entitas pelabel utama (pembagi dokumen) adalah komputator Cosine Thresholding yang menghitung deviasi dokumen individual terhadap setiap *Centroid* tersebut untuk menciptakan relasi Multi-Label.

| Dimensi | Deskripsi Teknis | Dampak Arsitektural |
| :--- | :--- | :--- |
| **Generasi Dimensi Takson** | Restriksi jumlah *Centroid* via Teorema Rice Rule ($X = \lceil 2 \cdot N^{1/3} \rceil$). | Otonomisasi penuh pada pipa analitik; mencegah partisi ekstrim (terlalu banyak/sedikit) tanpa iterasi komputasi ganda. |
| **Penamaan Sentroid (Naming)** | Ekstraksi *Top Keywords* pembentuk klaster menggunakan vektor bobot **TF-IDF**. | Menerjemahkan titik koordinat numerik *Dense Vector* (K-Means) menjadi bahasa leksikal yang dapat dipahami antarmuka manusia. |
| **Evaluasi Irisan (Venn)** | Pengukuran skalar geometri jarak titik dokumen ke *N-Centroid* menggunakan parameter $\tau \ge 0.50$. | Mengakomodasi *Multi-Label Matrix* di level sistem, menggeser struktur penyimpanan RDBMS dari *One-to-Many* menjadi relasi graf bobot spasial. |
| **Sistem Proteksi Outlier** | *Graceful degradation* dengan mendegradasi anomali ber-kemiripan absolut rendah menuju klaster *Fallback*. | Memproteksi kemurnian sentroid (*Centroid Purity*); memastikan taksonomi inti tidak terdistorsi oleh korpus acak/anomali linguistik. |

Kompleksitas perhitungan *multi-label* mendelegasikan kebutuhan matematis absolut ke lapisan implementasi (L3). *Pipeline* wajib mengoptimalkan matriks numpy agar terhindar dari *out-of-memory errors* (OOM) ketika matriks dokumen menembus besaran $>100,000$ baris vektor dimensi tinggi. 

```mermaid
graph TD
    classDef l2 fill:#16213e,stroke:#e94560,stroke-width:1px,color:#eee;
    classDef l3 fill:#0f3460,stroke:#fca311,stroke-width:1px,color:#fff;

    ROOT["[L2]\nTAXONOMY ENGINE\n& VENN ARCH"]:::l2
    
    L3_RICE["[L3]\nRICE RULE\nMATHEMATICS"]:::l3
    L3_COSINE["[L3]\nCOSINE THRESHOLDING\n(MULTI-LABEL)"]:::l3
    L3_OUTLIER["[L3]\nOUTLIER FALLBACK\nMECHANISM"]:::l3

    ROOT -->|"Regulasi\nPenentuan Limit K"| L3_RICE
    ROOT -->|"Logika Penentuan\nIrisan Topik Venn"| L3_COSINE
    ROOT -->|"Proteksi Kemurnian\nTaksonomi Ruang"| L3_OUTLIER
```

**Keterhubungan Graf (L3 Deep Dive Nodes):**
- [[L3_THEORY_RICE_RULE]]: Justifikasi Matematis $K$ Otonom berdasarkan distribusi populasi $N$.
- [[L3_PRACTICE_COSINE_THRESHOLDING]]: Logika komputasi jarak dinamis dan konversi probabilitas matriks Multi-Label.
- [[L3_PRACTICE_OUTLIER_FALLBACK]]: Mekanisme kondisional *Threshold* Penolakan.

---
*Konteks: Bagian dari [[L1_DATA_SCIENCE]]*
