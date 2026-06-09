# [L0] SYSTEM JOURNEY MAP: SIKLUS HIDUP DATA

_Konteks: Peta Utama Navigasi Sistem STKI_

Dokumen ini memetakan perjalanan seutas teks sejak ia masih berupa dokumen mentah, hingga diproses oleh **Mesin Leksikal (Sparse)** dan **Mesin Semantik (Dense)**, lalu disimpan di pangkalan data sentral untuk temu kembali hibrida.

Gunakan peta ini saat presentasi untuk menjelaskan aliran data secara runut dan teknis. Ikuti alur dari atas ke bawah.

```mermaid
flowchart TD
    %% PENENTUAN GAYA WARNA (COLOR CODING)
    classDef inputColor fill:#2d3748,stroke:#a0aec0,stroke-width:2px,color:#fff
    classDef parserColor fill:#2b6cb0,stroke:#63b3ed,stroke-width:2px,color:#fff
    classDef bm25Color fill:#c05621,stroke:#fbd38d,stroke-width:2px,color:#fff
    classDef denseColor fill:#276749,stroke:#68d391,stroke-width:2px,color:#fff
    classDef dbColor fill:#702459,stroke:#d6bcfa,stroke-width:2px,color:#fff
    classDef fusionColor fill:#b83280,stroke:#fbb6ce,stroke-width:2px,color:#fff
    classDef userColor fill:#1a202c,stroke:#e2e8f0,stroke-width:3px,color:#fff,stroke-dasharray: 5 5

    %% ==========================================
    %% ZONA HULU: DATA SCIENCE & PERSIAPAN DATA
    %% ==========================================
    subgraph ZONA_DS [ZONA HULU - DATA SCIENCE DAN PEMROSESAN DATA]
        
        %% FASE 1: INGESTI (INPUT)
        subgraph FASE_1 [1. FASE EKSTRAKSI KATA DAN PARSING MENTAH]
            A1(Unggah PDF)
            A2(Unggah DOCX)
            A3(Unggah CSV/XLSX)
            
            P1[PyPDF Engine]
            P2[Python-Docx Engine]
            P3[Pandas DataFrame]
            
            A1 --> P1
            A2 --> P2
            A3 --> P3
            
            Teks[Ekstraksi Teks String Murni]
            P1 --> Teks
            P2 --> Teks
            P3 --> Teks
        end

        %% FASE 2: REPRESENTASI MATEMATIS & LABELING
        subgraph FASE_2 [2. FASE VEKTORISASI DAN LABELING DATA]
            B1[Tokenisasi Kata & Hitung IDF]
            B2[(Penyimpanan Indeks Sparse / BM25)]
            Teks --> |Seluruh Teks| B1
            B1 --> B2

            D1[WordPiece Subword Tokenizer]
            D2[Inferensi Model Dense: MiniLM L-12]
            D3[Kalkulasi Mean Pooling]
            D4([Matriks Vektor 384-Dimensi])
            Teks --> |Distilasi TextRank| D1
            D1 --> D2
            D2 --> D3
            D3 --> D4
        end
        
    end

    %% ==========================================
    %% ZONA TENGAH: INFRASTRUKTUR PENYIMPANAN
    %% ==========================================
    subgraph ZONA_DB [ZONA TENGAH: PANGKALAN DATA TERPUSAT]
        %% FASE 3: PENYIMPANAN SQLITE
        subgraph FASE_3 [3. PENYIMPANAN DATABASE POLIMORFIK]
            S1{Struktur B-Tree SQLite}
            S2[(tb_docs_domain: Simpan Vektor & Teks)]
            S3[(tb_tax_domain: Simpan Kategori/Taksonomi)]
            
            D4 --> S1
            B2 --> S1
            S1 --> S2
            S1 --> S3
        end
    end

    %% ==========================================
    %% ZONA HILIR: SISTEM TEMU KEMBALI INFORMASI (STKI)
    %% ==========================================
    subgraph ZONA_STKI [ZONA HILIR - STKI RUNTIME INTERFACE]
        %% FASE 4: TEMU KEMBALI HIBRIDA & KLASIFIKASI
        subgraph FASE_4 [4. PENCARIAN KUERI DAN SKORING HIBRIDA]
            Q(Kueri Pencarian User)
            Q_B[Ekstraksi Leksikal BM25]
            Q_D[Ekstraksi Vektor Kueri ONNX]
            F1{Hybrid Fusion Formula}
            F2[Normalisasi Skor NDCG]
            R([Hasil Pencarian Terurut])
            
            Q --> Q_B
            Q --> Q_D
            
            S2 --> Q_B
            S2 --> Q_D
            
            Q_B --> F1
            Q_D --> F1
            
            F1 --> |Alpha = 0.70| F2
            F2 --> R
            
            %% Taksonomi digunakan untuk memfilter hasil atau klasifikasi kategori
            S3 -.-> |Filter Kategori Dinamis| F2
        end
    end

    %% PENERAPAN WARNA
    class A1,A2,A3 inputColor
    class P1,P2,P3,Teks parserColor
    class B1,B2,Q_B bm25Color
    class D1,D2,D3,D4,Q_D denseColor
    class S1,S2,S3 dbColor
    class F1,F2 fusionColor
    class Q,R userColor

```

## Penjelasan Simpul Proses Berdasarkan Warna
1. **Abu-Abu Gelap (Input User)**: Berkas mentah yang dilempar pengguna tanpa pengolahan apapun.
2. **Biru (Parsing Engine)**: Entitas Python yang menelanjangi format dokumen hingga tersisa string teks murninya.
3. **Oranye (Mesin Leksikal BM25)**: Algoritma evolusi TF-IDF. Menghitung statistik probabilitas kemunculan huruf persis. Cocok menangkap akronim kaku.
4. **Hijau (Mesin Semantik Dense)**: *Neural Network* (MiniLM L-12 ONNX). Ia membaca arah kalimat, memotong kata ke unit subword, dan menyusutkannya jadi koordinat 384 dimensi untuk mencari sinonim dan kaitan makna.
5. **Ungu Tua (Central Database)**: SQLite Master yang memecah lalu-lintas data secara isolasi antar tabel (`tb_docs_{domain}`).
6. **Pink (Fusion Engine)**: Formula final yang memadukan kekuatan probabilitas leksikal dan geometri semantik.
