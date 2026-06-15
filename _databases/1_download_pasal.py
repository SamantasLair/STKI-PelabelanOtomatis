import os
import sys

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
INGEST_SCRIPT = os.path.join(PROJECT_ROOT, "ETL_HAKI", "ingest_pasal.py")

def main():
    print("="*60)
    print("MEMULAI PENGUNDUHAN DATA LOKAL DARI API PASAL.ID")
    print("="*60)
    
    # Memanggil skrip utama ETL_HAKI/ingest_pasal.py
    # Skrip ini akan mengunduh file JSON mentah ke _RawData/hukum_pasal_id/
    exit_code = os.system(f'python "{INGEST_SCRIPT}"')
    
    if exit_code == 0:
        print("\n✅ Pengunduhan berhasil. Lanjutkan ke langkah 2 (2_process_to_sqlite.py).")
    else:
        print("\n❌ Terjadi kesalahan saat mengunduh data.")

if __name__ == "__main__":
    main()
