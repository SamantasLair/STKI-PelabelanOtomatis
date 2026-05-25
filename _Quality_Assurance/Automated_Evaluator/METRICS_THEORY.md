# Automated Evaluation Engine (Industry Standard)

Sistem evaluasi otomatis ini bertugas untuk mengukur kelayakan sistem pencarian (Information Retrieval) dan klasifikasi (Zero-Shot) berdasarkan metrik standar industri berskala produksi (Enterprise).

## Metrik Industri yang Diterapkan

### 1. Mean Reciprocal Rank (MRR)
MRR mengukur seberapa cepat sistem dapat menemukan dokumen relevan pertama (Top-1).
$$ \text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i} $$
Di mana $\text{rank}_i$ adalah posisi dokumen relevan pertama untuk kueri ke-$i$. Semakin mendekati 1, semakin baik.

### 2. Precision at K (P@K)
Mengukur rasio dokumen relevan dalam Top-$K$ hasil pencarian.
$$ P@K = \frac{\text{Jumlah dokumen relevan di Top-}K}{K} $$
Bermanfaat untuk mengukur kelayakan sistem rekomendasi.

### 3. Recall at K (R@K)
Mengukur kemampuan sistem menemukan semua dokumen relevan dari keseluruhan *database*.
$$ R@K = \frac{\text{Jumlah dokumen relevan di Top-}K}{\text{Total dokumen relevan di DB}} $$

### 4. Normalized Discounted Cumulative Gain (NDCG)
Berbeda dengan Precision yang bersifat biner, NDCG menghargai *ranking*. Dokumen relevan yang berada di peringkat 1 memberikan nilai lebih tinggi daripada di peringkat 10.
$$ \text{DCG}_p = \sum_{i=1}^{p} \frac{rel_i}{\log_2(i + 1)} $$
$$ \text{NDCG}_p = \frac{\text{DCG}_p}{\text{IDCG}_p} $$
*(Di mana IDCG adalah DCG Ideal yang tersusun sempurna secara menurun).*

## Alur Kerja Sistem Evaluasi
1. Sistem menarik dataset standar (Ground Truth).
2. Mengeksekusi kueri menggunakan `Hybrid Engine` (Dense + Sparse).
3. Mengkalkulasi metrik matematika secara otomatis.
4. Memberikan status **[PASS]** atau **[FAIL]** berdasarkan ambang batas kelayakan produksi ($>80\%$).
