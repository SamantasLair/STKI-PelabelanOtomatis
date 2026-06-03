# [L3] THEORY & PRACTICE: RICE RULE MATHEMATICS

Paradigma dasar *Unsupervised Learning*, khususnya pemisahan vektor via *K-Means*, selalu terbentur pada dilema tebakan teoretis *K*: berapa jumlah target pemisahan yang wajar? Evaluasi komputasi *Elbow Method* iteratif akan melumpuhkan performa *server* jika dihadapkan dengan re-klastering berulang untuk ratusan ribu korpus data. STKI mengatasi kejatuhan iteratif ini dengan mendelegasikan inisiasi klaster ke konstanta pasti secara matematis melalui **Rice Rule**, sebuah teorema estimasi kepadatan interval distribusi dari disiplin statistik.

### 1. Landasan Matematis: Regulasi Densitas Takson

*Rice Rule* mendikte bahwa besaran pemisahan kelompok $X$ (sebagai pengganti $K$) tidak tumbuh secara linear dengan peningkatan ukuran populasi dokumen $N$. Pertumbuhan dibatasi oleh struktur akar pangkat tiga. Hal ini menjamin ekuilibrium antara kekayaan spesifikasi klaster dan pencegahan fragmentasi di mana 1 dokumen menjadi 1 klaster (*Over-fitting*).

$$ X = \lceil 2 \cdot \sqrt[3]{N} \rceil = \lceil 2 \cdot N^{1/3} \rceil $$

Dalam ekosistem *Taxonomy Engine* STKI:
- Jika korpus akademik berjumlah $1000$ dokumen $\rightarrow 2 \cdot 1000^{1/3} = 20$. Sistem akan mengunci batas penemuan topik (*Topic Discovery*) secara otomatis di $20$ rentang *Centroid*.

### 2. Implementasi Source Code

*Source File:* `TKI/app_web.py` (Konteks Status API Telemetri)
Konstruksi fungsi Python beroperasi di sisi *Backend O.S* untuk mengirimkan patokan *optimal_x* agar antarmuka UI bisa mendisiplinkan pengguna untuk tidak menambah label manual melampaui aturan matematis tersebut.

```python
import math
import sqlite3

@app.route("/api/status", methods=["GET"])
def get_status():
    # Menarik jumlah N dokumen menggunakan fungsi hitung agregat C-Engine (O(1))
    conn = sqlite3.connect(get_active_db_path(), timeout=15)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM documents")
    total_docs = c.fetchone()[0]
    conn.close()
    
    # [FIXED] Hukum Rice Rule diaplikasikan murni
    optimal_x = math.ceil(2 * (total_docs ** (1/3))) if total_docs > 0 else 0
    
    return jsonify({
        "total_docs": total_docs,
        "optimal_labels_count": optimal_x
    })
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Saturasi Klaster pada Big Data ($N > 1,000,000$):** Meskipun *Rice Rule* efisien untuk korpus skala menengah ke bawah ($<1M$), nilai pangkat tiga akan tetap membengkak menjadi $\sim 200$ klaster untuk 1 juta paper, yang masih terlalu banyak untuk dikelola di dalam UI *Accordion*.
- **Mitigasi:** Arsitektur taksonomi membelah hirarki ke *Layer 1 (Domain)* dan *Layer 2 (Detail)*. *Rice Rule* hanya bertindak sebagai panduan mutlak bagi distribusi otomatis di *Layer 2*. Jika batas 50 tercapai, *Layer 1* bertugas sebagai *Container* makro penahan luapan sub-klaster (memaksa visualisasi dua dimensi bertingkat).

---
*Konteks: Eksekusi L3 dari [[L2_TAXONOMY_ENGINE]]*
