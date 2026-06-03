# [L3] THEORY & PRACTICE: HYBRID FUSION EQUATION

*Hybrid Fusion* memecahkan dualitas antara akurasi *exact-match* (N-Gram tekstual leksikal via BM25) dan interpretasi laten *semantic meaning* (Dense Vector *Cosine*). Kendala utama dalam menyatukan dua entitas independen ini adalah ketidakcocokan spektrum skala dasar: skor BM25 tidak memilik rentang batas atas mutlak (skor dapat berkisar antara $0$ hingga tak terbatas), sedangkan skor *Cosine* secara inheren dibatasi dalam rentang absolut $[-1, 1]$. Tanpa peredaman asimetris, sinyal probabilistik TF-IDF akan menelan mentah-mentah nilai Dense vektor yang rentangnya uniter.

Oleh karenanya, *Practice* mendikte proses *Min-Max Normalization* terisolasi pada kedua kanal skor sebelum diikat secara linear menggunakan konstanta perantara penyeimbang probabilitas (Fusion-Alpha $\alpha$).

### 1. Landasan Matematis: Normalisasi & Skala Penyatuan 

**A. Min-Max Normalization** untuk skala BM25:
$$ \hat{S}_{BM25} = \frac{S_{BM25} - \min(S_{BM25})}{\max(S_{BM25}) - \min(S_{BM25}) + \epsilon} $$
*(Rentang hasil: $0$ sampai $1$)*

**B. Interpolasi Hybrid (Fusion Equation):**
Sistem memberlakukan fusi linear tunggal untuk mengagregasi skor akhir. Nilai empiris dari STKI menetapkan titik $\alpha = 0.70$ sebagai nilai optimal ($70\%$ beban Dense semantik, $30\%$ sentuhan leksikal teknis).

$$ S_{final} = (\alpha \times \hat{S}_{Dense}) + ((1 - \alpha) \times \hat{S}_{BM25}) $$

### 2. Implementasi Source Code

*Source File:* `TKI/app_web.py` (Konteks Ekstraksi `calculate_hybrid_score`)
Karena perhitungan hibrida dieksekusi per satu-kueri-banyak-dokumen (1:N), vektorisasi *array* via Numpy mutlak diberlakukan untuk mengeksekusi normalisasi serentak tanpa *for-loop* yang melumpuhkan performa *runtime*.

```python
# [Konteks Logika Teras dari modul Retrieval Backend]
def execute_hybrid_search(query_vector, bm25_scores, alpha_dense=0.70):
    # 1. Asumsi bm25_scores dan dense_scores adalah list/array numpy
    dense_scores = np.array(dense_scores_raw)
    sparse_scores = np.array(bm25_scores)
    
    # 2. Min-Max Normalizer (Mencegah deviasi NaN dengan epsilon kecil)
    epsilon = 1e-9
    if np.max(sparse_scores) > np.min(sparse_scores):
        sparse_norm = (sparse_scores - np.min(sparse_scores)) / (np.max(sparse_scores) - np.min(sparse_scores) + epsilon)
    else:
        sparse_norm = np.zeros_like(sparse_scores)
        
    if np.max(dense_scores) > np.min(dense_scores):
        dense_norm = (dense_scores - np.min(dense_scores)) / (np.max(dense_scores) - np.min(dense_scores) + epsilon)
    else:
        dense_norm = np.zeros_like(dense_scores)
        
    # 3. Alpha-Weighted Fusion O(1) Vectorization
    final_hybrid_scores = (alpha_dense * dense_norm) + ((1.0 - alpha_dense) * sparse_norm)
    
    return final_hybrid_scores
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Saturasi Kosong (Min-Max Collapse):** Jika seluruh dokumen dalam indeks memiliki skor BM25 $0$ (kasus tidak ada irisan literal sama sekali), fungsi Min-Max secara brutal akan mendevaluasi seluruh himpunan menjadi *array zeros*, memaksa *Hybrid Equation* menanggung $100\%$ determinisme pada pundak skor Dense meskipun rumusnya adalah $70\%$. 
- **Mitigasi:** Variabel Epsilon ($\epsilon = 1e-9$) berfungsi sebagai perisai dari `ZeroDivisionError` pada *denominator*, menghasilkan kebisuan aman untuk skor *Sparse* sementara vektor tetap mengkalkulasi matriks *Dense* secara fungsional.

---
*Konteks: Eksekusi L3 dari [[L2_HYBRID_SEARCH]]*
