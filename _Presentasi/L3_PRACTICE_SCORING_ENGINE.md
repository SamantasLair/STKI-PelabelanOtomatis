# [L3] THEORY & PRACTICE: SCORING ENGINE IMPLEMENTATION

Entitas *Scoring Engine* beroperasi sebagai penterjemah teori matematis L3 ke dalam orkestrasi skrip Python terisolasi. Arsitektur melarang keras penyatuan mesin evaluasi dengan pipa *Runtime* produksi (aplikasi utama). Hal ini bertujuan untuk memproteksi siklus memori API *Information Retrieval* dari beban *cross-reference matrix* O(N*M) di mana mesin harus mengecek setiap kemunculan dokumen terhadap kamus *Ground Truth Benchmark*.

Prosedur evaluasi dibangkitkan pada interval audit, mengonsumsi korpus sampel secara independen dan menyemburkan laporannya secara *headless* via log *telemetry matrix*.

### 1. Landasan Matematis: Penurunan Precision & Recall

Sebelum skalar pangkat metrik lanjutan dieksekusi, matriks presisi biner diekstraksi terlebih dahulu sebagai *Foundation Baseline*:
- **Precision:** $P = \frac{TP}{TP + FP}$
- **Recall:** $R = \frac{TP}{TP + FN}$
- **F1-Score:** Harmonic Mean dari Precision dan Recall.

Kesalahan terbesar *Information Retrieval System* adalah mengejar nilai *Recall* absolut dengan memuntahkan setiap data beririsan kecil (*False Positives*), yang pada gilirannya menghancurkan matriks *Precision*. *Scoring Engine* dirancang menyingkap anomali saturasi tersebut secara lugas.

### 2. Implementasi Source Code

*Source File:* `_Quality_Assurance/metrics_executor.py` (Representatif)
Berikut adalah kode perakitan metrik gabungan yang diekstraksi secara sekuensial. Mesin me-loop himpunan prediktif dari *Query Response* untuk menumbuknya ke blok asuransi.

```python
def calculate_precision_recall_f1(retrieved_docs, relevant_docs):
    # retrieved_docs: list ID dokumen hasil tebakan mesin hybrid
    # relevant_docs: set() Ground Truth ID
    
    retrieved_set = set(retrieved_docs)
    relevant_set = set(relevant_docs)
    
    if not retrieved_set or not relevant_set:
        return 0.0, 0.0, 0.0
        
    true_positives = len(retrieved_set.intersection(relevant_set))
    false_positives = len(retrieved_set - relevant_set)
    false_negatives = len(relevant_set - retrieved_set)
    
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    
    f1_score = 0.0
    if precision + recall > 0:
        f1_score = 2 * (precision * recall) / (precision + recall)
        
    return precision, recall, f1_score
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Korpus Skala Besar dan Latensi O(N*M):** *Cross-referencing* setiap kueri dengan 10.000 vektor *Ground Truth* membutuhkan perulangan ganda matriks yang fatal jika diaplikasikan tanpa pra-pengelompokan.
- **Mitigasi:** Mesin skoring STKI tidak memanggil fungsi pencarian asinkron satu per satu pada tahap kalkulasi QA. Sebaliknya, prediksi indeks pencarian diturunkan (*dumped*) ke dalam representasi *SQLite Cache*, yang kemudian di-*batch processing* dengan metode *Map-Reduce* parsial, menekan latensi operasional mesin QA dari hitungan jam menjadi detik.

---
*Konteks: Eksekusi L3 dari [[L2_QA_EVALUATION]]*
