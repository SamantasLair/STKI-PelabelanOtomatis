# [L3] THEORY & PRACTICE: BIG DATA DOCTRINE

*Big Data Doctrine* pada STKI adalah filosofi rekayasa perangkat lunak ketat yang mensyaratkan toleransi waktu absolut $O(1)$ untuk akses referensi vektor OML (Open Machine Learning) yang berjalan pada spesifikasi server terbatas tanpa kartu *Graphics Processing Unit* (GPU). 

Secara konvensional, arsitektur *web app* memisahkan eksekusi model di level REST API dan menggunakan kueri SQL persisten murni untuk penarikan metadata. Pendekatan disk/I-O murni ini meledak dalam kondisi *Information Retrieval* yang membutuhkan agregasi O(N) untuk ribuan titik koordinat semantik vektor. Meminta DB men-de-serialisasi *string array* ke *float numpy* tiap kueri berarti kematian operasional server.

### 1. Fondasi Paradigma $O(1)$ vs Konstraint RAM Konkuren

Beban teoretis dari sebuah vektor 384-D dengan presisi `float64` (8 bytes) per dimensi adalah sekitar $3.072$ Kilobytes per dokumen.
Untuk korpus $100,000$ dokumen:
$$ \text{RAM Alloc} \approx 100,000 \times 3.072 \text{ KB} = 307.2 \text{ MB} $$

Beban ini sangat ringan bagi blok *Memory (RAM)* server. Mengapa mendelegasikan iterasi baca ke lambannya disk-drive (O(N) *Seek Time*) atau SQLite JSON parser saat kita bisa menyedot $307$ MB ke dalam pemetaan *Dictionary/Hash Table* memori yang menjamin rute O(1)? *Big Data Doctrine* mewajibkan pemusnahan perulangan deserialisasi JSON tingkat Python, mengubahnya menjadi satu siklus pre-komputasi asinkron.

### 2. Implementasi Filter C-Engine (Bypass JSON1)

*Source File:* `TKI/app_web.py` (Konteks Ekstraksi Paginasi UI)
Untuk fungsionalitas UI yang murni (seperti merender label kardinalitas matriks), Python tidak mengekstraksi atribut baris satu per satu. Ia memerintahkan ekstensi biner SQLite (JSON1 C-Engine) untuk memfilter tabel tersebut pada level biner absolut.

```python
# [BIG DATA DOCTRINE] C-Engine JSON1 Offloading (Zero Python RAM Allocation)
if filter_type == 'outlier':
    # Agregasi perhitungan dilakukan di level C/SQLite
    # Tidak pernah mem-fetch ratusan ribu row string dan di-loop for/json.loads()
    count_query = """
        SELECT COUNT(id) FROM documents 
        WHERE labels IS NULL OR labels = '[]' OR json_array_length(labels) = 0 
        OR EXISTS (SELECT 1 FROM json_each(documents.labels) WHERE json_each.value = 'Tidak Terklasifikasi')
    """
    data_query = f"""
        SELECT id, {filename_col}, labels, content FROM documents 
        WHERE labels IS NULL OR labels = '[]' OR json_array_length(labels) = 0 
        OR EXISTS (SELECT 1 FROM json_each(documents.labels) WHERE json_each.value = 'Tidak Terklasifikasi')
        ORDER BY id DESC LIMIT ? OFFSET ?
    """
    cursor.execute(count_query)
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Latensi Cold Start:** Memuat tensor kontinu dan memotong siklus komputasi disk akan meradikalisasi laju *runtime*, tetapi harus menanggung siklus penyedotan (Warm-Up Phase) pada detak pertama inisialisasi server. Ini memicu potensi pembekuan API Gunicorn jika `timeout` batas minimum dilewati.
- **Mitigasi:** Arsitektur asinkron *Lazy Load*. Proses deserialisasi hanya menaruh representasi O(1) ke cache saat dokumen bersangkutan disinggung pertama kali (*on-demand mapping*) melalui pendelegasian sub-sistem sekunder.

---
*Konteks: Eksekusi L3 dari [[L2_LATENCY_OPTIMIZATION]]*
