# Studi Kasus Perhitungan Matematika STKI & Pelabelan
**Dokumen Fondasi Akademik - Penyelesaian Lengkap Langkah-Demi-Langkah**

Dokumen ini menyajikan 4 studi kasus perhitungan matematika lengkap yang digunakan dalam sistem pelabelan semantik multi-layer offline. Seluruh perhitungan diuraikan secara eksplisit **tanpa ada satu pun tahapan matematis yang dilewati**, guna menjamin validitas akademik tingkat tinggi saat sidang tugas akhir.

---

## Studi Kasus 1: Perhitungan Dasar Cosine Similarity
Kita ingin mengukur tingkat kemiripan semantik antara Vektor Ringkasan Dokumen ($\mathbf{A}$) dengan Vektor Kandidat Label "Akademik Mahasiswa" ($\mathbf{B}$).

Misalkan output representasi logits berdimensi 5 dari model adalah:
* Vektor Dokumen $\mathbf{A} = [0.8, 0.6, 0.1, -0.2, 0.5]$
* Vektor Label $\mathbf{B} = [0.7, 0.5, 0.2, -0.1, 0.4]$

### Langkah 1: Hitung Perkalian Titik (Dot Product) $\mathbf{A} \cdot \mathbf{B}$
$$\mathbf{A} \cdot \mathbf{B} = \sum_{i=1}^{5} A_i B_i = (A_1 B_1) + (A_2 B_2) + (A_3 B_3) + (A_4 B_4) + (A_5 B_5)$$

Masukkan nilai-nilai elemen vektor:
$$\mathbf{A} \cdot \mathbf{B} = (0.8 \times 0.7) + (0.6 \times 0.5) + (0.1 \times 0.2) + ((-0.2) \times (-0.1)) + (0.5 \times 0.4)$$
$$\mathbf{A} \cdot \mathbf{B} = 0.56 + 0.30 + 0.02 + 0.02 + 0.20$$
$$\mathbf{A} \cdot \mathbf{B} = 1.10$$

---

### Langkah 2: Hitung Vektor Norm $L_2$ Dokumen $\|\mathbf{A}\|$
$$\|\mathbf{A}\| = \sqrt{A_1^2 + A_2^2 + A_3^2 + A_4^2 + A_5^2}$$
$$\|\mathbf{A}\| = \sqrt{0.8^2 + 0.6^2 + 0.1^2 + (-0.2)^2 + 0.5^2}$$
$$\|\mathbf{A}\| = \sqrt{0.64 + 0.36 + 0.01 + 0.04 + 0.25}$$
$$\|\mathbf{A}\| = \sqrt{1.30}$$
$$\|\mathbf{A}\| \approx 1.140175$$

---

### Langkah 3: Hitung Vektor Norm $L_2$ Label $\|\mathbf{B}\|$
$$\|\mathbf{B}\| = \sqrt{B_1^2 + B_2^2 + B_3^2 + B_4^2 + B_5^2}$$
$$\|\mathbf{B}\| = \sqrt{0.7^2 + 0.5^2 + 0.2^2 + (-0.1)^2 + 0.4^2}$$
$$\|\mathbf{B}\| = \sqrt{0.49 + 0.25 + 0.04 + 0.01 + 0.16}$$
$$\|\mathbf{B}\| = \sqrt{0.95}$$
$$\|\mathbf{B}\| \approx 0.974679$$

---

### Langkah 4: Hitung Nilai Cosine Similarity
$$\text{Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \frac{\mathbf{A} \cdot \mathbf{B}}{\|\mathbf{A}\| \|\mathbf{B}\|}$$
$$\text{Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \frac{1.10}{1.140175 \times 0.974679}$$
$$\text{Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \frac{1.10}{1.111304}$$
$$\text{Cosine Similarity}(\mathbf{A}, \mathbf{B}) \approx 0.989828 \quad (\text{atau } 98.98\%)$$

**Kesimpulan Kasus 1:** Sudut antar kedua vektor sangat kecil (kosinus mendekati 1.0), membuktikan dokumen memiliki kemiripan makna semantik yang sangat kuat dengan label "Akademik Mahasiswa".

---

## Studi Kasus 2: Perbandingan Skor Mentah Layer 1 (Multi-Layer)
Kita menguji sebuah dokumen spreadsheet baru **`data_sks.xlsx`** (yang memiliki metadata kolom jadwal kelas) terhadap **3 kandidat label pada Layer 1 (Domain)**.

Vektor representasi dokumen baru adalah:
* $\mathbf{D} = [0.75, 0.42, 0.88, -0.15, 0.60]$

Kita memiliki 3 Vektor Kandidat Domain pada Layer 1:
1. **Domain 1 (Akademik Mahasiswa):** $\mathbf{L}_1 = [0.70, 0.35, 0.80, -0.10, 0.55]$
2. **Domain 2 (Administrasi Dosen):** $\mathbf{L}_2 = [0.65, 0.40, 0.75, -0.20, 0.50]$
3. **Domain 3 (Jadwal dan SKS Perkuliahan):** $\mathbf{L}_3 = [0.76, 0.45, 0.90, -0.12, 0.62]$

*Catatan: Norm Vektor Dokumen $\|\mathbf{D}\| = \sqrt{0.75^2 + 0.42^2 + 0.88^2 + (-0.15)^2 + 0.60^2} = \sqrt{0.5625 + 0.1764 + 0.7744 + 0.0225 + 0.3600} = \sqrt{1.8958} \approx 1.376880$*

### Bagian A: Menghitung Similarity Dokumen terhadap Domain 1 ($\mathbf{L}_1$)
1. **Dot Product:**
   $$\mathbf{D} \cdot \mathbf{L}_1 = (0.75 \times 0.70) + (0.42 \times 0.35) + (0.88 \times 0.80) + ((-0.15) \times (-0.10)) + (0.60 \times 0.55)$$
   $$\mathbf{D} \cdot \mathbf{L}_1 = 0.5250 + 0.1470 + 0.7040 + 0.0150 + 0.3300 = 1.7210$$
2. **Norm $\mathbf{L}_1$:**
   $$\|\mathbf{L}_1\| = \sqrt{0.70^2 + 0.35^2 + 0.80^2 + (-0.10)^2 + 0.55^2} = \sqrt{0.49 + 0.1225 + 0.64 + 0.01 + 0.3025} = \sqrt{1.565} \approx 1.2509996$$
3. **Similarity Mentah ($s_1$):**
   $$s_1 = \frac{1.7210}{1.376880 \times 1.2509996} = \frac{1.7210}{1.722476} \approx 0.999143$$

---

### Bagian B: Menghitung Similarity Dokumen terhadap Domain 2 ($\mathbf{L}_2$)
1. **Dot Product:**
   $$\mathbf{D} \cdot \mathbf{L}_2 = (0.75 \times 0.65) + (0.42 \times 0.40) + (0.88 \times 0.75) + ((-0.15) \times (-0.20)) + (0.60 \times 0.50)$$
   $$\mathbf{D} \cdot \mathbf{L}_2 = 0.4875 + 0.1680 + 0.6600 + 0.0300 + 0.3000 = 1.6455$$
2. **Norm $\mathbf{L}_2$:**
   $$\|\mathbf{L}_2\| = \sqrt{0.65^2 + 0.40^2 + 0.75^2 + (-0.20)^2 + 0.50^2} = \sqrt{0.4225 + 0.16 + 0.5625 + 0.04 + 0.25} = \sqrt{1.435} \approx 1.1979148$$
3. **Similarity Mentah ($s_2$):**
   $$s_2 = \frac{1.6455}{1.376880 \times 1.1979148} = \frac{1.6455}{1.649385} \approx 0.997644$$

---

### Bagian C: Menghitung Similarity Dokumen terhadap Domain 3 ($\mathbf{L}_3$)
1. **Dot Product:**
   $$\mathbf{D} \cdot \mathbf{L}_3 = (0.75 \times 0.76) + (0.42 \times 0.45) + (0.88 \times 0.90) + ((-0.15) \times (-0.12)) + (0.60 \times 0.62)$$
   $$\mathbf{D} \cdot \mathbf{L}_3 = 0.5700 + 0.1890 + 0.7920 + 0.0180 + 0.3720 = 1.9410$$
2. **Norm $\mathbf{L}_3$:**
   $$\|\mathbf{L}_3\| = \sqrt{0.76^2 + 0.45^2 + 0.90^2 + (-0.12)^2 + 0.62^2} = \sqrt{0.5776 + 0.2025 + 0.81 + 0.0144 + 0.3844} = \sqrt{1.9889} \approx 1.4102836$$
3. **Similarity Mentah ($s_3$):**
   $$s_3 = \frac{1.9410}{1.376880 \times 1.4102836} = \frac{1.9410}{1.941791} \approx 0.999592$$

**Hasil Rekapitulasi Skor Mentah:**
* Domain 1 (Akademik Mahasiswa) = $0.999143$
* Domain 2 (Administrasi Dosen) = $0.997644$
* Domain 3 (Jadwal dan SKS Perkuliahan) = $0.999592$ (Skor Tertinggi!)

---

## Studi Kasus 3: Konversi Persentase Kemiripan Kosinus Mentah Layer 1
Kita ingin mengonversi skor Cosine Similarity mentah dari Studi Kasus 2 ($s_1 = 0.999143$, $s_2 = 0.997644$, $s_3 = 0.999592$) secara langsung ke dalam bentuk persentase visual tanpa menggunakan normalisasi probabilistik Softmax.

### Langkah 1: Hitung Persentase untuk Domain 1 (Akademik Mahasiswa)
$$P_1 = \max(0.0, \min(1.0, 0.999143)) \times 100\%$$
$$P_1 = 0.999143 \times 100\%$$
$$P_1 = 99.91\%$$

---

### Langkah 2: Hitung Persentase untuk Domain 2 (Administrasi Dosen)
$$P_2 = \max(0.0, \min(1.0, 0.997644)) \times 100\%$$
$$P_2 = 0.997644 \times 100\%$$
$$P_2 = 99.76\%$$

---

### Langkah 3: Hitung Persentase untuk Domain 3 (Jadwal dan SKS Perkuliahan)
$$P_3 = \max(0.0, \min(1.0, 0.999592)) \times 100\%$$
$$P_3 = 0.999592 \times 100\%$$
$$P_3 = 99.96\%$$

---

### Analisis Sensitivitas Kata (Bukti Kejujuran Matematis):
Misalkan dokumen input dikurangi beberapa kata penting sehingga kemiripan semantiknya dengan Domain 3 melorot menjadi $0.854210$. 
$$P_3' = \max(0.0, \min(1.0, 0.854210)) \times 100\% = 85.42\%$$
Terlihat dengan sangat jelas bahwa persentase turun secara dinamis dari **$99.96\%$** menjadi **$85.42\%$**. Hal ini membuktikan sensitivitas kata yang sangat presisi dan jujur, bebas dari bias one-hot Softmax!

**Keputusan Akhir Layer 1:** Dokumen dipetakan ke **"Jadwal dan SKS Perkuliahan"** dengan tingkat kesamaan semantik **$99.96\%$**.

---

## Studi Kasus 4: Konversi Persentase Kemiripan Kosinus Mentah Layer 2
Selanjutnya, dokumen kita evaluasi pada **Layer 2 (Detail)** untuk menentukan format spesifik berkasnya secara presisi.

Misalkan skor *Cosine Similarity* mentah hasil kalkulasi model ONNX untuk 5 kandidat label Layer 2 adalah:
1. `Transkrip Nilai Lengkap` ($s_{2,1} = 0.9312$)
2. `KRS SKS Kelas` ($s_{2,2} = 0.9482$) (Skor Mentah Tertinggi!)
3. `Daftar Dosen Pengajar` ($s_{2,3} = 0.9105$)
4. `Laporan Keuangan` ($s_{2,4} = 0.8540$)
5. `Kurikulum Jurusan` ($s_{2,5} = 0.8820$)

### Perhitungan Langkah-Demi-Langkah:
1. **Transkrip Nilai Lengkap:**
   $$P_{2,1} = \max(0.0, \min(1.0, 0.9312)) \times 100\% = 93.12\%$$
2. **KRS SKS Kelas:**
   $$P_{2,2} = \max(0.0, \min(1.0, 0.9482)) \times 100\% = 94.82\%$$
3. **Daftar Dosen Pengajar:**
   $$P_{2,3} = \max(0.0, \min(1.0, 0.9105)) \times 100\% = 91.05\%$$
4. **Laporan Keuangan:**
   $$P_{2,4} = \max(0.0, \min(1.0, 0.8540)) \times 100\% = 85.40\%$$
5. **Kurikulum Jurusan:**
   $$P_{2,5} = \max(0.0, \min(1.0, 0.8820)) \times 100\% = 88.20\%$$

---

### Hasil Klasifikasi Akhir Sistem:
* **Keputusan Layer 1:** `Jadwal dan SKS Perkuliahan` ($99.96\%$)
* **Keputusan Layer 2:** `KRS SKS Kelas` ($94.82\%$)

**Output Teks di Panel Dashboard GUI:**
`Jadwal dan SKS Perkuliahan (99.96%) ==> KRS SKS Kelas (94.82%)`

Perhitungan semantik multi-layer ini membuktikan dengan presisi sangat tinggi bahwa dokumen spreadsheet **`data_sks.xlsx`** tergolong dalam domain **Jadwal dan SKS Perkuliahan** dengan format spesifik **KRS SKS Kelas**, di mana setiap perubahan kecil pada isi sel berkas akan terefleksi secara proporsional dan jujur pada skor visual!

---

## Studi Kasus 5: Perhitungan Hybrid Retrieval (Dense BERT + Sparse BM25)
Kita memiliki dokumen kueri $Q$ (transkrip mahasiswa) yang akan dicari kecocokannya terhadap dokumen di database $D_1$ (dokumen transkrip asli yang sangat relevan) dan $D_2$ (dokumen profil dosen yang tidak sengaja mengandung nama mahasiswa tersebut).

### Kueri & Korpus Data Sederhana:
* **Kueri $Q$:** "transkrip rian hidayat"
* **Dokumen $D_1$:** "dokumen transkrip nilai rian hidayat mahasiswa informatika"
* **Dokumen $D_2$:** "profil dosen pembimbing akademik dari rian hidayat"
* **Statistik Korpus:**
  * Jumlah Dokumen $N = 2$.
  * Rata-rata panjang dokumen $\text{avgdl} = \frac{|D_1| + |D_2|}{2} = \frac{7 + 7}{2} = 7.0$ kata.
  * Panjang dokumen $|D_1| = 7$, $|D_2| = 7$.
  * Frekuensi kata kunci pada dokumen:
    * $q_1 = \text{"transkrip"}$: $f(q_1, D_1) = 1$, $f(q_1, D_2) = 0$. Muncul di 1 dokumen $\Rightarrow n(q_1) = 1$.
    * $q_2 = \text{"rian"}$: $f(q_2, D_1) = 1$, $f(q_2, D_2) = 1$. Muncul di 2 dokumen $\Rightarrow n(q_2) = 2$.
    * $q_3 = \text{"hidayat"}$: $f(q_3, D_1) = 1$, $f(q_3, D_2) = 1$. Muncul di 2 dokumen $\Rightarrow n(q_3) = 2$.

---

### TAHAP A: HITUNG SKOR SPARSE BM25

#### 1. Hitung Nilai IDF untuk Setiap Kata Kunci:
* **IDF("transkrip"):**
  $$\text{IDF}(q_1) = \ln\left(\frac{2 - 1 + 0.5}{1 + 0.5} + 1.0\right) = \ln\left(\frac{1.5}{1.5} + 1.0\right) = \ln(2.0) \approx 0.693147$$
* **IDF("rian") & IDF("hidayat"):**
  $$\text{IDF}(q_2) = \text{IDF}(q_3) = \ln\left(\frac{2 - 2 + 0.5}{2 + 0.5} + 1.0\right) = \ln\left(\frac{0.5}{2.5} + 1.0\right) = \ln(0.2 + 1.0) = \ln(1.2) \approx 0.182322$$

#### 2. Hitung Skor BM25 untuk Dokumen 1 ($D_1$):
*Parameter: $k_1 = 1.5, b = 0.75$. Karena $|D_1| = \text{avgdl} = 7$, maka penyebut penyusutan panjang dokumen adalah $1 - b + b \cdot (1.0) = 1.0$.*

* **Untuk $q_1$ ("transkrip"):**
  $$\text{Skor}_{q_1} = 0.693147 \cdot \frac{1 \cdot (1.5 + 1)}{1 + 1.5 \cdot (1.0)} = 0.693147 \cdot \frac{2.5}{2.5} = 0.693147$$
* **Untuk $q_2$ ("rian"):**
  $$\text{Skor}_{q_2} = 0.182322 \cdot \frac{1 \cdot 2.5}{2.5} = 0.182322$$
* **Untuk $q_3$ ("hidayat"):**
  $$\text{Skor}_{q_3} = 0.182322 \cdot \frac{1 \cdot 2.5}{2.5} = 0.182322$$
* **Total Skor BM25 ($D_1$):**
  $$\text{Score}_{\text{BM25}}(D_1) = 0.693147 + 0.182322 + 0.182322 = 1.057791$$

#### 3. Hitung Skor BM25 untuk Dokumen 2 ($D_2$):
* **Untuk $q_1$ ("transkrip"):** $f(q_1, D_2) = 0 \Rightarrow \text{Skor}_{q_1} = 0.0$
* **Untuk $q_2$ ("rian"):**
  $$\text{Skor}_{q_2} = 0.182322 \cdot \frac{1 \cdot 2.5}{2.5} = 0.182322$$
* **Untuk $q_3$ ("hidayat"):**
  $$\text{Skor}_{q_3} = 0.182322 \cdot \frac{1 \cdot 2.5}{2.5} = 0.182322$$
* **Total Skor BM25 ($D_2$):**
  $$\text{Score}_{\text{BM25}}(D_2) = 0.0 + 0.182322 + 0.182322 = 0.364644$$

#### 4. Normalisasi Skor BM25:
* Nilai maksimum BM25 pada korpus adalah $\max(1.057791, 0.364644) = 1.057791$.
* **Normalized BM25 ($D_1$):**
  $$\text{Score}_{\text{BM25, Norm}}(D_1) = \frac{1.057791}{1.057791} = 1.000000$$
* **Normalized BM25 ($D_2$):**
  $$\text{Score}_{\text{BM25, Norm}}(D_2) = \frac{0.364644}{1.057791} \approx 0.344722$$

---

### TAHAP B: HITUNG HYBRID RETRIEVAL FUSION

Misalkan hasil evaluasi kemiripan kosinus representasi vektor padat (Dense BERT) adalah:
* $\text{Similarity}_{\text{Dense}}(D_1) = 0.920000$ (Sangat relevan)
* $\text{Similarity}_{\text{Dense}}(D_2) = 0.450000$ (Kurang relevan)

Kita gabungkan dengan parameter bobot $\alpha = 0.70$:

#### 1. Skor Hybrid Akhir Dokumen 1 ($D_1$):
$$\text{Score}_{\text{Hybrid}}(D_1) = 0.70 \cdot (0.920000) + 0.30 \cdot (1.000000)$$
$$\text{Score}_{\text{Hybrid}}(D_1) = 0.644000 + 0.300000 = 0.944000 \quad (\text{atau } 94.40\%)$$

#### 2. Skor Hybrid Akhir Dokumen 2 ($D_2$):
$$\text{Score}_{\text{Hybrid}}(D_2) = 0.70 \cdot (0.450000) + 0.30 \cdot (0.344722)$$
$$\text{Score}_{\text{Hybrid}}(D_2) = 0.315000 + 0.103417 = 0.418417 \quad (\text{atau } 41.84\%)$$

---

### Analisis Hasil Akhir:
Sistem menetapkan Dokumen 1 ($D_1$) sebagai berkas serupa teratas dengan nilai kecocokan **$94.40\%$** sedangkan Dokumen 2 ($D_2$) teredam jauh di bawahnya pada **$41.84\%$**. Hal ini membuktikan bahwa penggabungan kekuatan **BERT Dense** (yang menangkap konsep akademis) dan **BM25 Sparse** (yang menangkap kata kunci unik `"transkrip"`) bekerja dengan sangat efektif, presisi, dan secara akademis sangat akuntabel!

---

## Studi Kasus 6: Penentuan Jumlah Kategori Optimal (Rice Rule)
Kita ingin merancang taksonomi pengelompokan semantik dokumen riset & pengabdian masyarakat (SINTA, IEEE, Paten) pada database aktif. Kita ingin menentukan jumlah optimal kategori/label ($X$) secara teoretis berdasarkan jumlah dokumen dalam korpus aktif ($N$).

### Kasus A: Jumlah Dokumen Korpus Utama / Demo ($N = 1000$ berkas)
Kita menerapkan Aturan Rice (*Rice Rule*):

1. **Rumus:**
   $$X = \lceil 2 \cdot N^{1/3} \rceil$$
2. **Substitusi Nilai $N$:**
   $$X = \lceil 2 \cdot 1000^{1/3} \rceil$$
3. **Hitung Akar Pangkat Tiga:**
   $$1000^{1/3} = 10$$
4. **Kalikan Parameter Konstanta:**
   $$X = \lceil 2 \cdot 10 \rceil = 20 \text{ Label}$$

**Hasil Kasus A:** Taksonomi ideal harus memiliki tepat **20 label unik** (misalnya 3 Domain Makro dan 17 Detail Mikro) agar sebaran dokumen tidak mengalami overfitting maupun underfitting.

---

### Kasus B: Jumlah Dokumen Korpus Mini / Custom ($N = 125$ berkas)
Misalkan pengguna mereset database dengan sampel mini sebanyak 125 berkas.

1. **Substitusi Nilai $N$:**
   $$X = \lceil 2 \cdot 125^{1/3} \rceil$$
2. **Hitung Akar Pangkat Tiga:**
   $$125^{1/3} = 5$$
3. **Kalikan Parameter Konstanta:**
   $$X = \lceil 2 \cdot 5 \rceil = 10 \text{ Label}$$

**Hasil Kasus B:** Untuk 125 dokumen, taksonomi ideal mencakup tepat **10 label unik**.

