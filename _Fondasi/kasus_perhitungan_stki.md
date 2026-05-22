# Studi Kasus Perhitungan Matematika STKI & Pelabelan
**Dokumen Fondasi Akademik - Penyelesaian Lengkap Langkah-Demi-Langkah**

Dokumen ini menyajikan 4 studi kasus perhitungan matematika lengkap yang digunakan dalam sistem pelabelan semantik multi-layer offline. Seluruh perhitungan diuraikan secara eksplisit **tanpa ada satu pun tahapan matematis yang dilewati**, guna menjamin validitas akademik tingkat tinggi saat sidang tugas akhir.

---

### Studi Kasus 1: Perhitungan Dasar TPD-Cosine Similarity
Keinginan kita adalah mengukur tingkat kemiripan semantik antara Vektor Ringkasan Dokumen ($\mathbf{A}$) dengan Vektor Kandidat Label "Akademik Mahasiswa" ($\mathbf{B}$).

Misalkan kita mengambil 5 kelas pertama dari output representasi logits/probabilitas berdimensi 20 dari model untuk tujuan demonstrasi perhitungan:
* Vektor Dokumen $\mathbf{A} = [0.80, 0.60, 0.10, 0.20, 0.50]$
* Vektor Label $\mathbf{B} = [0.70, 0.55, 0.20, 0.30, 0.40]$
* Vektor Null Embedding (bias baseline) $\mathbf{v}_{\text{null}} = [0.60, 0.50, 0.30, 0.55, 0.45]$
* Ambang Batas (Threshold) $t = 0.02$

### Langkah 1: Pengurangan Baseline Bias (Null Embedding)
Hitung deviasi bersih untuk masing-masing vektor:
$$\mathbf{A}_{\text{clean}} = \mathbf{A} - \mathbf{v}_{\text{null}}$$
$$\mathbf{A}_{\text{clean}} = [0.80-0.60, 0.60-0.50, 0.10-0.30, 0.20-0.55, 0.50-0.45]$$
$$\mathbf{A}_{\text{clean}} = [0.20, 0.10, -0.20, -0.35, 0.05]$$

$$\mathbf{B}_{\text{clean}} = \mathbf{B} - \mathbf{v}_{\text{null}}$$
$$\mathbf{B}_{\text{clean}} = [0.70-0.60, 0.55-0.50, 0.20-0.30, 0.30-0.55, 0.40-0.45]$$
$$\mathbf{B}_{\text{clean}} = [0.10, 0.05, -0.10, -0.25, -0.05]$$

### Langkah 2: Thresholding Deviasi Positif ($\ge t = 0.02$)
Saring elemen vektor yang memiliki deviasi di bawah $0.02$ menjadi $0.00$:
$$\tilde{\mathbf{A}} = [\max(0, 0.20), \max(0, 0.10), 0, 0, \max(0, 0.05)] = [0.20, 0.10, 0.00, 0.00, 0.05]$$
$$\tilde{\mathbf{B}} = [\max(0, 0.10), \max(0, 0.05), 0, 0, 0] = [0.10, 0.05, 0.00, 0.00, 0.00]$$

### Langkah 3: Hitung Perkalian Titik (Dot Product) $\tilde{\mathbf{A}} \cdot \tilde{\mathbf{B}}$
$$\tilde{\mathbf{A}} \cdot \tilde{\mathbf{B}} = (0.20 \times 0.10) + (0.10 \times 0.05) + (0.00 \times 0.00) + (0.00 \times 0.00) + (0.05 \times 0.00)$$
$$\tilde{\mathbf{A}} \cdot \tilde{\mathbf{B}} = 0.02 + 0.005 + 0.00 + 0.00 + 0.00 = 0.025$$

### Langkah 4: Hitung Vektor Norm $L_2$
$$\|\tilde{\mathbf{A}}\| = \sqrt{0.20^2 + 0.10^2 + 0.00^2 + 0.00^2 + 0.05^2} = \sqrt{0.04 + 0.01 + 0.0025} = \sqrt{0.0525} \approx 0.229129$$
$$\|\tilde{\mathbf{B}}\| = \sqrt{0.10^2 + 0.05^2 + 0.00^2 + 0.00^2 + 0.00^2} = \sqrt{0.01 + 0.0025} = \sqrt{0.0125} \approx 0.111803$$

### Langkah 5: Hitung Nilai TPD-Cosine Similarity
$$\text{TPD-Cosine Similarity}(\mathbf{A}, \mathbf{B}) = \frac{\tilde{\mathbf{A}} \cdot \tilde{\mathbf{B}}}{\|\tilde{\mathbf{A}}\| \|\tilde{\mathbf{B}}\|} = \frac{0.025}{0.229129 \times 0.111803} \approx 0.975915 \quad (97.59\%)$$

---

## Studi Kasus 2: Perbandingan Skor Layer 1 (Multi-Layer)
Kita menguji sebuah dokumen spreadsheet baru **`data_sks.xlsx`** terhadap **3 kandidat label pada Layer 1 (Domain)**.

* Vektor Dokumen $\mathbf{D} = [0.75, 0.42, 0.88, 0.20, 0.60]$
* Vektor Null Embedding $\mathbf{v}_{\text{null}} = [0.60, 0.50, 0.30, 0.55, 0.45]$

### Langkah 1: Bersihkan dan Saring Vektor Dokumen $\mathbf{D}$
1. **Clean:** $\mathbf{D}_{\text{clean}} = [0.15, -0.08, 0.58, -0.35, 0.15]$
2. **Thresholded ($t=0.02$):** $\tilde{\mathbf{D}} = [0.15, 0.00, 0.58, 0.00, 0.15]$
3. **Norm:** $\|\tilde{\mathbf{D}}\| = \sqrt{0.15^2 + 0.58^2 + 0.15^2} = \sqrt{0.0225 + 0.3364 + 0.0225} = \sqrt{0.3814} \approx 0.617576$

### Bagian A: Menghitung Kesamaan terhadap Domain 1 (Akademik Mahasiswa)
* $\mathbf{L}_1 = [0.70, 0.35, 0.80, 0.20, 0.55]$
1. **Clean & Thresholded:** $\tilde{\mathbf{L}}_1 = [0.10, 0.00, 0.50, 0.00, 0.10]$
2. **Norm:** $\|\tilde{\mathbf{L}}_1\| = \sqrt{0.10^2 + 0.50^2 + 0.10^2} = \sqrt{0.27} \approx 0.519615$
3. **Dot Product:** $\tilde{\mathbf{D}} \cdot \tilde{\mathbf{L}}_1 = (0.15 \times 0.10) + (0.58 \times 0.50) + (0.15 \times 0.10) = 0.32$
4. **TPD-Cosine Similarity ($s_1$):** $s_1 = \frac{0.32}{0.617576 \times 0.519615} \approx 0.997220$

### Bagian B: Menghitung Kesamaan terhadap Domain 2 (Administrasi Dosen)
* $\mathbf{L}_2 = [0.65, 0.40, 0.75, 0.20, 0.50]$
1. **Clean & Thresholded:** $\tilde{\mathbf{L}}_2 = [0.05, 0.00, 0.45, 0.00, 0.05]$
2. **Norm:** $\|\tilde{\mathbf{L}}_2\| = \sqrt{0.05^2 + 0.45^2 + 0.05^2} = \sqrt{0.0025 + 0.2025 + 0.0025} = \sqrt{0.2075} \approx 0.455522$
3. **Dot Product:** $\tilde{\mathbf{D}} \cdot \tilde{\mathbf{L}}_2 = (0.15 \times 0.05) + (0.58 \times 0.45) + (0.15 \times 0.05) = 0.276$
4. **TPD-Cosine Similarity ($s_2$):** $s_2 = \frac{0.276}{0.617576 \times 0.455522} \approx 0.981090$

### Bagian C: Menghitung Kesamaan terhadap Domain 3 (Jadwal dan SKS Perkuliahan)
* $\mathbf{L}_3 = [0.76, 0.45, 0.90, 0.20, 0.62]$
1. **Clean & Thresholded:** $\tilde{\mathbf{L}}_3 = [0.16, 0.00, 0.60, 0.00, 0.17]$
2. **Norm:** $\|\tilde{\mathbf{L}}_3\| = \sqrt{0.16^2 + 0.60^2 + 0.17^2} = \sqrt{0.4145} \approx 0.643817$
3. **Dot Product:** $\tilde{\mathbf{D}} \cdot \tilde{\mathbf{L}}_3 = (0.15 \times 0.16) + (0.58 \times 0.60) + (0.15 \times 0.17) = 0.3975$
4. **TPD-Cosine Similarity ($s_3$):** $s_3 = \frac{0.3975}{0.617576 \times 0.643817} \approx 0.999733$

---

## Studi Kasus 3: Konversi Persentase TPD-Cosine Similarity Layer 1
Kita mengonversi skor kesamaan dari Studi Kasus 2 ke persentase visual pada dashboard.

### Langkah 1: Persentase Domain 1 (Akademik Mahasiswa)
$$P_1 = s_1 \times 100\% = 0.997220 \times 100\% = 99.72\%$$

### Langkah 2: Persentase Domain 2 (Administrasi Dosen)
$$P_2 = s_2 \times 100\% = 0.981090 \times 100\% = 98.11\%$$

### Langkah 3: Persentase Domain 3 (Jadwal dan SKS Perkuliahan)
$$P_3 = s_3 \times 100\% = 0.999733 \times 100\% = 99.97\%$$

**Kesimpulan Layer 1:** Dokumen `data_sks.xlsx` diklasifikasikan ke dalam **Jadwal dan SKS Perkuliahan** dengan tingkat keyakinan **$99.97\%$**.

---

## Studi Kasus 4: Konversi Persentase TPD-Cosine Similarity Layer 2
Selanjutnya, dokumen kita evaluasi pada **Layer 2 (Detail)**.

Misalkan skor TPD-Cosine Similarity mentah hasil kalkulasi model untuk 5 kandidat label Layer 2 adalah:
1. `Transkrip Nilai Lengkap` ($s_{2,1} = 0.9312$)
2. `KRS SKS Kelas` ($s_{2,2} = 0.9482$) (Skor Tertinggi!)
3. `Daftar Dosen Pengajar` ($s_{2,3} = 0.9105$)
4. `Laporan Keuangan` ($s_{2,4} = 0.0000$) (Terfilter karena di bawah threshold)
5. `Kurikulum Jurusan` ($s_{2,5} = 0.8820$)

### Perhitungan Langkah-Demi-Langkah:
1. **Transkrip Nilai Lengkap:** $P_{2,1} = 0.9312 \times 100\% = 93.12\%$
2. **KRS SKS Kelas:** $P_{2,2} = 0.9482 \times 100\% = 94.82\%$
3. **Daftar Dosen Pengajar:** $P_{2,3} = 0.9105 \times 100\% = 91.05\%$
4. **Laporan Keuangan:** $P_{2,4} = 0.0000 \times 100\% = 0.00\%$
5. **Kurikulum Jurusan:** $P_{2,5} = 0.8820 \times 100\% = 88.20\%$

### Hasil Klasifikasi Akhir Sistem:
* **Keputusan Layer 1:** `Jadwal dan SKS Perkuliahan` ($99.97\%$)
* **Keputusan Layer 2:** `KRS SKS Kelas` ($94.82\%$)

**Output Teks di Panel Dashboard:**
`Jadwal dan SKS Perkuliahan (99.97%) ==> KRS SKS Kelas (94.82%)`

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

---

## Studi Kasus 7: Perhitungan Klasifikasi Berbasis Booster & Hierarchical Consistency
Kita mengevaluasi dokumen acak yang bernilai `Pert 9. Evaluasi Resiko.pdf` di bawah Skenario Korpus Utama.

### Data Input:
- Teks dokumen mengandung kata kunci `"risiko"`, `"ketidakpastian"`, `"manajemen risiko"`.
- Vektor kemiripan kosinus mentah Layer 2:
  - `Transkrip Nilai Lengkap` ($s_{2,1} = 0.8058$)
  - `KRS SKS Kelas` ($s_{2,2} = 0.8058$)
  - `Daftar Dosen Pengajar` ($s_{2,3} = 0.6058$)
  - `Laporan Keuangan` ($s_{2,4} = 0.7485$)
  - `Kurikulum Jurusan` ($s_{2,5} = 0.5485$)
- Vektor kemiripan kosinus mentah Layer 1:
  - `Akademik Mahasiswa` ($s_{1,1} = 0.8485$)
  - `Administrasi Dosen` ($s_{1,2} = 0.5485$)
  - `Jadwal dan SKS Perkuliahan` ($s_{1,3} = 0.7952$)

- Kata kunci booster Layer 2:
  - `Laporan Keuangan` dirangsang oleh kata kunci `"biaya"`, `"keuangan"`, `"spp"`, dst. Karena dokumen tidak mengandung kata-kata tersebut, $\text{Boost}_{2,4} = 0.0$.
  - Seluruh label Layer 2 lainnya juga tidak cocok dengan kata kunci booster masing-masing, sehingga seluruh $\text{Boost}_{2, k} = 0.0$ untuk $k = 1, \dots, 5$.

- Peta Hierarki (CHILD_TO_PARENT_MAP):
  - `Transkrip Nilai Lengkap` $\rightarrow$ `Akademik Mahasiswa`
  - `KRS SKS Kelas` $\rightarrow$ `Akademik Mahasiswa`
  - `Daftar Dosen Pengajar` $\rightarrow$ `Administrasi Dosen`
  - `Laporan Keuangan` $\rightarrow$ `Akademik Mahasiswa`
  - `Kurikulum Jurusan` $\rightarrow$ `Jadwal dan SKS Perkuliahan`

- Ambang batas ketat $\theta = 0.92$.
- Booster konsistensi hierarki $\text{Boost}_{\text{hierarchical}} = 0.30$.

---

### TAHAP 1: EVALUASI LAYER 2 (DETAIL)

Kita terapkan rumus Penyelarasan Booster & Strict Fallback Thresholding untuk masing-masing kelas Layer 2:

1. **Transkrip Nilai Lengkap:**
   - $\text{Boost}_{2,1} = 0.0$
   - $\text{Sim}_{\text{raw}, 2,1} = 0.8058 < 0.92$
   - $\text{Sim}_{\text{final}, 2,1} = 0.00 \quad (0.00\%)$

2. **KRS SKS Kelas:**
   - $\text{Boost}_{2,2} = 0.0$
   - $\text{Sim}_{\text{raw}, 2,2} = 0.8058 < 0.92$
   - $\text{Sim}_{\text{final}, 2,2} = 0.00 \quad (0.00\%)$

3. **Daftar Dosen Pengajar:**
   - $\text{Boost}_{2,3} = 0.0$
   - $\text{Sim}_{\text{raw}, 2,3} = 0.6058 < 0.92$
   - $\text{Sim}_{\text{final}, 2,3} = 0.00 \quad (0.00\%)$

4. **Laporan Keuangan:**
   - $\text{Boost}_{2,4} = 0.0$
   - $\text{Sim}_{\text{raw}, 2,4} = 0.7485 < 0.92$
   - $\text{Sim}_{\text{final}, 2,4} = 0.00 \quad (0.00\%)$

5. **Kurikulum Jurusan:**
   - $\text{Boost}_{2,5} = 0.0$
   - $\text{Sim}_{\text{raw}, 2,5} = 0.5485 < 0.92$
   - $\text{Sim}_{\text{final}, 2,5} = 0.00 \quad (0.00\%)$

**Keputusan Layer 2:**
Seluruh nilai kemiripan Layer 2 adalah $0.00\%$, sehingga keputusan label Layer 2 adalah **"Tidak Terklasifikasi"**.

---

### TAHAP 2: EVALUASI LAYER 1 (DOMAIN)

Karena keputusan Layer 2 terpilih adalah `"Tidak Terklasifikasi"`, maka tidak ada booster konsistensi hierarki yang ditambahkan ke Layer 1 ($\text{Boost}_{\text{hierarchical}, j} = 0.0$ untuk semua $j$).

Kita terapkan rumus Penyelarasan Booster & Strict Fallback Thresholding untuk masing-masing kelas Layer 1:

1. **Akademik Mahasiswa:**
   - $\text{Boost}_{\text{lexical}, 1,1} = 0.0$ (tidak ada kata kunci akademik seperti `"nim"`, `"nilai"`, dst)
   - $\text{Boost}_{\text{hierarchical}, 1,1} = 0.0$
   - Total $\text{Boost}_{1,1} = 0.0$
   - $\text{Sim}_{\text{raw}, 1,1} = 0.8485 < 0.92$
   - $\text{Sim}_{\text{final}, 1,1} = 0.00 \quad (0.00\%)$

2. **Administrasi Dosen:**
   - $\text{Boost}_{\text{lexical}, 1,2} = 0.0$
   - $\text{Boost}_{\text{hierarchical}, 1,2} = 0.0$
   - Total $\text{Boost}_{1,2} = 0.0$
   - $\text{Sim}_{\text{raw}, 1,2} = 0.5485 < 0.92$
   - $\text{Sim}_{\text{final}, 1,2} = 0.00 \quad (0.00\%)$

3. **Jadwal dan SKS Perkuliahan:**
   - $\text{Boost}_{\text{lexical}, 1,3} = 0.0$
   - $\text{Boost}_{\text{hierarchical}, 1,3} = 0.0$
   - Total $\text{Boost}_{1,3} = 0.0$
   - $\text{Sim}_{\text{raw}, 1,3} = 0.7952 < 0.92$
   - $\text{Sim}_{\text{final}, 1,3} = 0.00 \quad (0.00\%)$

**Keputusan Layer 1:**
Seluruh nilai kemiripan Layer 1 adalah $0.00\%$, sehingga keputusan label Layer 1 adalah **"Tidak Terklasifikasi"**.

---

### ANALISIS PERBAIKAN SISTEM:
Sebelum perbaikan dilakukan, dokumen `"Pert 9. Evaluasi Resiko.pdf"` dinilai memiliki kecocokan **$99.85\%$** dengan `"Akademik Mahasiswa"` dan **$80.58\%$** dengan `"Transkrip Nilai Lengkap"`. Dengan adanya rumus penyelarasan booster individual per kelas dan fallback ambang batas ketat $\theta = 0.92$, bias representasi geometris dapat disaring sepenuhnya. Hasil keputusan akhir menjadi **`Tidak Terklasifikasi` (0.00%)**, yang secara akademis sepenuhnya benar karena isi dokumen membahas manajemen risiko industri, bukan urusan akademik universitas.

---

## Studi Kasus 8: Peringkasan Dokumen Menggunakan TextRank
Kasus ini menguraikan perhitungan manual langkah-demi-langkah algoritma TextRank untuk menyaring kalimat kunci dari suatu dokumen pendek yang memiliki $M = 3$ kalimat.

### 1. Kumpulan Kalimat Input ($S$):
* $s_1$: `"Model klasifikasi otomatis membaca skripsi mahasiswa."`
* $s_2$: `"Pencarian semantik data skripsi menggunakan cosine similarity."`
* $s_3$: `"Metode klasifikasi skripsi ini melabeli data otomatis."`

### 2. Ekstraksi Kata Unik ($W(s_i)$):
* $W(s_1) = \{\text{model}, \text{klasifikasi}, \text{otomatis}, \text{membaca}, \text{skripsi}, \text{mahasiswa}\} \quad (|W(s_1)| = 6)$
* $W(s_2) = \{\text{pencarian}, \text{semantik}, \text{data}, \text{skripsi}, \text{menggunakan}, \text{cosine}, \text{similarity}\} \quad (|W(s_2)| = 7)$
* $W(s_3) = \{\text{metode}, \text{klasifikasi}, \text{skripsi}, \text{ini}, \text{melabeli}, \text{data}, \text{otomatis}\} \quad (|W(s_3)| = 7)$

Panjang logaritma kata untuk masing-masing kalimat:
* $\ln(|W(s_1)|) = \ln(6) \approx 1.7918$
* $\ln(|W(s_2)|) = \ln(7) \approx 1.9459$
* $\ln(|W(s_3)|) = \ln(7) \approx 1.9459$

### 3. Perhitungan Kesamaan Logaritma Kalimat ($\text{Sim}_{\text{leksikal}}(s_i, s_j)$):
* Irisan kata unik antara $s_1$ dan $s_2$: $W(s_1) \cap W(s_2) = \{\text{skripsi}\} \quad (\text{jumlah} = 1)$
  $$\text{Sim}(s_1, s_2) = \frac{1}{\ln(6) + \ln(7) + 1} = \frac{1}{1.7918 + 1.9459 + 1} = \frac{1}{4.7377} \approx 0.2111$$

* Irisan kata unik antara $s_1$ and $s_3$: $W(s_1) \cap W(s_3) = \{\text{klasifikasi}, \text{otomatis}, \text{skripsi}\} \quad (\text{jumlah} = 3)$
  $$\text{Sim}(s_1, s_3) = \frac{3}{\ln(6) + \ln(7) + 1} = \frac{3}{1.7918 + 1.9459 + 1} = \frac{3}{4.7377} \approx 0.6332$$

* Irisan kata unik antara $s_2$ and $s_3$: $W(s_2) \cap W(s_3) = \{\text{data}, \text{skripsi}\} \quad (\text{jumlah} = 2)$
  $$\text{Sim}(s_2, s_3) = \frac{2}{\ln(7) + \ln(7) + 1} = \frac{2}{1.9459 + 1.9459 + 1} = \frac{2}{4.8918} \approx 0.4089$$

### 4. Pembentukan Similarity Matrix:
$$\text{Sim} = \begin{pmatrix}
0.0 & 0.2111 & 0.6332 \\
0.2111 & 0.0 & 0.4089 \\
0.6332 & 0.4089 & 0.0
\end{pmatrix}$$

Jumlah baris dari similarity matrix:
* $\text{RowSum}(s_1) = 0.2111 + 0.6332 = 0.8443$
* $\text{RowSum}(s_2) = 0.2111 + 0.4089 = 0.6200$
* $\text{RowSum}(s_3) = 0.6332 + 0.4089 = 1.0421$

### 5. Pembentukan Transition Probability Matrix ($P$):
Dengan membagi elemen baris dengan jumlah barisnya, kita peroleh matriks transisi probabilitas:
$$P = \begin{pmatrix}
0.0 & 0.2500 & 0.7500 \\
0.3405 & 0.0 & 0.6595 \\
0.6076 & 0.3924 & 0.0
\end{pmatrix}$$

Transpos matriks $P^T$:
$$P^T = \begin{pmatrix}
0.0 & 0.3405 & 0.6076 \\
0.2500 & 0.0 & 0.3924 \\
0.7500 & 0.6595 & 0.0
\end{pmatrix}$$

### 6. Perhitungan Iterasi PageRank (Power Iteration):
Menggunakan damping factor $d = 0.85$ dan inisialisasi skor $\mathbf{PR}^{(0)} = \begin{pmatrix} 1.0 \\ 1.0 \\ 1.0 \end{pmatrix}$.

#### Iterasi 1:
$$\mathbf{PR}^{(1)} = (1 - d)\mathbf{1} + d \cdot P^T \mathbf{PR}^{(0)}$$
$$\mathbf{PR}^{(1)} = 0.15 \cdot \begin{pmatrix} 1.0 \\ 1.0 \\ 1.0 \end{pmatrix} + 0.85 \cdot \begin{pmatrix}
0.0 & 0.3405 & 0.6076 \\
0.2500 & 0.0 & 0.3924 \\
0.7500 & 0.6595 & 0.0
\end{pmatrix} \begin{pmatrix} 1.0 \\ 1.0 \\ 1.0 \end{pmatrix}$$
$$\mathbf{PR}^{(1)} = \begin{pmatrix} 0.15 \\ 0.15 \\ 0.15 \end{pmatrix} + 0.85 \cdot \begin{pmatrix} 0.9481 \\ 0.6424 \\ 1.4095 \end{pmatrix} = \begin{pmatrix} 0.9559 \\ 0.6960 \\ 1.3481 \end{pmatrix}$$

#### Iterasi 2:
$$\mathbf{PR}^{(2)} = (1 - d)\mathbf{1} + d \cdot P^T \mathbf{PR}^{(1)}$$
$$\mathbf{PR}^{(2)} = 0.15 \cdot \begin{pmatrix} 1.0 \\ 1.0 \\ 1.0 \end{pmatrix} + 0.85 \cdot \begin{pmatrix}
0.0 & 0.3405 & 0.6076 \\
0.2500 & 0.0 & 0.3924 \\
0.7500 & 0.6595 & 0.0
\end{pmatrix} \begin{pmatrix} 0.9559 \\ 0.6960 \\ 1.3481 \end{pmatrix}$$
$$\mathbf{PR}^{(2)} = \begin{pmatrix} 0.15 \\ 0.15 \\ 0.15 \end{pmatrix} + 0.85 \cdot \begin{pmatrix} 0.3405(0.6960) + 0.6076(1.3481) \\ 0.2500(0.9559) + 0.3924(1.3481) \\ 0.7500(0.9559) + 0.6595(0.6960) \end{pmatrix}$$
$$\mathbf{PR}^{(2)} = \begin{pmatrix} 0.15 \\ 0.15 \\ 0.15 \end{pmatrix} + 0.85 \cdot \begin{pmatrix} 1.0561 \\ 0.7680 \\ 1.1759 \end{pmatrix} = \begin{pmatrix} 1.0477 \\ 0.8028 \\ 1.1495 \end{pmatrix}$$

### 7. Hasil Akhir & Perangkingan Kalimat:
Skor akhir kalimat pada iterasi ke-2 menunjukkan tingkat pentingnya kalimat dalam dokumen:
1. Kalimat $s_3$ (Skor: $1.1495$) — *Peringkat 1*
2. Kalimat $s_1$ (Skor: $1.0477$) — *Peringkat 2*
3. Kalimat $s_2$ (Skor: $0.8028$) — *Peringkat 3*

Sistem mengambil kalimat dengan peringkat tertinggi untuk mewakili makna utama dokumen.

---

## Studi Kasus 9: Evaluasi Klasifikasi Multi-Label (Confusion Matrix + Metrik Positif & Negatif)
Kita mengevaluasi performa klasifikasi sistem untuk **1 label spesifik**: `Transkrip Nilai Lengkap`, terhadap **10 dokumen pengujian** yang memiliki ground truth (kebenaran) yang sudah diketahui.

### Data Pengujian:

| No | Dokumen | Ground Truth | Prediksi Sistem |
|----|---------|-------------|-----------------|
| 1 | `transkrip_budi.pdf` | Positif (1) | Positif (1) |
| 2 | `transkrip_ani.xlsx` | Positif (1) | Positif (1) |
| 3 | `krs_rian.pdf` | Negatif (0) | Negatif (0) |
| 4 | `dosen_hermawan.xlsx` | Negatif (0) | Negatif (0) |
| 5 | `transkrip_dewi.csv` | Positif (1) | Positif (1) |
| 6 | `keuangan_ukt_fajar.pdf` | Negatif (0) | Positif (1) |
| 7 | `transkrip_hendra.docx` | Positif (1) | Negatif (0) |
| 8 | `kurikulum_if.xlsx` | Negatif (0) | Negatif (0) |
| 9 | `transkrip_siti.pdf` | Positif (1) | Positif (1) |
| 10 | `dosen_sri_utami.csv` | Negatif (0) | Negatif (0) |

### Langkah 1: Hitung Elemen Confusion Matrix
Dari tabel di atas, kita identifikasi masing-masing elemen:
* **True Positive ($TP$):** Dokumen 1, 2, 5, 9 (Ground Truth = 1, Prediksi = 1) $\Rightarrow TP = 4$
* **False Positive ($FP$):** Dokumen 6 (Ground Truth = 0, Prediksi = 1) $\Rightarrow FP = 1$
* **True Negative ($TN$):** Dokumen 3, 4, 8, 10 (Ground Truth = 0, Prediksi = 0) $\Rightarrow TN = 4$
* **False Negative ($FN$):** Dokumen 7 (Ground Truth = 1, Prediksi = 0) $\Rightarrow FN = 1$

### Langkah 2: Hitung Precision Kelas Positif
$$\text{Precision}^{+} = \frac{TP}{TP + FP} = \frac{4}{4 + 1} = \frac{4}{5} = 0.8000 \quad (80.00\%)$$

### Langkah 3: Hitung Recall Kelas Positif (Sensitivity)
$$\text{Recall}^{+} = \frac{TP}{TP + FN} = \frac{4}{4 + 1} = \frac{4}{5} = 0.8000 \quad (80.00\%)$$

### Langkah 4: Hitung F1-Score Kelas Positif
$$\text{F1}^{+} = 2 \cdot \frac{0.8000 \times 0.8000}{0.8000 + 0.8000} = 2 \cdot \frac{0.6400}{1.6000} = 2 \times 0.4000 = 0.8000 \quad (80.00\%)$$

### Langkah 5: Hitung Precision Kelas Negatif
$$\text{Precision}^{-} = \frac{TN}{TN + FN} = \frac{4}{4 + 1} = \frac{4}{5} = 0.8000 \quad (80.00\%)$$

### Langkah 6: Hitung Recall Kelas Negatif (Specificity)
$$\text{Recall}^{-} = \text{Specificity} = \frac{TN}{TN + FP} = \frac{4}{4 + 1} = \frac{4}{5} = 0.8000 \quad (80.00\%)$$

### Langkah 7: Hitung F1-Score Kelas Negatif
$$\text{F1}^{-} = 2 \cdot \frac{0.8000 \times 0.8000}{0.8000 + 0.8000} = 0.8000 \quad (80.00\%)$$

### Langkah 8: Hitung Akurasi Keseluruhan
$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN} = \frac{4 + 4}{4 + 4 + 1 + 1} = \frac{8}{10} = 0.8000 \quad (80.00\%)$$

### Langkah 9: Hitung False Positive Rate & False Negative Rate
$$\text{FPR} = \frac{FP}{FP + TN} = \frac{1}{1 + 4} = 0.2000 \quad (20.00\%)$$
$$\text{FNR} = \frac{FN}{FN + TP} = \frac{1}{1 + 4} = 0.2000 \quad (20.00\%)$$

**Kesimpulan:** Sistem memiliki kinerja seimbang antara kelas positif dan negatif dengan F1-Score $80\%$ pada kedua arah, dan tingkat kesalahan (FPR \& FNR) masing-masing hanya $20\%$.

---

## Studi Kasus 10: Evaluasi Pencarian STKI (Precision@K, MAP, NDCG@K)
Kita mengevaluasi kualitas peringkat hasil pencarian Hybrid Retrieval (Dense BERT + BM25) menggunakan **3 kueri pengujian** dengan $K = 5$ dan ground truth yang telah disiapkan.

### Kueri Pengujian dan Ground Truth:

**Kueri 1:** `"transkrip nilai mahasiswa informatika"`
* Dokumen relevan (ground truth): $R_1 = \{D_1, D_3, D_7, D_{12}\}$ ($|R_1| = 4$)
* Hasil pencarian sistem (Top-5): $[D_1, D_5, D_3, D_7, D_9]$
* Relevansi per posisi: $[\textbf{1}, 0, \textbf{1}, \textbf{1}, 0]$

**Kueri 2:** `"daftar dosen pengajar fakultas"`
* Dokumen relevan (ground truth): $R_2 = \{D_2, D_6, D_{10}\}$ ($|R_2| = 3$)
* Hasil pencarian sistem (Top-5): $[D_2, D_6, D_4, D_{10}, D_8]$
* Relevansi per posisi: $[\textbf{1}, \textbf{1}, 0, \textbf{1}, 0]$

**Kueri 3:** `"rencana studi KRS semester genap"`
* Dokumen relevan (ground truth): $R_3 = \{D_4, D_{11}\}$ ($|R_3| = 2$)
* Hasil pencarian sistem (Top-5): $[D_8, D_4, D_{11}, D_1, D_5]$
* Relevansi per posisi: $[0, \textbf{1}, \textbf{1}, 0, 0]$

---

### TAHAP A: HITUNG PRECISION@5

#### Kueri 1:
$$\text{Precision@5}(q_1) = \frac{|\{D_1, D_3, D_7\}|}{5} = \frac{3}{5} = 0.6000 \quad (60.00\%)$$

#### Kueri 2:
$$\text{Precision@5}(q_2) = \frac{|\{D_2, D_6, D_{10}\}|}{5} = \frac{3}{5} = 0.6000 \quad (60.00\%)$$

#### Kueri 3:
$$\text{Precision@5}(q_3) = \frac{|\{D_4, D_{11}\}|}{5} = \frac{2}{5} = 0.4000 \quad (40.00\%)$$

---

### TAHAP B: HITUNG MEAN AVERAGE PRECISION (MAP)

#### Average Precision Kueri 1:
Dokumen relevan ditemukan di posisi $k = 1, 3, 4$:
* $\text{Precision@1} = \frac{1}{1} = 1.0000$
* $\text{Precision@3} = \frac{2}{3} = 0.6667$
* $\text{Precision@4} = \frac{3}{4} = 0.7500$
$$\text{AP}(q_1) = \frac{1}{4}(1.0000 + 0.6667 + 0.7500) = \frac{2.4167}{4} = 0.6042$$

#### Average Precision Kueri 2:
Dokumen relevan ditemukan di posisi $k = 1, 2, 4$:
* $\text{Precision@1} = \frac{1}{1} = 1.0000$
* $\text{Precision@2} = \frac{2}{2} = 1.0000$
* $\text{Precision@4} = \frac{3}{4} = 0.7500$
$$\text{AP}(q_2) = \frac{1}{3}(1.0000 + 1.0000 + 0.7500) = \frac{2.7500}{3} = 0.9167$$

#### Average Precision Kueri 3:
Dokumen relevan ditemukan di posisi $k = 2, 3$:
* $\text{Precision@2} = \frac{1}{2} = 0.5000$
* $\text{Precision@3} = \frac{2}{3} = 0.6667$
$$\text{AP}(q_3) = \frac{1}{2}(0.5000 + 0.6667) = \frac{1.1667}{2} = 0.5834$$

#### Hitung MAP:
$$\text{MAP} = \frac{1}{3}(0.6042 + 0.9167 + 0.5834) = \frac{2.1043}{3} = 0.7014 \quad (70.14\%)$$

---

### TAHAP C: HITUNG NDCG@5

#### NDCG@5 Kueri 1:
Relevansi hasil sistem: $[1, 0, 1, 1, 0]$

**DCG@5:**
$$\text{DCG@5} = \frac{2^1-1}{\log_2(2)} + \frac{2^0-1}{\log_2(3)} + \frac{2^1-1}{\log_2(4)} + \frac{2^1-1}{\log_2(5)} + \frac{2^0-1}{\log_2(6)}$$
$$= \frac{1}{1.0000} + \frac{0}{1.5850} + \frac{1}{2.0000} + \frac{1}{2.3219} + \frac{0}{2.5850}$$
$$= 1.0000 + 0.0000 + 0.5000 + 0.4307 + 0.0000 = 1.9307$$

**IDCG@5** (urutan ideal: $[1, 1, 1, 1, 0]$ karena $|R_1| = 4$):
$$\text{IDCG@5} = \frac{1}{1.0000} + \frac{1}{1.5850} + \frac{1}{2.0000} + \frac{1}{2.3219} + \frac{0}{2.5850}$$
$$= 1.0000 + 0.6309 + 0.5000 + 0.4307 + 0.0000 = 2.5616$$

$$\text{NDCG@5}(q_1) = \frac{1.9307}{2.5616} = 0.7537 \quad (75.37\%)$$

#### NDCG@5 Kueri 2:
Relevansi hasil sistem: $[1, 1, 0, 1, 0]$

**DCG@5:**
$$\text{DCG@5} = \frac{1}{1.0000} + \frac{1}{1.5850} + \frac{0}{2.0000} + \frac{1}{2.3219} + \frac{0}{2.5850}$$
$$= 1.0000 + 0.6309 + 0.0000 + 0.4307 + 0.0000 = 2.0616$$

**IDCG@5** (urutan ideal: $[1, 1, 1, 0, 0]$ karena $|R_2| = 3$):
$$\text{IDCG@5} = \frac{1}{1.0000} + \frac{1}{1.5850} + \frac{1}{2.0000} + \frac{0}{2.3219} + \frac{0}{2.5850}$$
$$= 1.0000 + 0.6309 + 0.5000 + 0.0000 + 0.0000 = 2.1309$$

$$\text{NDCG@5}(q_2) = \frac{2.0616}{2.1309} = 0.9675 \quad (96.75\%)$$

#### NDCG@5 Kueri 3:
Relevansi hasil sistem: $[0, 1, 1, 0, 0]$

**DCG@5:**
$$\text{DCG@5} = \frac{0}{1.0000} + \frac{1}{1.5850} + \frac{1}{2.0000} + \frac{0}{2.3219} + \frac{0}{2.5850}$$
$$= 0.0000 + 0.6309 + 0.5000 + 0.0000 + 0.0000 = 1.1309$$

**IDCG@5** (urutan ideal: $[1, 1, 0, 0, 0]$ karena $|R_3| = 2$):
$$\text{IDCG@5} = \frac{1}{1.0000} + \frac{1}{1.5850} + \frac{0}{2.0000} + \frac{0}{2.3219} + \frac{0}{2.5850}$$
$$= 1.0000 + 0.6309 + 0.0000 + 0.0000 + 0.0000 = 1.6309$$

$$\text{NDCG@5}(q_3) = \frac{1.1309}{1.6309} = 0.6934 \quad (69.34\%)$$

#### Rata-Rata NDCG@5:
$$\overline{\text{NDCG@5}} = \frac{0.7537 + 0.9675 + 0.6934}{3} = \frac{2.4146}{3} = 0.8049 \quad (80.49\%)$$

---

### Analisis Hasil Evaluasi STKI:

| Metrik | Nilai | Interpretasi |
|--------|-------|-------------|
| MAP | $70.14\%$ | Kualitas peringkat pencarian baik secara konsisten |
| $\overline{\text{NDCG@5}}$ | $80.49\%$ | Dokumen relevan cenderung muncul di posisi atas |
| Precision@5 (rata-rata) | $53.33\%$ | Lebih dari separuh hasil Top-5 adalah relevan |

Hasil ini membuktikan bahwa Hybrid Retrieval (Dense BERT $70\%$ + Sparse BM25 $30\%$) mampu menempatkan dokumen relevan di peringkat atas secara konsisten dengan MAP di atas $70\%$ dan NDCG di atas $80\%$, yang menurut standar evaluasi IR modern (Manning et al., 2008) tergolong performa yang sangat layak untuk sistem pencarian berskala korpus 1000 dokumen.

