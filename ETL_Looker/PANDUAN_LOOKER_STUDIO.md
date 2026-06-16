# 📊 Panduan Lengkap Perancangan Dashboard Google Looker Studio untuk Sistem STKI

Dokumen ini berisi panduan teknis untuk mengimpor dan memvisualisasikan hasil klasifikasi AI dokumen Hukum (pasal.id) ke dalam Google Looker Studio menggunakan **Wide Architecture** (Arsitektur Multi-Kolom).

## Tahap 1: Sinkronisasi Data (ETL)
1. Buka terminal/cmd di folder proyek Anda.
2. Eksekusi perintah ini untuk mengambil data klasifikasi terbaru dari SQLite dan memipihkannya:
   ```bash
   python ETL_Looker/export_looker_csv.py
   ```
3. Script akan menghasilkan file `ETL_Looker/looker_dashboard_feed.csv`. File inilah yang akan menjadi *Data Source* Anda.

> [!NOTE]
> **Arsitektur Wide Data**
> Saat ini 1 baris di CSV = tepat 1 dokumen UU. Anda tidak perlu khawatir tentang redundansi baris.

---

## Tahap 2: Menghubungkan ke Google Looker Studio
1. Buka [Looker Studio](https://lookerstudio.google.com/).
2. Buat **Blank Report** baru.
3. Pilih konektor data **File Upload** (Unggah File).
4. Klik tombol unggah dan pilih file `looker_dashboard_feed.csv` milik Anda.
5. Setelah file berstatus *Uploaded* (hijau), klik tombol **Add** di pojok kanan bawah.

---

## Tahap 3: Perancangan Arsitektur Widget (Anti-Redundan)

Di arsitektur Wide yang baru ini, perancangan metrik menjadi jauh lebih sederhana karena Anda bisa menggunakan agregasi **Count** standar (tanpa perlu Count Distinct).

### Bagian Atas: Global Control (Penyaring Dinamis)
Tambahkan komponen **Drop-down list** di paling atas *dashboard* agar *user* bisa menyaring data:
* **Control 1:** Dimension: `tahun_terbit` (Filter berdasarkan tahun pengesahan).
* **Control 2:** Dimension: `layer_1_primary` (Filter spesifik klaster AI).

### Level 1: Executive Scorecards (Makro)
Gunakan komponen **Scorecard** berjajar empat di atas untuk melihat kesehatan sistem secara instan.

1. **Total Dokumen Tersimpan**
   * **Chart:** Scorecard
   * **Metric:** `Record Count`
   * *Tujuan:* Menampilkan total populasi dokumen undang-undang yang ada dalam sistem.

2. **Rasio Anomali (Outlier Ratio)**
   * **Chart:** Scorecard
   * **Metric:** Buat *Calculated Field* baru, beri nama "Persentase Outlier":
     ```sql
     COUNT(CASE WHEN indikator_outlier = 'Yes' THEN document_id ELSE NULL END) / COUNT(document_id)
     ```
   * **Data Type:** Ubah menjadi Percentage (%).
   * *Tujuan:* Jika persentase ini tinggi, berarti mesin AI K-Means gagal mengelompokkan banyak dokumen.

3. **Total Keragaman Topik (Unique Domains)**
   * **Chart:** Scorecard
   * **Metric:** `layer_1_primary`
   * **Aggregation:** `Count Distinct`
   * *Tujuan:* Mengetahui secara persis ada berapa banyak variasi topik/klaster hukum raksasa yang berhasil dipetakan oleh mesin kecerdasan buatan.

4. **Rata-rata Kedalaman Klasifikasi**
   * **Chart:** Scorecard
   * **Metric:** `jumlah_label`
   * **Aggregation:** `Average`
   * *Tujuan:* Mengukur seberapa kaya fitur taksonomi dokumen Anda. Semakin tinggi angkanya, semakin detail AI mendeskripsikan satu dokumen.

### Level 2: Visualisasi Distribusi (Kategori & Waktu)

3. **Distribusi Tahun Pembuatan UU**
   * **Chart:** Diagram Batang (Bar Chart)
   * **Dimension:** `tahun_terbit` (Jika ingin menampilkan per tahun).
   * **Metric:** `Record Count`
   * *Tujuan:* Mengetahui tren jumlah pengesahan Undang-Undang per tahunnya.

> [!TIP]
> **Pro Tip: Membuat Rentang 5-Tahunan (Tanpa Coding)**
> Jika grafik batang Anda terlalu padat dan menumpuk di kategori "Lainnya", Anda bisa mengelompokkan tahun menjadi rentang per 5 tahun (misal: "1945 - 1949") langsung dari Looker Studio!
> 1. Di panel kanan (Sumber Data), klik **+ Tambahkan kolom (Add a field)** di bagian paling bawah.
> 2. Beri nama kolom: `Rentang 5 Tahun`.
> 3. *Copy-paste* rumus ajaib ini ke dalam kotak Formula:
>    ```sql
>    CASE 
>      WHEN REGEXP_MATCH(tahun_terbit, "^[0-9]{4}$") THEN 
>        CONCAT(CAST(FLOOR(CAST(tahun_terbit AS NUMBER) / 5) * 5 AS TEXT), " - ", CAST(FLOOR(CAST(tahun_terbit AS NUMBER) / 5) * 5 + 4 AS TEXT))
>      ELSE "Tidak Diketahui"
>    END
>    ```
> 4. Klik **Simpan** lalu **Selesai**.
> 5. Ganti Dimensi pada grafik batang Anda dari `tahun_terbit` menjadi `Rentang 5 Tahun`. Grafik Anda akan langsung menjadi sangat rapi!

4. **Kekuatan Prediksi Domain AI (Layer 1)**
   * **Chart:** Treemap atau Donut Chart
   * **Dimension:** `layer_1_primary`
   * **Metric:** `Record Count`
   * *Tujuan:* Mengetahui domain/kategori utama mana yang paling dominan di dalam sistem. Data ini saling eksklusif (1 dokumen hanya masuk 1 irisan *Pie Chart*).

### Level 3: Analisis Investigasi Mendalam (Tabel Teks)

5. **Tabel Ensiklopedia Hukum (Interactive Table)**
   * **Chart:** Table
   * **Dimensions (Berurutan):** `filename`, `tahun_terbit`, `layer_1_primary`, `layer_1_all`, `layer_2_primary`, `content_snippet`
   * **Metric:** Hilangkan/Sembunyikan semua metric angka.
   * *Tujuan:* Ini akan menjadi Ensiklopedia Super! Administrator bisa membaca 150 karakter pertama dari bunyi UU secara langsung dari dalam tabel di *dashboard* tanpa harus membuka dokumen aslinya, disertai dengan informasi lengkap tahun dan klasifikasi kecerdasannya.
