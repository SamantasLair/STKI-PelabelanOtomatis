# [L3] Arsitektur Sentralisasi B-Tree Polimorfik

_Konteks: Bagian dari Topologi Presentasi Data Pipeline_

Dokumen ini adalah landasan teoretis untuk mempertahankan keputusan arsitektur (Architecture Decision Record) pemusnahan sistem Multi-Database (*File-Based Sharding*) dan migrasi mutlak ke **Master Database Sentral (`stki_master.db`)** dengan Tabel Polimorfik.

## 1. Analisis Kritis: Kegagalan Multi-Database (Legacy System)
Sistem lama STKI memecah domain (Hukum, Akademik, Politik) ke dalam file `.db` yang berbeda-beda (`db_politik.db`, `academic_metadata.db`, dll). Secara dangkal, ini tampak mengisolasi data. Namun secara sistemik, ini adalah cacat arsitektur:
1. **Disk I/O Bottleneck:** Pada setiap perpindahan antarmuka (*Switch Ledger*), OS harus menutup *file handle* lama dan membuka *file handle* baru. Ini menelan biaya syscall tingkat OS yang asimtotik membebani RAM ketika beban *user* naik.
2. **Koneksi Terputus (I/O Lock):** Flask SQLite connection pool gagal digunakan secara optimum karena pool harus dipecah untuk belasan file berbeda.

## 2. Paradigma Polymorphic Tables (The B-Tree Solution)
Sistem baru mengintegrasikan seluruh domain ke dalam satu file tunggal `stki_master.db` namun tetap menjamin **Isolasi Logis (Logical Isolation)** dengan arsitektur **Paket Tabel Domain**.

Untuk setiap domain (misal $D = \text{"hukum"}$), sistem membangkitkan 3 tabel independen:
1. `tb_docs_hukum` (Menyimpan Vektor O(1))
2. `tb_tax_hukum` (Menyimpan Taksonomi K-Means)
3. `tb_set_hukum` (Menyimpan Threshold)

### 2.1 Pembuktian Matematis Efisiensi B-Tree
Jika kita mencampur seluruh dokumen (jutaan row) ke dalam *satu tabel tunggal* dengan kolom `domain = 'hukum'`, pencarian dokumen akan memicu operasi B-Tree *Index Scan* dengan kompleksitas $O(\log N_{total})$. 

Namun, dengan **Tabel Polimorfik** terpisah per domain, ukuran $N$ berkurang secara drastis hanya menjadi $N_{domain}$ saja. 
Maka kompleksitas pencarian adalah murni $O(\log N_{domain})$, jauh lebih ringan secara logaritmik, namun mendapat keuntungan I/O dari 1 koneksi terpusat.

```mermaid
graph TD
    A[stki_master.db (1 I/O Connection)] --> B{Domain Switcher}
    B -- "Domain: Akademik" --> C[tb_docs_akademik]
    B -- "Domain: Akademik" --> D[tb_tax_akademik]
    B -- "Domain: Hukum" --> E[tb_docs_hukum]
    B -- "Domain: Hukum" --> F[tb_tax_hukum]
    
    style A fill:#1a1a1a,stroke:#333,stroke-width:2px,color:#fff
    style C fill:#0f3b0f,stroke:#2d5a2d,color:#fff
    style E fill:#0f3b0f,stroke:#2d5a2d,color:#fff
```

## 3. Kesimpulan Evaluasi
Sistem saat ini sepenuhnya terproteksi dari kebocoran label taksonomi antar-domain (karena setiap domain punya tabel `tb_tax_{domain}` sendiri). Model ini membuktikan bahwa *Clean Code Architecture* yang diusung oleh standar industri modern tidak mencampur urusan aplikasi (*Business Logic*) ke dalam manajemen sistem operasi file (*OS File Management*).
