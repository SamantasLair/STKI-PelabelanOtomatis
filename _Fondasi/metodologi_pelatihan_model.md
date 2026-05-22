# Metodologi Pelatihan Model (Fine-Tuning BERT) & MLOps
**Dokumen Fondasi Akademik - Spesifikasi Data Science & Model Training**

Dokumen ini menjelaskan spesifikasi arsitektur *hyperparameter*, fungsi kerugian (*loss function*), dan strategi evaluasi metrik untuk melatih ulang (*fine-tuning*) model Transformer (`BERT-Mini`) pada tugas klasifikasi dokumen multi-label akademik berskala besar.

---

## 1. Spesifikasi Hyperparameter Fine-Tuning
Dalam melatih arsitektur Transformer, pengaturan parameter sangat sensitif dan berdampak langsung pada terhindarnya model dari *catastrophic forgetting* (merusak bobot asli dari prapelatihan). Berdasarkan makalah asli BERT (Devlin et al., 2018), sistem menggunakan konfigurasi berikut:

* **Optimizer:** AdamW (*Adam with Weight Decay*)
* **Learning Rate (LR):** $3 \times 10^{-5}$ ($3e-5$). Nilai ini berada di titik *sweet spot* untuk memastikan model belajar fitur akademik tanpa menghapus pengetahuan kebahasaan dasarnya.
* **Batch Size:** $32$. Ukuran batch yang cukup besar untuk meminimalkan *stochastic noise* selama penurunan gradien.
* **Epochs:** $4$. Melatih lebih dari 5 epoch pada data multi-label teks pendek/abstrak berisiko tinggi menyebabkan *overfitting*.
* **Weight Decay ($\lambda$):** $0.01$. Berfungsi sebagai regularisasi L2 untuk mencegah bobot model menjadi terlalu besar dan hanya menghafal sampel mayoritas.
* **Warmup Ratio:** $10\%$ ($0.1$). Nilai LR akan dinaikkan perlahan dari $0$ ke $3e-5$ pada 10% langkah pertama untuk menjaga stabilitas pelatihan awal.
* **Random Seed:** 42. Digunakan untuk memastikan seluruh pembagian data (*data splitting*) dan inisialisasi bobot dapat direproduksi (*reproducible*) dengan hasil yang konsisten.

---

## 2. Fungsi Loss Klasifikasi Multi-Label (BCEWithLogitsLoss)
Sistem ini memecahkan masalah **Multi-Label Classification** (di mana satu dokumen bisa memiliki lebih dari 1 label secara bersamaan, misalnya "Transkrip" dan "Akademik Mahasiswa"). Oleh karena itu, kita tidak boleh menggunakan *Softmax* atau *CrossEntropyLoss* standar, melainkan **Binary Cross Entropy with Logits Loss (BCEWithLogitsLoss)**.

Fungsi ini mengubah masalah menjadi $N$ buah klasifikasi biner yang independen (satu untuk setiap kelas/label), menerapkan fungsi sigmoid $\sigma(x)$, lalu menghitung *Cross Entropy*:

$$\mathcal{L} = -\frac{1}{N} \sum_{i=1}^{N} \left[ y_i \cdot \log(\sigma(x_i)) + (1 - y_i) \cdot \log(1 - \sigma(x_i)) \right]$$

### Deskripsi Variabel:
* $\mathcal{L}$: Nilai *loss* keseluruhan.
* $N$: Jumlah total label kandidat.
* $y_i$: *Ground truth* / kebenaran biner (1 jika dokumen memiliki label $i$, 0 jika tidak).
* $x_i$: Output *logit* mentah dari model BERT sebelum aktivasi.
* $\sigma(x_i) = \frac{1}{1 + e^{-x_i}}$: Fungsi aktivasi Sigmoid untuk mengonversi *logit* menjadi probabilitas $[0, 1]$.

Dengan fungsi ini, jika model mendeteksi kehadiran Label A, hal itu tidak akan mengurangi probabilitas kehadiran Label B.

---

## 3. Strategi Pembagian Dataset (Data Splitting)
Untuk memastikan model dapat divalidasi dengan adil dan terhindar dari bias data *training*:
1. **Rasio Pembagian:** Sistem menggunakan rasio **80:20** ($80\%$ data digunakan untuk pelatihan/Train, $20\%$ digunakan untuk pengujian/Test).
2. **Transformasi Biner:** Seluruh susunan label string dikonversi menjadi matriks biner ortogonal menggunakan `MultiLabelBinarizer` dari Scikit-Learn sebelum proses pembelajaran dimulai.

---

## 4. Evaluasi Global: Metrik Positif, Negatif, dan Akurasi Multi-Label
Karena setiap label dievaluasi sebagai kasus biner ($1$ atau $0$), maka sistem menghitung metrik performa (*Precision*, *Recall*, *F1-Score*) secara terpisah untuk dua arah:
1. **Arah Positif (Kemampuan menemukan label yang benar):** Fokus pada meminimalkan *False Positives* (salah tempel label).
2. **Arah Negatif (Kemampuan menolak label yang salah):** Fokus pada menjaga *Specificity* agar dokumen tidak sembarangan dilabeli label yang tidak relevan.

Selain itu, karena jumlah dokumen di tiap kelas tidak seimbang, evaluasi sistem diukur menggunakan **Classification Report Global**, yang memungkinkan kita melihat performa setiap kelas individu secara objektif tanpa bias ke arah kelas mayoritas. Akurasi akhir sistem didefinisikan menggunakan **Exact Match Ratio**, di mana sebuah prediksi dianggap "Benar" (Akurat) HANYA jika susunan seluruh label yang diprediksi untuk satu dokumen cocok 100% secara mutlak dengan *ground truth*-nya.
