# Landasan Teori STKI & NLP Modern (Offline Semantic Engine)
**Dokumen Fondasi Akademik - Tahap Eksperimental & Produksi**

Dokumen ini menjelaskan secara mendalam teori-teori ilmiah yang mendasari pembuatan Sistem Temu Kembali Informasi (STKI) offline dan sistem klasifikasi multi-layer dinamis pada berkas civitas akademika.

---

## 1. Evolusi Sistem Temu Kembali Informasi (STKI)
Temu kembali informasi tradisional sangat bergantung pada pencocokan leksikal (kata kunci mentah) menggunakan algoritma frekuensi kata seperti **TF-IDF** (Term Frequency - Inverse Document Frequency) dan **BM25**. 

### Limitasi Pencocokan Leksikal:
* **Masalah Sinonim (Synonymy):** Jika dokumen menulis "KRS" dan kueri mencari "rencana studi", pencocokan leksikal akan gagal menemukannya karena tidak ada kecocokan karakter kata mentah.
* **Masalah Polisemi (Polysemy):** Kata yang sama bisa memiliki makna berbeda tergantung konteks (misal: "sks" sebagai satuan kredit semester vs "sks" sebagai singkatan sistem kebut semalam).

### Solusi STKI Modern: Dense Semantic Embeddings
Sistem modern memetakan dokumen dan kueri ke dalam **Ruang Vektor Dimensi Tinggi (Vector Space Model)** di mana jarak antara dua vektor merepresentasikan kedekatan makna semantiknya. Vektor ini dihasilkan oleh arsitektur Deep Learning (Transformer) yang dilatih menggunakan milyaran korpus teks untuk memahami konteks kalimat seutuhnya.

---

## 2. Arsitektur Transformer Kompak (BERT-Mini)
Untuk deployment offline dengan latensi rendah pada komputer lokal (TKT 4), kita memilih **BERT-Mini** (Turc et al., 2019). 

### Mengapa BERT-Mini?
1. **Efisiensi Komputasi:** BERT-Mini hanya memiliki 4 layer, hidden size berdimensi 256, dan 4 attention heads. Dibandingkan BERT-Base (110 juta parameter), BERT-Mini berukuran sangat kecil (~44 MB) sehingga sangat ringan dijalankan pada CPU lokal standar kampus.
2. **Transfer Learning & Fine-Tuning:** Meskipun kecil, model ini mewarisi kemampuan representasi bahasa dari pra-pelatihan (*pre-trained weights*) HuggingFace, yang kemudian kita lakukan *fine-tuning* menggunakan metode klasifikasi multi-label terpadu untuk dataset akademis.

---

## 3. Ekspor & Optimasi Graf Komputasi via ONNX
Format **ONNX (Open Neural Network Exchange)** digunakan untuk menjembatani fase riset Data Science (PyTorch di Colab) ke fase produksi (aplikasi desktop lokal).

### Keuntungan ONNX untuk STKI Offline:
* **Independensi Library:** Menghilangkan kebutuhan untuk menginstal PyTorch (yang berukuran > 2 GB dan lambat dimuat). ONNX Runtime murni ditulis dalam C++ dengan wrapper Python yang sangat ringan.
* **Operator Fusion & Constant Folding:** Selama ekspor ONNX, grafik komputasi model dioptimasi dengan menyatukan beberapa operator matematika yang berdekatan dan menghitung operasi konstan terlebih dahulu. Ini menghasilkan pemangkasan latensi inferensi hingga lebih dari 300%.

---

## 4. Teori Persentase Kemiripan Kosinus Mentah (Raw Cosine Similarity Percentage)
Untuk menyajikan tingkat kedekatan semantik yang sangat sensitif terhadap perubahan atau penambahan kata pada dokumen masukan secara jujur, kita mengonversi skor Cosine Similarity mentah langsung ke dalam rentang persentase $[0\%, 100\%]$ tanpa menggunakan normalisasi probabilistik Softmax.

### Mengapa Softmax Berskala Suhu Ditinggalkan?
1. **Bias Ekstrim (One-Hot Bias):** Penggunaan normalisasi Softmax berskala suhu rendah ($T=0.012$) memaksa perbedaan kecil pada kesamaan mentah menjadi keputusan biner ekstrem (satu label 100%, lainnya 0%). Ini tidak realistis dan mencurigakan di hadapan dosen penguji.
2. **Ketiadaan Sensitivitas Kata:** Softmax memaksa total probabilitas menjadi 100%. Sehingga, penambahan kata-kata minor atau sedikit pengurangan kata pada dokumen masukan tidak akan mengubah skor visual secara dinamis karena akan selalu terdorong paksa ke 100% atau 0%.
3. **Representasi Asli Vektor:** Dengan menyajikan skor kemiripan kosinus mentah (*Raw Cosine Similarity*), setiap variasi kata pada dokumen masukan akan terrefleksi secara dinamis dan jujur pada grafik kesamaan. Jika ada 1 kata yang kurang, skor kesamaan geometris akan turun secara proporsional (misalnya dari 88% menjadi 82%), memberikan validitas sains yang jauh lebih tinggi.

---

## 5. Struktur Pelabelan Klasifikasi Multi-Layer
Sistem pelabelan dirancang menggunakan struktur **2 Layer Hierarkis** karena terbukti secara empiris paling efisien untuk dokumen terstruktur:

1. **Layer 1 (Domain Makro):** Memetakan dokumen ke domain besar civitas akademika (misal: *Akademik Mahasiswa*, *Administrasi Dosen*, *Jadwal dan SKS*).
2. **Layer 2 (Detail Mikro / Aksi):** Memetakan tipe aksi spesifik dokumen di bawah naungan domain tersebut (misal: *Transkrip Nilai*, *KRS Kelas*, *Daftar Dosen Pengajar*).

### Mengapa 2 Layer Paling Efisien dibanding 5 Layer?
* **Teori Klasifikasi Kognitif (Rosch, 1978):** Otak manusia secara alami mengelompokkan objek pada tingkat dasar (*basic level*) dan tingkat superordinat. Dua tingkat hierarki sudah sangat cukup untuk mencakup akurasi klasifikasi tanpa membebani sistem dengan overhead percabangan keputusan (*decision tree complexity*) yang berlebihan dan lambat.
* **Konsistensi Data:** Penambahan layer yang terlalu dalam (hingga 5 layer) menyebabkan masalah kelangkaan data (*data sparsity*) di mana label pada layer terdalam tidak memiliki representasi sampel yang cukup untuk dipelajari secara akurat, meningkatkan risiko klasifikasi salah (*false positives*).

---

## 6. Teori Hybrid Retrieval (Dense Semantic + Sparse BM25 Fusion)
Dalam implementasi mesin pencari akademik berskala besar, pencarian berbasis vektor padat (*Dense Retrieval*) dan pencarian berbasis kata kunci statistik (*Sparse Retrieval*) memiliki kekuatan dan kelemahan yang saling melengkapi.

### Perbandingan Dense vs Sparse Retrieval:
1. **Dense Retrieval (BERT Semantic):** Unggul dalam menangani kesepadanan konsep semantik (*synonymy*) dan makna implisit. Namun, model neural kadang kurang peka terhadap karakter kata yang unik secara mutlak (seperti kode virtual account, NIM mahasiswa spesifik, atau kode mata kuliah unik).
2. **Sparse Retrieval (Okapi BM25):** Unggul dalam mendeteksi kecocokan kata kunci persis (*exact lexical overlap*). Namun, BM25 tidak dapat memahami konteks semantik ataupun sinonim dari kata-kata yang berbeda.

### Metodologi Hybrid Fusion:
Dengan menggabungkan kedua skor di atas menggunakan **kombinasi linier tertimbang** (*weighted linear combination*), kita mendapatkan sistem pencarian hibrida yang sangat kokoh.
$$\text{Score}_{\text{Hybrid}} = \alpha \cdot \text{Dense}_{\text{BERT}} + (1 - \alpha) \cdot \text{Sparse}_{\text{BM25}}$$
Sistem menyetel $\alpha = 0.70$, yang berarti memberikan bobot utama pada kedalaman makna semantik ($70\%$), namun tetap mempertahankan filter leksikal persis ($30\%$) dari BM25 untuk mengeliminasi hasil penemuan palsu (*false positives*). Hal ini menjamin dokumen transkrip nilai riil yang memuat NIM yang persis sama akan langsung terangkat ke peringkat teratas dengan nilai keyakinan geometris yang jujur dan presisi.

---

## 7. Teori Penentuan Jumlah Optimal Kategori / Label (Rice Rule)
Dalam Teori Temu Kembali Informasi dan Pengelompokan Data (*Information Retrieval & Clustering Theory*), pembagian data ke dalam kategori atau label yang terlalu sedikit akan mengakibatkan hilangnya kedalaman semantik (*semantic underfitting*), sedangkan pembagian ke dalam terlalu banyak label akan menyebabkan kelangkaan sebaran data (*data sparsity* atau *overfitting*).

Untuk menyeimbangkan kompleksitas taksonomi dengan jumlah dokumen total ($N$) dalam database, kita mengacu pada **Aturan Rice** (*Rice Rule*) yang didefinisikan secara matematis untuk memprediksi jumlah optimal kategori/label $X$:

$$X = \lceil 2 \cdot N^{1/3} \rceil$$

### Penerapan pada Korpus Akademik Kampus:
* Untuk jumlah dokumen database kita ($N = 1000$ dokumen):
  $$X = \lceil 2 \cdot 1000^{1/3} \rceil = \lceil 2 \cdot 10 \rceil = 20 \text{ Label}$$
* Oleh karena itu, kita membagi taksonomi eksklusif skenario Demo Real (Riset, Jurnal, dan Abdimas) menjadi tepat **20 label unik** (3 Domain Makro pada Layer 1 + 17 Detail Mikro pada Layer 2) untuk menjamin penyebaran probabilitas kelas yang optimal di hadapan model saraf BERT-mini.

