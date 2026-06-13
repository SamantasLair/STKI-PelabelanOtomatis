# Panduan Migrasi Database Hukum ke Supabase (PostgreSQL)

Dokumen ini berisi instruksi teknis langkah demi langkah untuk memigrasikan basis data lokal SQLite (`hukum.db`) ke infrastruktur basis data *Cloud* PostgreSQL di **Supabase**, serta konfigurasi koneksi pada aplikasi Web Flask.

---

## Tahap 1: Persiapan Akun & Server Supabase

1. Kunjungi [supabase.com](https://supabase.com) dan buat proyek baru.
2. Tunggu hingga proses *provisioning* server PostgreSQL selesai (sekitar 2-3 menit).
3. Buka menu **Project Settings** -> **Database**.
4. Gulir ke bawah hingga menemukan bagian **Connection String** -> **URI**.
5. Salin URL tersebut. Formatnya akan terlihat seperti ini:
   `postgresql://postgres:[YOUR-PASSWORD]@db.xxxxxx.supabase.co:5432/postgres`

---

## Tahap 2: Migrasi Data (SQLite ke PostgreSQL)

Karena kita berpindah dari SQLite lokal ke server PostgreSQL, cara termudah dan teraman tanpa menghilangkan relasi arsitektur polimorfik kita adalah menggunakan **DBeaver** (Aplikasi Manajemen Basis Data Gratis).

1. Unduh dan instal **DBeaver Community Edition**. 
   *(Catatan: Berdasarkan arsitektur laptop/PC Anda saat ini, silakan pilih versi installer **Windows 64-bit (x86_64)**, bukan versi ARM).*
2. **Koneksi Lokal (Sumber):** 
   - Klik `New Database Connection` -> Pilih `SQLite`.
   - Arahkan *Path* ke file `hukum.db` di komputer Anda.
3. **Koneksi Supabase (Tujuan):**
   - Klik `New Database Connection` -> Pilih `PostgreSQL`.
   - Masukkan *Host*, *Database* (`postgres`), *User* (`postgres`), dan *Password* dari Supabase.
4. **Eksekusi Ekspor (Data Pump):**
   - Buka koneksi SQLite Anda, sorot semua tabel (seperti `documents`, `taxonomies`, dll).
   - Klik kanan -> Pilih **Export Data**.
   - Pilih target **Database**, lalu arahkan ke koneksi PostgreSQL (Supabase) Anda di skema `public`.
   - Klik *Next* hingga selesai. DBeaver akan menyalin struktur tabel beserta ribuan baris data dokumen hukum secara otomatis.

---

## Tahap 3: Konfigurasi Web App (Production)

Aplikasi Flask STKI kita telah dibekali dengan modul `SQLAlchemy` dan *driver* `psycopg2-binary` (lihat `requirements.txt`). Anda hanya perlu mengubah variabel lingkungan (*Environment Variable*).

1. Buka file `.env` di *root* proyek.
2. Temukan variabel `DATABASE_URL`.
3. Ganti nilainya dari URL SQLite menjadi URL Supabase Anda:

```env
# MENGGUNAKAN SUPABASE
DATABASE_URL=postgresql://postgres:PASSWORD_ANDA@db.xxxxxx.supabase.co:5432/postgres
```

> **[WARNING] Peringatan Keamanan**
> Pastikan file `.env` **TIDAK PERNAH** terunggah ke GitHub atau Hugging Face Spaces. Sistem telah diatur agar file ini diabaikan oleh `.gitignore`.

## Tahap 4: Verifikasi Deployment

Setelah aplikasi dijalankan (baik di lokal maupun setelah di-*deploy* ke HuggingFace/Server), aplikasi STKI akan secara otomatis membaca `DATABASE_URL` tersebut.

Tidak perlu mengubah kode sumber `app_web.py` maupun fungsi algoritma *K-Means*, karena *wrapper* pangkalan data kita (Connection Pooling) bersifat polimorfik dan mendeteksi bahasa *SQL dialect* secara dinamis.
