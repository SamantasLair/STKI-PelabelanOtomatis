# [L3] THEORY & PRACTICE: IN-MEMORY SEMANTIC CACHING

*In-Memory Semantic Caching* bertugas mewujudkan doktrin komputasi O(1) STKI. Di saat antarmuka *UI/UX Neobrutalism* menuntut interaksi instan yang kaku dan mekanistik, proses di balik layar (*Back-End*) tidak memiliki kemewahan latensi parsial untuk membongkar tumpukan berkas yang bersarang di cakram (*disk storage*). Metode pengambilan memori di STKI mengganti sirkulasi *query* repetitif relasional di SQL menjadi *pointer dereferencing* instan di dalam struktur data internal Python (`dict`).

### 1. Landasan Implementasi: Pemetaan Key-Value Array

Cache semantik tidak menyimpan korpus mentah, melainkan blok presisi NumPy (`ndarray`) dari representasi vektor model. Skema pengenal kunci dirancang untuk mendukung multi-ledger (banyak basis data taksonomi paralel):
$$ \text{Cache Key} = (\text{DB\_Type}, \text{Doc\_ID}) \rightarrow \text{NumPy Array}_{384D} $$

Pengenal silang ini menjamin bahwa sistem bisa merotasi beberapa basis data akademik secara konkuren (contoh: *Dataset Politik* dan *Dataset Komputer*) tanpa polusi tumpang-tindih alamat memori *Cache*.

### 2. Implementasi Source Code

*Source File:* `TKI/app_web.py` (Konteks Ekstraksi `get_db_embedding`)
Proses penarikan memori ini dijalankan secara reaktif (*Lazy Initialization*). Jika skalar vektor tak ada di RAM, sirkuit SQL akan memanggil JSON O.S lokal, namun hanya satu kali, selamanya ia dibekukan dalam struktur C NumPy RAM.

```python
# [Variabel Global RAM State]
DB_EMBEDDING_CACHE = {}

def get_db_embedding(active_db_type, doc_id, emb_str):
    cache_key = (active_db_type, doc_id)
    
    # Pencarian Memori O(1) via Hashing Key Tuple
    if cache_key not in DB_EMBEDDING_CACHE:
        # Konversi JSON String O(N) dilakukan hanya sekali di fase Cold Start
        DB_EMBEDDING_CACHE[cache_key] = np.array(json.loads(emb_str))
        
    return DB_EMBEDDING_CACHE[cache_key]

@app.before_request
def sync_global_db_state():
    # [FIXED] Cache Invalidation Logic
    # Sistem melacak state antar Ledger dan memaksa flush memory O(1) jika ada pergeseran State
    global active_db_type, active_db_path, TAXONOMY, DB_EMBEDDING_CACHE
    current_type = get_active_db_type()
    
    if 'active_db_type' not in globals() or active_db_type != current_type:
        active_db_type = current_type
        active_db_path = get_active_db_path()
        TAXONOMY = load_taxonomy(active_db_path)
        DB_EMBEDDING_CACHE = {} # Pemusnahan Alokasi Memori Paksa (Garbage Collection Trigger)
```

### 3. Batas Eksekusi & Mitigasi Limit

- **Saturasi Out-Of-Memory (OOM):** *Caching* buta akan mengekspansi RAM mesin hingga terbunuh oleh Kernel Linux (OOM-Killer) apabila indeks sistem merayap melewati $5$ juta dokumen.
- **Mitigasi:** Mekanisme pembersihan paksa terintegrasi di dalam rotasi basis data (`sync_global_db_state`). Saat pengguna berpindah klaster taksonomi/Ledger, `DB_EMBEDDING_CACHE` dengan paksa direset (dihapus penunjukknya/dereferencing) menjadi objek kosong `{}`. Pendekatan ini melepaskan kontrol referensi (*Reference Count*) Python ke nol, memaksa modul *Garbage Collector* (GC) sistem mendealokasikan RAM matriks besar sebelumnya sebelum matriks klaster baru dimuat.

---
*Konteks: Eksekusi L3 dari [[L2_LATENCY_OPTIMIZATION]]*
