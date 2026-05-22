# Rumus Matematika Klasifikasi Semantik & STKI
**Dokumen Fondasi Akademik - Spesifikasi Rumus Teoretis**

Dokumen ini memuat seluruh kompilasi rumus matematika yang digunakan dalam mesin pencari semantik STKI dan sistem pelabelan otomatis secara offline.

---

## 1. Perhitungan Dot Product (Perkalian Titik)
Dot product antara dua vektor mengukur akumulasi perkalian elemen-elemen yang bersesuaian. Ini menunjukkan tingkat kesejajaran arah kedua vektor dalam ruang multidimensi.

$$\mathbf{A} \cdot \mathbf{B} = \sum_{i=1}^{n} A_i B_i = A_1 B_1 + A_2 B_2 + \dots + A_n B_n$$

### Deskripsi Variabel:
* $\mathbf{A}, \mathbf{B}$: Dua buah vektor berdimensi $n$ (misal: vektor embedding dokumen dan vektor embedding label).
* $A_i, B_i$: Nilai elemen ke-$i$ dari masing-masing vektor.
* $n$: Panjang dimensi vektor (untuk BERT-Mini, $n = 20$ pada output logits classifier).

---

## 2. Perhitungan Vektor Norm ($L_2$ Norm / Euclidean Norm)
Vektor norm (panjang Euclidean) mengukur jarak lurus dari titik asal $(0, 0, \dots, 0)$ ke ujung vektor tersebut. Digunakan untuk menormalkan panjang vektor dokumen agar tidak bias oleh panjangnya teks.

$$\|\mathbf{A}\| = \sqrt{\sum_{i=1}^{n} A_i^2} = \sqrt{A_1^2 + A_2^2 + \dots + A_n^2}$$

### Deskripsi Variabel:
* $\|\mathbf{A}\|$: Norm atau panjang Euclidean dari vektor $\mathbf{A}$.
* $A_i^2$: Hasil kuadrat elemen ke-$i$ dari vektor $\mathbf{A}$.

---

## 3. Rumus Thresholded Positive Deviation Cosine Similarity (TPD-Cosine Similarity)
TPD-Cosine similarity menghitung kemiripan kosinus sudut antara dua vektor yang telah dikurangi baseline bias model (null embedding) dan dilakukan penyaringan nilai deviasi positif dengan ambang batas (threshold) $t$. Hal ini bertujuan untuk menghilangkan bias background noise (representation collapse) di mana dokumen acak dapat dinilai $99\%$ mirip dengan label non-relevan.

Langkah pertama adalah menghitung deviasi positif bersih terhadap null embedding $\mathbf{v}_{\text{null}}$:
$$\mathbf{A}_{\text{clean}} = \mathbf{A} - \mathbf{v}_{\text{null}}$$
$$\mathbf{B}_{\text{clean}} = \mathbf{B} - \mathbf{v}_{\text{null}}$$

Langkah kedua adalah menyaring elemen vektor menggunakan threshold $t$ (pada sistem diatur $t = 0.02$):
$$\tilde{A}_i = \begin{cases} A_{\text{clean}, i} & \text{if } A_{\text{clean}, i} \ge t \\ 0.0 & \text{otherwise} \end{cases}$$
$$\tilde{B}_i = \begin{cases} B_{\text{clean}, i} & \text{if } B_{\text{clean}, i} \ge t \\ 0.0 & \text{otherwise} \end{cases}$$

Langkah ketiga adalah menghitung nilai kesamaan sudut geometris:
$$\text{TPD-Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \begin{cases} \frac{\tilde{\mathbf{A}} \cdot \tilde{\mathbf{B}}}{\|\tilde{\mathbf{A}}\| \|\tilde{\mathbf{B}}\|} = \frac{\sum_{i=1}^{n} \tilde{A}_i \tilde{B}_i}{\sqrt{\sum_{i=1}^{n} \tilde{A}_i^2} \sqrt{\sum_{i=1}^{n} \tilde{B}_i^2}} & \text{if } \|\tilde{\mathbf{A}}\| > 0 \text{ and } \|\tilde{\mathbf{B}}\| > 0 \\ 0.0 & \text{otherwise} \end{cases}$$

### Deskripsi Variabel:
* $\mathbf{A}, \mathbf{B}$: Dua buah vektor probabilitas keluaran model (dimensi $n = 20$ untuk model BERT-mini).
* $\mathbf{v}_{\text{null}}$: Vektor null embedding (representasi teks kosong `""` atau token padding saja) untuk mengidentifikasi bias inheren model.
* $\tilde{\mathbf{A}}, \tilde{\mathbf{B}}$: Vektor hasil penyaringan deviasi positif dengan ambang batas $t$.
* $t$: Ambang batas (threshold) aktivasi deviasi positif ($t = 0.02$).
* $\|\tilde{\mathbf{A}}\|, \|\tilde{\mathbf{B}}\|$: Norm atau panjang Euclidean dari vektor tersaring.

---

## 4. Rumus Persentase Kemiripan TPD-Cosine (TPD-Cosine Similarity Percentage)
Untuk menyajikan tingkat kedekatan semantik yang sensitif dan jujur secara visual pada dashboard GUI/Web, kita mengonversi skor TPD-Cosine Similarity langsung ke dalam rentang persentase $[0\%, 100\%]$.

$$\text{Similarity Percentage}(\mathbf{A}, \mathbf{B}) = \text{TPD-Cosine Similarity}(\mathbf{A}, \mathbf{B}) \times 100\%$$

### Deskripsi Variabel:
* $\text{Similarity Percentage}(\mathbf{A}, \mathbf{B})$: Nilai persentase kemiripan semantik akhir dalam rentang $[0\%, 100\%]$.
* $\text{TPD-Cosine Similarity}(\mathbf{A}, \mathbf{B})$: Skor kemiripan kosinus setelah pengurangan baseline bias dan thresholding.

---

## 5. Mean Pooling (Ekstraksi Embedding Representasi Teks)
Operasi matematika untuk mereduksi seluruh representasi token teks kalimat yang dikeluarkan oleh arsitektur Transformer menjadi satu vektor tunggal kalimat (*sentence embedding*).

$$\mathbf{u} = \frac{1}{N} \sum_{k=1}^{N} \mathbf{h}_k$$

### Deskripsi Variabel:
* $\mathbf{u}$: Vektor embedding akhir yang mewakili makna utuh teks dokumen.
* $N$: Jumlah total token kata setelah dipotong padding (maksimal 256 token).
* $\mathbf{h}_k$: Vektor *hidden state* representasi token ke-$k$ dari output layer BERT terakhir.

---

## 6. Rumus Sparse Lexical Score (Okapi BM25)
Digunakan untuk mengukur kemiripan leksikal (kata kunci persis) secara statistik antara kueri dengan dokumen berdasarkan frekuensi kata dan panjang rata-rata dokumen pada korpus.

$$\text{Score}_{\text{BM25}}(Q, D) = \sum_{i=1}^{n} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$

$$\text{IDF}(q_i) = \ln\left(\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1.0\right)$$

### Deskripsi Variabel:
* $\text{Score}_{\text{BM25}}(Q, D)$: Skor leksikal dokumen $D$ terhadap kueri $Q$.
* $f(q_i, D)$: Frekuensi kata kunci $q_i$ di dalam dokumen $D$.
* $|D|$: Jumlah total kata di dalam dokumen $D$.
* $\text{avgdl}$: Panjang rata-rata kata dari seluruh dokumen di korpus database.
* $k_1$: Parameter saturasi frekuensi kata (disetel ke $1.5$ pada sistem).
* $b$: Parameter hukuman panjang dokumen (disetel ke $0.75$ pada sistem).
* $N$: Jumlah total dokumen di dalam korpus database.
* $n(q_i)$: Jumlah dokumen yang mengandung kata kunci $q_i$ minimal satu kali.
* $\text{IDF}(q_i)$: Inverse Document Frequency kata kunci $q_i$.

---

## 7. Rumus Hybrid Retrieval Fusion (Linear Combination)
Rumus untuk menyatukan kekuatan pencarian semantik murni (Dense) dengan pencarian leksikal persis (Sparse BM25) menjadi satu skor kesamaan tunggal yang stabil.

$$\text{Score}_{\text{Hybrid}}(D) = \alpha \cdot \text{Similarity}_{\text{Dense}}(D) + (1 - \alpha) \cdot \text{Score}_{\text{BM25, Normalized}}(D)$$

$$\text{Score}_{\text{BM25, Normalized}}(D) = \frac{\text{Score}_{\text{BM25}}(D)}{\max_{j} \text{Score}_{\text{BM25}}(D_j)}$$

### Deskripsi Variabel:
* $\text{Score}_{\text{Hybrid}}(D)$: Skor kesamaan hibrida akhir dokumen $D$ (skala $[0.0, 1.0]$).
* $\text{Similarity}_{\text{Dense}}(D)$: Kemiripan kosinus representasi vektor padat dokumen $D$ (skala $[0.0, 1.0]$).
* $\text{Score}_{\text{BM25, Normalized}}(D)$: Skor leksikal BM25 dokumen $D$ yang telah dinormalisasi menggunakan nilai maksimum pada korpus agar berskala $[0.0, 1.0]$.
* $\alpha$ (alpha): Parameter bobot pencarian semantik (disetel ke $0.70$ atau $70\%$ pada sistem).

---

## 8. Rumus Optimal Label Count (Rice Rule)
Digunakan dalam perancangan taksonomi dinamis untuk memperkirakan jumlah optimal kategori atau label ($X$) yang representatif berdasarkan ukuran korpus total ($N$) dokumen di dalam database aktif.

$$X = \lceil 2 \cdot N^{1/3} \rceil$$

### Deskripsi Variabel:
* $X$: Jumlah kategori / label optimal yang direkomendasikan secara teoretis.
* $N$: Jumlah total dokumen/berkas yang tersimpan di dalam database SQLite aktif.
* $N^{1/3}$: Operasi akar pangkat tiga dari jumlah dokumen total ($N$).
* $\lceil \dots \rceil$: Operasi pembulatan ke atas (*ceiling*) untuk menjamin bilangan bulat positif terkecil.

---

## 9. Rumus Penyelarasan Booster & Strict Fallback Thresholding
Untuk meminimalkan kesalahan klasifikasi palsu (false positive) pada kelas yang tidak relevan namun memiliki kedekatan kosinus tinggi akibat bias representasi model, sistem menerapkan penyelarasan booster berbasis kata kunci (lexical cues) dan fallback ambang batas ketat secara individual per kelas.

Untuk setiap kelas $i$ pada Layer $L$:
$$\text{Sim}_{\text{final}, i} = \begin{cases} \text{Sim}_{\text{raw}, i} + \text{Boost}_i & \text{if } \text{Boost}_i > 0.0 \\ 0.0 & \text{if } \text{Boost}_i = 0.0 \text{ and } \text{Sim}_{\text{raw}, i} < \theta \\ \text{Sim}_{\text{raw}, i} & \text{otherwise} \end{cases}$$

### Deskripsi Variabel:
* $\text{Sim}_{\text{raw}, i}$: TPD-Cosine similarity mentah antara dokumen dengan kelas $i$.
* $\text{Boost}_i$: Nilai booster leksikal untuk kelas $i$ (misal: $+0.20$ jika ada pencocokan kata kunci tertentu di dalam dokumen).
* $\theta$: Ambang batas (threshold) ketat untuk fallback kelas tanpa booster ($\theta = 0.92$).
* $\text{Sim}_{\text{final}, i}$: Skor kemiripan akhir kelas $i$ setelah penyelarasan booster dan penyaringan ambang batas.

---

## 10. Hierarchical Taxonomy Consistency & Parent Guidance
Untuk menjamin integritas hierarki taksonomi, keputusan klasifikasi Layer 2 (Detail) digunakan untuk membimbing klasifikasi Layer 1 (Domain). Jika kelas Layer 2 terbaik yang terpilih ($\text{Best}_{L2}$) memiliki hubungan induk-anak dengan kelas Layer 1 tertentu ($\text{Parent}_{L1}$), maka kelas Layer 1 tersebut mendapatkan dorongan konsistensi hierarki tambahan.

Untuk setiap kelas $j$ pada Layer 1:
$$\text{Boost}_{L1, j} = \text{Boost}_{\text{lexical}, j} + \text{Boost}_{\text{hierarchical}, j}$$

Di mana:
$$\text{Boost}_{\text{hierarchical}, j} = \begin{cases} 0.30 & \text{if } \text{Parent}(\text{Best}_{L2}) = \text{Label}_{L1, j} \\ 0.0 & \text{otherwise} \end{cases}$$

### Deskripsi Variabel:
* $\text{Best}_{L2}$: Label hasil keputusan klasifikasi terbaik pada Layer 2.
* $\text{Parent}(\text{Best}_{L2})$: Label induk Layer 1 yang menaungi label $\text{Best}_{L2}$ berdasarkan peta taksonomi.
* $\text{Boost}_{\text{lexical}, j}$: Nilai booster leksikal berbasis kata kunci untuk kelas Layer 1 ke-$j$.
* $\text{Boost}_{\text{hierarchical}, j}$: Booster konsistensi hierarki yang ditambahkan sebesar $+0.30$ jika kelas $j$ merupakan induk langsung dari keputusan Layer 2 terbaik.
* $\text{Boost}_{L1, j}$: Total booster yang diakumulasikan untuk kelas Layer 1 ke-$j$ sebelum proses thresholding dilakukan.

---

## 11. Algoritma TextRank untuk Sentralitas Kalimat (Key-Sentence Distillation)
Untuk mengatasi *representation collapse* dan *input length limit* (pemotongan dokumen) pada dokumen panjang, sistem melakukan peringkasan ekstraktif tanpa pengawasan menggunakan model graf TextRank sebelum diumpankan ke model BERT.

### A. Segmentasi Kalimat & Pembersihan
Dokumen dipecah menjadi kumpulan kalimat $S = \{s_1, s_2, \dots, s_M\}$ berdasarkan pembatas tanda baca akhiran (`.`, `!`, `?`) dan baris baru (`\n`). Kalimat dengan jumlah karakter $\le 15$ atau yang merupakan duplikat dari kalimat sebelumnya disaring keluar dari himpunan graf untuk mencegah *boilerplate noise*.

### B. Rumus Kesamaan Logaritma Kalimat (Logarithmic Word-Overlap Similarity)
Tingkat kemiripan leksikal dan kesamaan topik antar-kalimat $s_i$ dan $s_j$ diukur berdasarkan jumlah irisan kosakata unik yang dinormalisasi dengan logaritma panjang kata masing-masing kalimat untuk menghindari bias kalimat panjang:

$$\text{Sim}_{\text{leksikal}}(s_i, s_j) = \frac{|W(s_i) \cap W(s_j)|}{\ln |W(s_i)| + \ln |W(s_j)| + 1}$$

### C. Pembentukan Transition Probability Matrix ($P$)
Matriks kesamaan simetris berukuran $M \times M$ dibentuk dan dinormalisasi baris demi baris untuk menghasilkan transition matrix probabilitas $P$:

$$P_{ij} = \begin{cases} \frac{\text{Sim}_{\text{leksikal}}(s_j, s_i)}{\sum_{k=1}^{M} \text{Sim}_{\text{leksikal}}(s_j, s_k)} & \text{if } \sum_{k=1}^{M} \text{Sim}_{\text{leksikal}}(s_j, s_k) > 0 \\ 0.0 & \text{otherwise} \end{cases}$$

### D. Iterasi Kekuatan PageRank (Power Iteration)
Skor sentralitas setiap kalimat dihitung secara iteratif menggunakan formula PageRank dengan damping factor $d = 0.85$ hingga konvergen atau mencapai maksimum 15 iterasi:

$$\mathbf{PR}^{(t+1)} = (1 - d)\mathbf{1} + d \cdot P^T \mathbf{PR}^{(t)}$$

### Deskripsi Variabel:
* $s_i, s_j$: Kalimat ke-$i$ dan ke-$j$ dalam dokumen tersaring.
* $W(s_i)$: Himpunan kata unik (dalam format huruf kecil tanpa tanda baca) pada kalimat $s_i$.
* $|W(s_i) \cap W(s_j)|$: Kardinalitas irisan himpunan kata unik antara kalimat $s_i$ dan $s_j$.
* $P$: Transition probability matrix dari model graf kalimat.
* $\mathbf{PR}^{(t)}$: Vektor skor PageRank kalimat pada iterasi ke-$t$.
* $d$: Damping factor ($d = 0.85$).
* $\mathbf{1}$: Vektor kolom konstan bernilai $1.0$ berukuran $M \times 1$.

---

## 12. Elemen Confusion Matrix Evaluasi Klasifikasi Multi-Label
Dalam evaluasi klasifikasi multi-label, setiap label dianalisis sebagai masalah klasifikasi biner independen. Empat kategori prediksi dasar didefinisikan sebagai:

$$TP = |\{d \in D : \hat{y}_d = 1 \land y_d = 1\}|$$
$$FP = |\{d \in D : \hat{y}_d = 1 \land y_d = 0\}|$$
$$TN = |\{d \in D : \hat{y}_d = 0 \land y_d = 0\}|$$
$$FN = |\{d \in D : \hat{y}_d = 0 \land y_d = 1\}|$$

### Deskripsi Variabel:
* $D$: Himpunan seluruh dokumen dalam set pengujian.
* $\hat{y}_d$: Label prediksi sistem untuk dokumen $d$ ($1$ = positif, $0$ = negatif).
* $y_d$: Label ground truth (kebenaran) untuk dokumen $d$.
* $TP$: True Positive — prediksi positif yang benar.
* $FP$: False Positive — prediksi positif yang salah.
* $TN$: True Negative — prediksi negatif yang benar.
* $FN$: False Negative — prediksi negatif yang salah (label terlewat).

**Referensi:** Manning, Raghavan & Schütze (2008) — *Introduction to Information Retrieval*, Cambridge University Press, Chapter 8.

---

## 13. Rumus Precision Kelas Positif
Precision positif mengukur proporsi prediksi positif yang benar dari seluruh prediksi positif. Nilai tinggi menandakan sistem jarang memberikan label yang salah.

$$\text{Precision}^{+} = \frac{TP}{TP + FP}$$

### Deskripsi Variabel:
* $\text{Precision}^{+}$: Rasio ketepatan prediksi positif (skala $[0, 1]$).
* $TP + FP$: Total seluruh prediksi positif yang dikeluarkan sistem.

---

## 14. Rumus Recall Kelas Positif / Sensitivity
Recall positif mengukur proporsi label relevan yang berhasil terdeteksi dari seluruh label yang seharusnya ada. Nilai tinggi menandakan sistem jarang melewatkan label benar.

$$\text{Recall}^{+} = \text{Sensitivity} = \frac{TP}{TP + FN}$$

### Deskripsi Variabel:
* $\text{Recall}^{+}$: Rasio cakupan deteksi label positif (skala $[0, 1]$).

---

## 15. Rumus F1-Score Kelas Positif
F1-Score adalah rata-rata harmonik dari Precision dan Recall, memberikan satu metrik tunggal yang menyeimbangkan ketepatan dan cakupan.

$$\text{F1}^{+} = 2 \cdot \frac{\text{Precision}^{+} \cdot \text{Recall}^{+}}{\text{Precision}^{+} + \text{Recall}^{+}}$$

### Deskripsi Variabel:
* $\text{F1}^{+}$: Skor harmonik gabungan (skala $[0, 1]$). Nilai $1.0$ = sempurna, $0.0$ = gagal total.

**Referensi:** Van Rijsbergen, C.J. (1979) — *Information Retrieval*, Butterworths, London.

---

## 16. Rumus Precision Kelas Negatif
Precision negatif mengukur proporsi prediksi negatif yang benar. Penting untuk memastikan sistem tidak keliru menolak label yang seharusnya diberikan.

$$\text{Precision}^{-} = \frac{TN}{TN + FN}$$

### Deskripsi Variabel:
* $\text{Precision}^{-}$: Rasio ketepatan penolakan label (skala $[0, 1]$).

---

## 17. Rumus Recall Kelas Negatif / Specificity
Specificity mengukur kemampuan sistem mengidentifikasi dokumen yang memang tidak termasuk dalam suatu label.

$$\text{Recall}^{-} = \text{Specificity} = \frac{TN}{TN + FP}$$

### Deskripsi Variabel:
* $\text{Recall}^{-}$: Rasio cakupan deteksi negatif benar (skala $[0, 1]$).

---

## 18. Rumus F1-Score Kelas Negatif
F1-Score negatif menyeimbangkan Precision negatif dan Specificity menjadi satu metrik evaluasi untuk kelas non-relevan.

$$\text{F1}^{-} = 2 \cdot \frac{\text{Precision}^{-} \cdot \text{Recall}^{-}}{\text{Precision}^{-} + \text{Recall}^{-}}$$

---

## 19. Rumus Akurasi Keseluruhan
Akurasi mengukur proporsi seluruh prediksi (positif dan negatif) yang benar dari total prediksi.

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}$$

---

## 20. Rumus False Positive Rate (FPR) & False Negative Rate (FNR)
Kedua metrik ini mengukur tingkat kesalahan prediksi sistem secara spesifik per arah.

$$\text{FPR} = \frac{FP}{FP + TN} = 1 - \text{Specificity}$$
$$\text{FNR} = \frac{FN}{FN + TP} = 1 - \text{Recall}^{+}$$

### Deskripsi Variabel:
* $\text{FPR}$: Proporsi dokumen non-relevan yang salah ditandai. Semakin rendah semakin baik.
* $\text{FNR}$: Proporsi dokumen relevan yang gagal terdeteksi. Semakin rendah semakin baik.

---

## 21. Rumus Precision@K (Evaluasi Pencarian STKI)
Precision@K mengukur proporsi dokumen relevan yang muncul di dalam $K$ hasil pencarian teratas.

$$\text{Precision@K}(q) = \frac{|\{d \in \text{Top-K}(q) : d \in R_q\}|}{K}$$

### Deskripsi Variabel:
* $q$: Kueri pencarian pengguna.
* $\text{Top-K}(q)$: Himpunan $K$ dokumen teratas yang dikembalikan sistem untuk kueri $q$.
* $R_q$: Himpunan dokumen yang relevan menurut ground truth untuk kueri $q$.

---

## 22. Rumus Mean Average Precision (MAP)
MAP menghitung rata-rata presisi kumulatif pada setiap posisi dokumen relevan ditemukan, lalu dirata-ratakan atas seluruh kueri pengujian.

$$\text{AP}(q) = \frac{1}{|R_q|} \sum_{k=1}^{n} \text{Precision@k}(q) \cdot \text{rel}(k)$$
$$\text{MAP} = \frac{1}{|Q|} \sum_{q=1}^{|Q|} \text{AP}(q)$$

### Deskripsi Variabel:
* $\text{AP}(q)$: Average Precision untuk kueri $q$.
* $|R_q|$: Jumlah total dokumen relevan untuk kueri $q$.
* $\text{rel}(k)$: Fungsi indikator ($1$ jika dokumen peringkat $k$ relevan, $0$ jika tidak).
* $|Q|$: Jumlah total kueri pengujian.

**Referensi:** Karpukhin et al. (2020) — *Dense Passage Retrieval for Open-Domain Question Answering*, ACL.

---

## 23. Rumus Normalized Discounted Cumulative Gain (NDCG@K)
NDCG@K mengukur kualitas peringkat hasil pencarian dengan memberikan bobot lebih tinggi pada dokumen relevan yang muncul di posisi atas.

$$\text{DCG@K} = \sum_{i=1}^{K} \frac{2^{rel_i} - 1}{\log_2(i + 1)}$$
$$\text{IDCG@K} = \sum_{i=1}^{K} \frac{2^{rel_i^*} - 1}{\log_2(i + 1)}$$
$$\text{NDCG@K} = \frac{\text{DCG@K}}{\text{IDCG@K}}$$

### Deskripsi Variabel:
* $\text{DCG@K}$: Discounted Cumulative Gain aktual dari hasil pencarian sistem.
* $\text{IDCG@K}$: Ideal DCG (nilai DCG jika peringkat sempurna menurut ground truth).
* $rel_i$: Skor relevansi dokumen peringkat ke-$i$ dari hasil sistem (biner: $0$ atau $1$).
* $rel_i^*$: Skor relevansi dokumen peringkat ke-$i$ dari urutan ideal.

**Referensi:** Järvelin & Kekäläinen (2002) — *Cumulated Gain-Based Evaluation of IR Techniques*, ACM TOIS.

