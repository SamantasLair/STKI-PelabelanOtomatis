import os
import sqlite3
import json
import glob

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "_RawData", "hukum_pasal_id")
DB_PATH = os.path.join(CURRENT_DIR, "stki_master.db")

def main():
    print("="*60)
    print("MEMULAI INJEKSI MENTAH KE DATABASE LOKAL (TANPA ONNX)")
    print("="*60)
    
    if not os.path.exists(RAW_DATA_DIR):
        print(f"[X] Direktori {RAW_DATA_DIR} tidak ditemukan. Jalankan langkah 1 terlebih dahulu.")
        return

    json_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.json"))
    if not json_files:
        print(f"[X] Tidak ada file JSON di {RAW_DATA_DIR}.")
        return

    print(f"-> Menemukan {len(json_files)} file dokumen mentah.")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Pastikan tabel tb_docs_hukum ada
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tb_docs_hukum (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            content TEXT,
            labels TEXT,
            embedding TEXT
        )
    """)
    
    success_count = 0
    for idx, filepath in enumerate(json_files):
        filename = os.path.basename(filepath)
        with open(filepath, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Ekstrak konten teks mentah sesuai struktur API Pasal.id
                work_data = data.get("work", {})
                title = work_data.get("title", filename)
                articles_list = data.get("articles", [])
                
                content_parts = [f"=== JUDUL DOKUMEN ===\n{title}"]
                for article in articles_list:
                    a_type = str(article.get("type") or "").capitalize()
                    a_number = str(article.get("number") or "")
                    a_content = str(article.get("content") or "")
                    
                    if a_content.strip():
                        content_parts.append(f"--- {a_type} {a_number} ---\n{a_content.strip()}")
                
                full_content = "\n\n".join(content_parts)
                
                # Injeksi ke SQLite TANPA proses ONNX
                # Membiarkan labels = [] dan embedding = NULL
                cursor.execute(
                    "INSERT OR REPLACE INTO tb_docs_hukum (filename, content, labels, embedding) VALUES (?, ?, ?, ?)",
                    (filename, full_content, '[]', None)
                )
                success_count += 1
                
                if (idx + 1) % 100 == 0:
                    print(f"  [Sedang Memproses] {idx + 1} / {len(json_files)} dokumen...")
                    
            except Exception as e:
                print(f"  [Error] Gagal membaca {filename}: {e}")
                
    conn.commit()
    conn.close()
    
    print("\n[V] Injeksi selesai!")
    print(f"[V] {success_count} dokumen telah masuk ke stki_master.db (tb_docs_hukum).")

if __name__ == "__main__":
    main()
