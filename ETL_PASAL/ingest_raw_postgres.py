import os
import json
import glob
from tqdm import tqdm
from dotenv import load_dotenv

try:
    import psycopg2
    from psycopg2.extras import Json
except ImportError:
    print("[FATAL] Modul psycopg2 belum terinstall. Jalankan: pip install psycopg2-binary")
    exit(1)

# ==========================================
# KONFIGURASI GLOBAL
# ==========================================
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "_RawData", "hukum_pasal_id")

def main():
    if not DATABASE_URL:
        print("[FATAL] DATABASE_URL tidak ditemukan di environment variables.")
        return

    print("="*60)
    print("🚀 MEMULAI INGESTI RAW DOKUMEN KE POSTGRESQL 🚀")
    print("="*60)

    # 1. Mendapatkan daftar seluruh berkas JSON
    json_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.json"))
    total_files = len(json_files)

    if total_files == 0:
        print(f"[!] Tidak ada dokumen JSON di {RAW_DATA_DIR}.")
        return

    print(f"[*] Ditemukan {total_files} dokumen JSON siap diproses.")

    try:
        # 2. Koneksi ke Database PostgreSQL
        print("[*] Mencoba terhubung ke PostgreSQL...")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()
        print("[*] Koneksi berhasil.")

        # 3. Pembuatan Tabel (Jika belum ada)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tb_raw_pasal (
                id SERIAL PRIMARY KEY,
                filename TEXT UNIQUE NOT NULL,
                content_json JSONB NOT NULL,
                ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # 4. Memasukkan data ke PostgreSQL
        print("\n[*] Mulai mentransfer data ke PostgreSQL (tb_raw_pasal)...")
        
        with tqdm(total=total_files, desc="Transfer ke DB", unit="doc") as pbar:
            for file_path in json_files:
                filename = os.path.basename(file_path)
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Insert menggunakan JSONB. Gunakan ON CONFLICT untuk menghindari error duplikasi (Idempotency)
                    cursor.execute("""
                        INSERT INTO tb_raw_pasal (filename, content_json) 
                        VALUES (%s, %s)
                        ON CONFLICT (filename) DO UPDATE 
                        SET content_json = EXCLUDED.content_json,
                            ingested_at = CURRENT_TIMESTAMP
                    """, (filename, Json(data)))
                    
                except Exception as e:
                    print(f"\n[ERROR] Gagal memproses {filename}: {str(e)}")
                finally:
                    pbar.update(1)

        conn.commit()
        print("\n" + "="*60)
        print("✅ PROSES TRANSFER SELESAI ✅")
        print(f"Seluruh {total_files} dokumen telah disimpan sebagai JSON mentah (unprocessed) di tb_raw_pasal.")
        print("="*60)

    except psycopg2.Error as db_err:
        print(f"\n[FATAL DB ERROR] {db_err}")
    finally:
        if 'conn' in locals() and conn:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    main()
