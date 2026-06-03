# [L3] THEORY & PRACTICE: 12 QA METRICS THEORY

Keabsahan ilmiah dari sistem klasifikasi dan *Hybrid Search* STKI bertumpu pada pondasi 12 skalar Metrik Evaluasi *Information Retrieval*. Sistem menolak evaluasi parsial (seperti hanya mengandalkan akurasi) karena akurasi gagal mempresentasikan kegagalan asimetris dalam dataset yang tidak seimbang (*Imbalanced Corpus*).

Secara teoretis, metrik evaluasi didelegasikan menjadi dua zona pembuktian absolut:
1. **Set Metrik Klasifikasi Biner Dasar (Precision, Recall, F1, Fall-out, Miss Rate):** Mengukur kemampuan ekuivalensi sistem terhadap kemurnian himpunan jawaban, tidak mempedulikan urutan baris hasil.
2. **Set Metrik Sensitivitas Rangking (MRR, MAP, NDCG, Bpref, R-Precision, ERR, MFRR):** Mengukur kecerdasan posisi *ranking*. Dokumen relevan di posisi #1 diberi bobot pahala yang secara eksponensial lebih tinggi daripada dokumen relevan di posisi #10.

### 1. Landasan Matematis: Metrik Krusial

**A. Normalized Discounted Cumulative Gain (NDCG)**
Fungsi komputasi yang memberikan sanksi logaritmik terhadap dokumen relevan yang terlempar ke bawah. Berbeda dengan metrik biner konvensional, NDCG memungkinkan sistem dinilai di dalam derajat relevansi (*graded relevance*).
$$ DCG_p = \sum_{i=1}^{p} \frac{rel_i}{\log_2(i + 1)} $$
$$ NDCG_p = \frac{DCG_p}{IDCG_p} $$
*(Di mana IDCG adalah skenario ideal di mana seluruh dokumen diletakkan pada posisi kebenaran absolut tertinggi).*

**B. Expected Reciprocal Rank (ERR)**
Fungsi model kaskade probabilitas *user behaviour*. Jika dokumen di posisi pertama sangat memuaskan, probabilitas sistem untuk dinilai baik di bawahnya otomatis meredup secara kaskade (mengasumsikan *user* tidak lagi peduli pada posisi bawah).
$$ ERR = \sum_{r=1}^{n} \frac{1}{r} P(user\_stops\_at\_r) $$

### 2. Implementasi Source Code

*Source File:* `_Quality_Assurance/qa_engine.py` (Representatif)
Karena sifat *Black-Box* dari L2 QA, sistem skoring berjalan sebagai entitas matematika murni memakan larik hasil tebakan sistem vs korpus *Ground Truth*.

```python
import math

def calculate_ndcg(retrieved_relevance_scores, k=10):
    # retrieved_relevance_scores array biner/skalar dari posisi 1 s.d k
    dcg = 0.0
    for i, rel in enumerate(retrieved_relevance_scores[:k]):
        # Penalitas eksponensial menggunakan log basis 2
        dcg += rel / math.log2(i + 1 + 1)
        
    ideal_scores = sorted(retrieved_relevance_scores, reverse=True)
    idcg = 0.0
    for i, rel in enumerate(ideal_scores[:k]):
        idcg += rel / math.log2(i + 1 + 1)
        
    if idcg == 0:
        return 0.0
        
    return dcg / idcg
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Saturasi Ketersediaan Klasifikasi Multilabel:** Dalam model taksonomi himpunan beririsan (*Venn Diagram*), *Ground Truth* seringkali lebih dari satu per dokumen. Menentukan *Binary Relevance* (Benar/Salah) untuk metrik dasar menjadi bias jika sistem hanya berhasil menebak 1 dari 3 topik *Ground Truth*.
- **Mitigasi:** Arsitektur skoring STKI memodifikasi relasi biner murni dengan relasi toleransi parsial pada *Bpref* dan *R-Precision*, di mana bobot diberikan secara proporsional sesuai rasio irisan takson yang berhasil diterbak versus korpus ideal, lalu nilai pecahan itu direkatkan ke dalam kalkulasi matriks MRR (*Mean Reciprocal Rank*).

---
*Konteks: Eksekusi L3 dari [[L2_QA_EVALUATION]]*
