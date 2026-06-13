# Panduan Cepat Deployment Aplikasi STKI (Tanpa Model Berat)

Karena aplikasi ini dibangun menggunakan arsitektur Python (*Flask*) dan sudah dilengkapi dengan `Dockerfile` standar industri, platform terbaik, gratis, dan paling profesional untuk memamerkan proyek Data Science Anda adalah **Hugging Face Spaces**.

Berikut adalah langkah paling sederhana untuk melakukan *deployment*:

## Opsi 1: Menggunakan Git (Paling Cepat & Profesional)

Hugging Face Space pada dasarnya adalah sebuah repositori Git (sama seperti GitHub). Anda bisa langsung mem-*push* kode lokal Anda ke server mereka:

1. **Buat Space di Hugging Face:**
   - Masuk ke [huggingface.co/spaces](https://huggingface.co/spaces).
   - Klik tombol **Create new Space**.
   - **Space name**: Bebas (misal: `stki-hukum-app`).
   - **Select the Space SDK**: Pilih **Docker** (lalu pilih *Blank*).
   - Klik **Create Space**.

2. **Push Kode via Terminal/CMD:**
   - Setelah Space terbuat, Hugging Face akan memberikan URL Git (contoh: `https://huggingface.co/spaces/username/stki-hukum-app`).
   - Buka Terminal/CMD di komputer Anda, pastikan Anda berada di folder proyek `UAS`, lalu jalankan perintah berikut secara berurutan:
     ```bash
     git init
     git add .
     git commit -m "Initial deploy tanpa model ONNX"
     git remote add origin https://huggingface.co/spaces/username-anda/nama-space-anda
     git push -u origin main
     ```
   - *(Hugging Face mungkin akan meminta Username dan Password. Gunakan **Access Token** dari menu Settings akun Hugging Face Anda sebagai password).*

3. Hugging Face akan otomatis membaca `Dockerfile` yang baru saja Anda dorong (*push*) dan memulai proses *Build*!

---

## Opsi 2: Upload Langsung ke Hugging Face (Tanpa GitHub)

Jika Anda tidak terbiasa dengan GitHub, Anda bisa langsung mengunggahnya:

1. Buat *Space* baru di Hugging Face dengan SDK **Docker** seperti pada Opsi 1.
2. Buka tab **Files** di dalam *Space* Anda.
3. Klik **Add File** -> **Upload Files**.
4. Tarik dan lepas (*Drag & Drop*) **seluruh file dan folder** yang ada di dalam proyek lokal Anda ke sana (kecuali folder `_RawData`, `_Fondasi`, dan file `.docx`). Pastikan file `Dockerfile`, `requirements.txt`, dan folder `TKI` serta `_UIUX` ikut terunggah.
5. Klik **Commit changes**.
6. Hugging Face akan langsung mendeteksi `Dockerfile` dan menjalankan proses *Building*. Tunggu sekitar 2-3 menit.

---

## Yang Akan Terjadi Setelah Deploy (Mode Fallback)

Karena file model `multi_label_model.onnx` sengaja kita tinggalkan di komputer lokal Anda:
1. **Sistem Tidak Akan Crash:** Aplikasi akan tetap hidup dan menampilkan desain *Playful Brutalism* secara utuh.
2. **Dashboard Looker Studio:** Akan otomatis muncul dan langsung mengambil grafik visual (karena *iframe* bergantung pada jaringan Google, bukan CPU aplikasi).
3. **Pencarian Kata Kunci:** Fitur pencarian akan otomatis beralih menggunakan mesin **BM25 Lexical** secara murni. Jika Anda mencari "presiden", sistem tetap akan memunculkan dokumen yang mengandung kata presiden.

Cukup kumpulkan URL *Hugging Face Space* tersebut (contoh: `https://huggingface.co/spaces/username-anda/stki-hukum-app`) kepada dosen Anda!
