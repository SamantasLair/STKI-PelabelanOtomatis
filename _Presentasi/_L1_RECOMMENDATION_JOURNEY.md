# [L1] RECOMMENDATION & BACKGROUND TASK JOURNEY MAP

_Konteks: Peta Lapisan 1 untuk Sistem Rekomendasi (More Like This) & Background K-Means Relabeling_

Dokumen ini memetakan alur subsistem tambahan (Auxiliary) yang berjalan di luar proses pencarian kueri utama. Subsistem ini menjamin bahwa dokumen selalu memiliki klasifikasi yang mutakhir dan pengguna bisa menemukan dokumen serupa secara otonom.

```mermaid
flowchart TD
    %% PENENTUAN GAYA WARNA (COLOR CODING)
    classDef bgProcess fill:#2c5282,stroke:#63b3ed,stroke-width:2px,color:#fff,stroke-dasharray: 5 5
    classDef dbColor fill:#702459,stroke:#d6bcfa,stroke-width:2px,color:#fff
    classDef denseColor fill:#276749,stroke:#68d391,stroke-width:2px,color:#fff
    classDef uiColor fill:#1a202c,stroke:#e2e8f0,stroke-width:3px,color:#fff

    %% ==========================================
    %% SUB-SISTEM 1: REKOMENDASI "MORE LIKE THIS"
    %% ==========================================
    subgraph ZONA_REKOMENDASI [ZONA HILIR - SISTEM REKOMENDASI SEMANTIK]
        U1(User Sedang Membaca Dokumen X) ::: uiColor
        U1 --> R1[Klik 'Cari Dokumen Serupa'] ::: uiColor
        
        R1 --> D1{Ambil Vektor Dokumen X dari Database} ::: dbColor
        D1 --> D2[Target Vektor [384-D]] ::: denseColor
        
        D2 --> D3[Kalkulasi Cosine Similarity Massal vs Semua Dokumen Lain] ::: denseColor
        D3 --> D4[Urutkan Top-5 Skor Cosine Tertinggi] ::: denseColor
        D4 --> R2([Tampilkan Daftar Rekomendasi Akurat]) ::: uiColor
    end

    %% ==========================================
    %% SUB-SISTEM 2: BACKGROUND K-MEANS RELABELING
    %% ==========================================
    subgraph ZONA_TELEMETRI [ZONA BELAKANG - BACKGROUND TELEMETRY DAN RELABELING]
        B1(Trigger: User Mengunggah Dokumen Baru) ::: uiColor
        B1 --> B2{Spawn Asynchronous Thread} ::: bgProcess
        
        B2 --> B3[Tarik Seluruh Vektor dari tb_docs_domain] ::: dbColor
        B3 --> K1[Kalkulasi Rice Rule] ::: bgProcess
        
        K1 --> K2[Eksekusi Scikit-Learn K-Means Clustering] ::: bgProcess
        K2 --> K3[Ekstraksi TF-IDF Top Words per Cluster] ::: bgProcess
        K3 --> K4[Beri Nama Topik Dinamis] ::: bgProcess
        
        K4 --> B4[Update Array Label di tb_docs_domain] ::: dbColor
        B4 --> B5[Overwrite tb_tax_domain] ::: dbColor
    end
```

## Penjelasan Simpul Proses Berdasarkan Warna
1. **Abu-Abu Gelap (User Interface)**: Interaksi ujung dari pengguna saat meminta dokumen rujukan.
2. **Ungu Tua (Database Read/Write)**: Operasi baca-tulis berat yang terjadi pada SQLite secara terisolasi.
3. **Hijau (Dense Vector Math)**: Proses matematika murni (Cosine Similarity) tanpa melibatkan pencarian huruf/teks. Sistem merekomendasikan dokumen murni berdasarkan himpitan kordinat vektor.
4. **Biru Putus-Putus (Background Thread)**: Proses berat yang dieksekusi secara asinkron (*Asynchronous*) di balik layar. Pengguna tidak akan mengalami *Freeze/Lag* saat mengunggah dokumen karena tugas ektraksi TF-IDF dan K-Means diserahkan kepada *Thread* pekerja cadangan (*Worker Thread*).
