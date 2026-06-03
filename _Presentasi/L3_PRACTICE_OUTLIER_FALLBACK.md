# [L3] THEORY & PRACTICE: OUTLIER FALLBACK MECHANISM

Dalam paradigma mesin pembelajaran *Unsupervised* (contohnya klasterisasi *Hard-Bound* dari K-Means ortodoks), sistem sering dijangkiti kecacatan konseptual di mana ia memaksa dokumen anomali murni untuk masuk ke dalam klaster yang paling dekat, meski "terdekat" itu memiliki selisih jarak semantik spasial yang ektstrem. *Outlier Fallback Mechanism* diciptakan sebagai perisai pemutus rantai anomali tersebut dalam ekosistem Taksonomi STKI.

Sub-sistem ini secara spesifik beroperasi sebagai penyaring di mana mesin akan mendeklarasikan *Surrender State* ("Tidak Terklasifikasi") ketika dokumen yang dievaluasi gagal menembus batas kelayakan *Cosine Thresholding* ($\tau_{L1}$ maupun $\tau_{L2}$). Ini berfungsi melindungi agregasi klaster utama dari degradasi kemurnian sentroid (*Centroid Degradation*).

### 1. Landasan Pemikiran Arsitektural

Kondisi yang memicu *Outlier Fallback*:
1. **Pecahan Entropi Linguistik Ekstrem:** Teks terlalu pendek, banyak diisi oleh data tabular cacat *OCR*, atau *Stop-Words* tak berarti, membuat representasi tensor *Dense* 384-D mengumpul secara sporadis di nol ($\sim \vec{0}$).
2. **Kondisi O.O.D (Out of Distribution):** Jika seluruh taksonomi berpusat pada sentroid klaster *Teknologi Informasi*, sementara teks dokumen adalah manual perakitan pompa air sentrifugal hidrolik; jarak semantiknya niscaya berputar di angka $< 0.20$. Pemaksaan klasterisasi terhadap dokumen tersebut akan menyebabkan *Centroid Bias* di iterasi OML berikutnya.

### 2. Implementasi Source Code

*Source File:* `TKI/app_web.py` (Konteks Ekstraksi `async_relabel_task`)
Deteksi O.O.D diterapkan pada siklus final pendelegasian himpunan array (*Assignation Check*).

```python
# [Konteks Pasca Iterasi Array l1_raw_sims dan Filter Threshold dyn_t1]
assigned_l1 = []
for i, sim in enumerate(l1_raw_sims):
    if sim > 0.0:
        assigned_l1.append(tax_layer1[i])
        
# Evaluasi Outlier O.O.D: Array Irisan Kosong
if not assigned_l1:
    assigned_l1 = ["Tidak Terklasifikasi"]

# Penyatuan Final L1 & L2 List Tanpa Duplikasi
predicted_labels = list(set(assigned_l1 + assigned_l2))

# Eksekusi O(1) String-ify JSON untuk injeksi database SQLite
cursor.execute(
    "UPDATE documents SET labels = ? WHERE id = ?", 
    (json.dumps(predicted_labels), doc_id)
)
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Efek "Black Hole" pada Ambang Ekstrem:** Apabila pengguna dengan agresif menyetel tingkat $\tau$ terlalu tinggi (contohnya $\tau = 0.90$), maka akan mendistorsi ekosistem di mana $99\%$ dokumen menjadi himpunan bagian dari klaster "Tidak Terklasifikasi", merusak kapabilitas filter antarmuka.
- **Mitigasi:** Arsitektur antarmuka Terminal Data Science secara kaku mengimplementasikan kontrol pengungkit rentang geser (Range Slider Constraint) yang menolak penyetelan *Threshold* $\tau > 0.85$ guna mencegah efek "lubang hitam" taksonomi di lapisan pelabelan otomatis.

---
*Konteks: Eksekusi L3 dari [[L2_TAXONOMY_ENGINE]]*
