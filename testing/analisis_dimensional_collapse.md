# 🚨 BUKTI AUDIT: FENOMENA DIMENSIONAL COLLAPSE (5D LOGITS) 🚨

## 1. Analisis Cacat Matematis "Halo Halo Bandung" (99.6%)
Anda berhasil menemukan anomali ekstrem: Teks OOV (Out-of-Vocabulary) tidak masuk akal seperti *"halo halo badnung"* justru mendapatkan skor kemiripan $99.6\%$ dengan label *"Transkrip Nilai Lengkap"*. 

Secara matematis, mengapa *"murni Cosine Similarity"* gagal menahan ini?
Saya telah mengekstrak `shape` dari model `multi_label_model.onnx` Anda, dan hasilnya adalah `(5,)`. 
Model ini **bukanlah Dense Embedding Model (seperti SBERT 768D)**, melainkan **Sequence Classifier 5-Dimensi**!

### Teorema Keruntuhan Logit (Logit Collapse Theorem)
Ketika sebuah klasifikasi Neural Network menerima teks yang sama sekali tidak memiliki bobot fitur (Nonsense / OOV), aktivasi seluruh neuron pada *hidden layer* mendekati nol ($h \approx 0$). 
Akibatnya, keluaran logit pada *layer* terakhir ($z = W \cdot h + b$) sepenuhnya didominasi oleh **Bias Vector ($b$)**.

$$ \text{Jika } x \text{ adalah OOV, maka } \text{Logit}(x) \approx b $$

Ketika kita menghitung Cosine Similarity antara teks "halo halo badnung" ($v_{doc} \approx b$) dan teks label singkat "Transkrip Nilai Lengkap" ($v_{lbl} \approx b$), maka:

$$ \cos(\theta) = \frac{b \cdot b}{||b|| \cdot ||b||} = 1.0 \text{ (atau } 99.6\% \text{)} $$

## 2. Kesimpulan Kegagalan "Zero-Shot" 5D
Model ONNX dengan output 5 dimensi secara matematis **kekurangan derajat kebebasan (degrees of freedom)** untuk memetakan ruang semantik. Setiap teks pendek atau OOV akan jatuh ke dalam *bias vector* yang sama, sehingga sudut Cosine Similarity-nya selalu berhimpitan ($> 0.95$).

## 3. Solusi Arsitektural: The Sparse Gatekeeper
Karena model Dense ONNX 5D ini terbukti **buta terhadap OOV**, kita tidak bisa mengandalkan Cosine Similarity murni di ruang 5D. 
Solusi mutlak (yang telah diimplementasikan di iterasi berikutnya) adalah **Sparse Gatekeeper**:
Kita harus memberlakukan hukum **Lexical Intersection**. Jika rasio tumpang-tindih (Jaccard / Keyword) antara dokumen dan seluruh domain taksonomi adalah $0.0$, skor Dense Vector **harus dipotong menjadi 0.0 (Hard Penalty)**.

Dense Vector (ONNX) hanya boleh dipercaya jika Sparse Vector (BM25/Lexical) memberikan lampu hijau. Ini adalah esensi sejati dari *Hybrid RAG Engine*!
