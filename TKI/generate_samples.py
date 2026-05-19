import os
import sys

# Inisialisasi otomatis library yang dibutuhkan
try:
    import pandas as pd
    import openpyxl
except ImportError:
    print("[INFO] pandas atau openpyxl belum terinstall. Menginstall secara otomatis...")
    os.system("pip install --user -q pandas openpyxl")
    import pandas as pd
    import openpyxl

print("="*80)
print("GENERATOR SAMPLE EXCEL AKADEMIS (OFFLINE DEMO)")
print("="*80)

# Pastikan direktori TKI aktif
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
os.makedirs(CURRENT_DIR, exist_ok=True)

# 1. Generate File 1: Data Mahasiswa (data_mahasiswa.xlsx)
file_mahasiswa = os.path.join(CURRENT_DIR, "data_mahasiswa.xlsx")
data_mahasiswa = {
    'Nama': ['Budi Santoso', 'Budi Santoso', 'Budi Santoso', 'Ani Wijaya', 'Ani Wijaya', 'Cici Lestari', 'Cici Lestari', 'Dedi Kurnia'],
    'NIM': ['10123001', '10123001', '10123001', '10123002', '10123002', '10123003', '10123003', '10123004'],
    'Semester': [1, 2, 3, 1, 2, 1, 2, 1],
    'Mata_Kuliah': ['Aljabar Linier', 'Kalkulus 2', 'Struktur Data', 'Aljabar Linier', 'Fisika Dasar', 'Kalkulus 2', 'Fisika Dasar', 'Struktur Data'],
    'Nilai': [85, 90, 78, 92, 88, 70, 75, 82],
    'SKS': [3, 4, 3, 3, 3, 4, 3, 3]
}
df_mahasiswa = pd.DataFrame(data_mahasiswa)
df_mahasiswa.to_excel(file_mahasiswa, index=False)
print(f"File 1 Terbuat: {os.path.basename(file_mahasiswa)} [SUKSES]")

# 2. Generate File 2: Data SKS / KRS (data_sks.xlsx)
file_sks = os.path.join(CURRENT_DIR, "data_sks.xlsx")
data_sks = {
    'Kode_Mata_Kuliah': ['IF-101', 'IF-102', 'IF-201', 'IF-202', 'IF-301', 'IF-302'],
    'Nama_Mata_Kuliah': ['Algoritma Pemrograman', 'Matematika Diskrit', 'Struktur Data', 'Aljabar Linier', 'Sistem Operasi', 'Kecerdasan Buatan'],
    'SKS': [4, 3, 3, 3, 4, 3],
    'Jurusan': ['Teknik Informatika', 'Teknik Informatika', 'Teknik Informatika', 'Sistem Informasi', 'Teknik Informatika', 'Sistem Informasi'],
    'Hari': ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Senin'],
    'Ruangan': ['Lab-A', 'Kelas-301', 'Lab-B', 'Kelas-102', 'Lab-A', 'Kelas-204']
}
df_sks = pd.DataFrame(data_sks)
df_sks.to_excel(file_sks, index=False)
print(f"File 2 Terbuat: {os.path.basename(file_sks)} [SUKSES]")

# 3. Generate File 3: Daftar Dosen (daftar_dosen.xlsx)
file_dosen = os.path.join(CURRENT_DIR, "daftar_dosen.xlsx")
data_dosen = {
    'NIP': ['1988021201', '1985041502', '1990113003', '1982071804', '1992032405'],
    'Nama_Dosen': ['Dr. Eng. Hermawan', 'Prof. Dr. Sri Utami', 'Rian Hidayat, M.T.', 'Dr. Diana Putri', 'Fahmi Ichsan, M.Cs.'],
    'Spesialisasi': ['Kecerdasan Buatan & ML', 'Kriptografi & Keamanan Informasi', 'Jaringan Komputer', 'Rekayasa Perangkat Lunak', 'Pemrograman Web & Mobile'],
    'Mata_Kuliah_Diajar': ['Kecerdasan Buatan', 'Matematika Diskrit', 'Algoritma Pemrograman', 'Struktur Data', 'Sistem Operasi'],
    'Fakultas': ['Fakultas Ilmu Komputer', 'Fakultas Ilmu Komputer', 'Fakultas Ilmu Komputer', 'Fakultas Ilmu Komputer', 'Fakultas Ilmu Komputer'],
    'Email': ['hermawan@kampus.ac.id', 'sri.utami@kampus.ac.id', 'rian@kampus.ac.id', 'diana@kampus.ac.id', 'fahmi@kampus.ac.id']
}
df_dosen = pd.DataFrame(data_dosen)
df_dosen.to_excel(file_dosen, index=False)
print(f"File 3 Terbuat: {os.path.basename(file_dosen)} [SUKSES]")

print("\n" + "="*80)
print("KESIMPULAN: 3 BERKAS SAMPLE EXCEL BERHASIL DI-GENERASI DI FOLDER TKI!")
print("="*80)
