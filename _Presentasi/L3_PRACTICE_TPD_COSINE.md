# [L3] THEORY & PRACTICE: TPD COSINE SIMILARITY

Perhitungan jarak antara ruang vektor dokumen dengan ruang vektor kueri dalam ekosistem STKI dimandatkan murni pada metrik komparatif sudut dimensi geometri hiper, yang secara formal disebut *Cosine Similarity*. Versi terdahulu dari STKI bereksperimen dengan metode TPD (*Targeted Penalty Distance*), yang secara paksa memberikan batas `v_null` untuk mendiskon vektor statis. Namun, temuan diagnostik membuktikan bahwa intervensi heuristik buatan tersebut menyebabkan *Collapse Thresholding* massal—dokumen dengan keragaman jauh malah menerima skor konvergen yang seragam di angka ~86%.

Oleh karenanya, *Practice* terkini menegaskan kembali ortodoksi *Pure Cosine Similarity* tanpa distorsi buatan, melempar filter penolakan (*rejection filter*) keluar dari fungsi hitung, dan menempatkannya ke zona logika fusi.

### 1. Landasan Matematis: Pure Cosine Angle

Formula yang diaplikasikan untuk kemiripan dua vektor Dense ($V_A, V_B$) adalah rasio dari *Dot Product* melawan *Euclidean Magnitude* dari kedua entitas:

$$ \text{Sim}(V_A, V_B) = \cos(\theta) = \frac{V_A \cdot V_B}{\|V_A\|_2 \|V_B\|_2} = \frac{\sum_{i=1}^{n} {A_i B_i}}{\sqrt{\sum_{i=1}^{n} A_i^2} \sqrt{\sum_{i=1}^{n} B_i^2}} $$

Fungsi dijamin memancarkan skala ekuivalensi absolut pada ruang vektor ternormalisasi: rentang skor semantik murni dari $[-1, 1]$.

### 2. Implementasi Source Code

*Source File:* `TKI/app_web.py`
Fungsi komputasi didelegasikan secara total pada perakitan biner linier *NumPy* di tingkat sistem operasi dasar (O.S C-Library). Operasi iteratif Python (`for` loops) dilarang mutlak untuk proses ini.

```python
def get_cosine_similarity(v1, v2):
    # [FIXED] Pure Cosine Similarity
    # Pemusnahan v_null thresholding yang terbukti memicu Collapse Thresholding
    # di mana seluruh dokumen mendapatkan kemiripan sama persis (contoh: 86.3%).
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
        
    return float(np.dot(v1, v2) / (norm_v1 * norm_v2))
```

### 3. Batas Eksekusi & Mitigasi Limit

- **CPU Saturation di Vektor Berskala O(N):** *Dot product* dan operasi *Norm* sangat rentan membekukan sirkuit sinkron *Frontend* jika dilakukan berurut untuk 100,000 dokumen korpus saat kueri masuk.
- **Mitigasi:** Operasi ini hanya difungsikan untuk pencarian dinamis (kueri *runtime* tak terprediksi) dan proses *Taxonomy Relabeling* di *Back-Office*. Beban perhitungan diimbangi dengan *Semantic In-Memory Cache* yang mencegah *bottleneck* input/output dari *disk* yang akan menghancurkan keuntungan waktu dari metode `np.dot` C-Library.

---
*Konteks: Eksekusi L3 dari [[L2_HYBRID_SEARCH]]*
