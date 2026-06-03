# [L3] THEORY & PRACTICE: COSINE THRESHOLDING (MULTI-LABEL)

Setelah *Taxonomy Engine* mendefinisikan ruang kategori (via manual *Domain* atau otonomi sentroid *Rice Rule*), sistem menghadapi rintangan kedua: *Assignation* (Penetapan Himpunan). Mengklasifikasikan 1 dokumen murni kepada 1 klaster dengan logika maksimum argumen (`argmax`) adalah kecacatan logika fatal pada arsitektur semantik yang kompleks. Sebaliknya, STKI mengadopsi paradigma ambang batas sudut (*Cosine Thresholding*) di mana setiap dokumen memiliki probabilitas lintasan antar klaster tanpa batas, membentuk arsitektur himpunan irisan *Venn*.

### 1. Landasan Matematis: Regulasi Irisan Dinamis

Sebuah dokumen direpresentasikan sebagai vektor target $\vec{V_D}$. Mesin mengkalkulasi skalar sudut (Cosine) antara target tersebut terhadap seluruh vektor sentroid taksonomi $\vec{V_{T_i}}$. Jika sebuah skor melewati batas parameter penolakan minimum (umumnya $\tau \ge 0.50$), takson tersebut dipetakan ke dalam daftar *Multi-Label* dokumen.

Syarat Himpunan Inklusi $L$:
$$ L = \{ T_i \mid \text{Cosine}(\vec{V_D}, \vec{V_{T_i}}) \ge \tau \} $$

Pemisahan regulasi *Threshold* berlaku pada dua garis besar topologi:
- *Layer 1 (Domain)* lebih luas sehingga menoleransi irisan lebih renggang ($\tau_{L1} = 0.50$).
- *Layer 2 (Detail)* menuntut derajat determinasi yang lebih padat ($\tau_{L2} = 0.55$).

### 2. Implementasi Source Code

*Source File:* `TKI/app_web.py` (Konteks Ekstraksi `async_relabel_task`)
Komputasi berjalan secara parsial pada sirkuit asinkron (*Background Thread*) untuk memastikan pengguna dapat bernavigasi tanpa antarmuka beku selama pelabelan ulang beroperasi.

```python
# [Logika Thresholding O(N*C) di dalam Thread Relabeling]
l2_raw_sims = []
for label in tax_layer2:
    lbl_vector = get_onnx_embedding(label)
    sim = get_cosine_similarity(emb, lbl_vector)
    l2_raw_sims.append(sim)

# ... [Lexical Gatekeeper Code dihilangkan untuk abstraksi] ...

# Ambil threshold dinamis dari RAM/DB Memory
dyn_t2 = float(TAXONOMY.get("threshold_l2", 0.55))

# Filter Array (Rejection Limit)
for i in range(len(l2_raw_sims)):
    if l2_raw_sims[i] < dyn_t2: 
        l2_raw_sims[i] = 0.0

assigned_l2 = []
for i, sim in enumerate(l2_raw_sims):
    if sim > 0.0:
        assigned_l2.append(tax_layer2[i])
        
# Kondisi Fallback jika Array Irisan Kosong (Outlier)
if not assigned_l2:
    assigned_l2 = ["Tidak Terklasifikasi"]
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Anomali Over-Clustering (Saturasi 100%):** Pada pengaturan ambang batas yang terlalu moderat ($\tau < 0.40$), sebuah dokumen cenderung akan ditarik oleh daya tarik gravitasi seluruh klaster. Efek ini memunculkan kardinalitas semu ($1$ Dokumen memiliki $15$ Label) dan merusak *Telemetry Matrix*.
- **Mitigasi:** Lapisan penalti yang dikembangkan sebelum filter $\tau$ dieksekusi, yakni integrasi *Soft Lexical Gatekeeper* berbobot IDF yang mereduksi skor vektor *Cosine* sebesar $20\%$ (`x 0.80`) jika irisan N-Gram dari teks utama tidak menembus batas persilangan murni yang dikehendaki.

---
*Konteks: Eksekusi L3 dari [[L2_TAXONOMY_ENGINE]]*
