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
* $n$: Panjang dimensi vektor (untuk BERT-Mini, $n = 5$ pada output logits classifier).

---

## 2. Perhitungan Vektor Norm ($L_2$ Norm / Euclidean Norm)
Vektor norm (panjang Euclidean) mengukur jarak lurus dari titik asal $(0, 0, \dots, 0)$ ke ujung vektor tersebut. Digunakan untuk menormalkan panjang vektor dokumen agar tidak bias oleh panjangnya teks.

$$\|\mathbf{A}\| = \sqrt{\sum_{i=1}^{n} A_i^2} = \sqrt{A_1^2 + A_2^2 + \dots + A_n^2}$$

### Deskripsi Variabel:
* $\|\mathbf{A}\|$: Norm atau panjang Euclidean dari vektor $\mathbf{A}$.
* $A_i^2$: Hasil kuadrat elemen ke-$i$ dari vektor $\mathbf{A}$.

---

## 3. Rumus Cosine Similarity (Kemiripan Kosinus)
Cosine similarity menghitung kosinus sudut antara dua vektor dalam ruang multidimensi. Nilai ini berkisar antara $-1.0$ (berlawanan arah seutuhnya) hingga $1.0$ (searah sempurna).

$$\text{Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \cos(\theta) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|} = \frac{\sum_{i=1}^{n} A_i B_i}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}}$$

### Deskripsi Variabel:
* $\cos(\theta)$: Nilai kemiripan arah semantik. Semakin mendekati $1.0$, makna kalimat terbukti semakin mirip.
* $\mathbf{A} \cdot \mathbf{B}$: Dot product dari vektor $\mathbf{A}$ dan $\mathbf{B}$.
* $\|\mathbf{A}\| \|\mathbf{B}\|$: Hasil perkalian panjang norm masing-masing vektor.

---

## 4. Rumus Persentase Kemiripan Kosinus Mentah (Raw Cosine Similarity Percentage)
Untuk menyajikan tingkat kedekatan semantik yang sangat sensitif terhadap perubahan atau penambahan kata pada dokumen masukan secara jujur, kita mengonversi skor Cosine Similarity mentah langsung ke dalam rentang persentase $[0\%, 100\%]$ tanpa menggunakan normalisasi probabilistik Softmax.

$$\text{Similarity Percentage}(\mathbf{A}, \mathbf{B}) = \max\left(0.0, \min\left(1.0, \text{Cosine Similarity}(\mathbf{A}, \mathbf{B})\right)\right) \times 100\%$$

### Deskripsi Variabel:
* $\text{Similarity Percentage}(\mathbf{A}, \mathbf{B})$: Nilai persentase kemiripan semantik dalam rentang $[0\%, 100\%]$.
* $\text{Cosine Similarity}(\mathbf{A}, \mathbf{B})$: Skor kemiripan kosinus mentah yang dihitung berdasarkan arah vektor semantik.
* $\max(0.0, \min(1.0, x))$: Fungsi pembatas (*clipping*) untuk memastikan nilai berada di rentang geometris yang valid $[0, 1]$.

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

