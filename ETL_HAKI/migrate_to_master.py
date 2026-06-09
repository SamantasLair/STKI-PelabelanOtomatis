import os
import sqlite3
import glob
from tqdm import tqdm

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
DB_DIR = os.path.join(PROJECT_ROOT, "_databases")
MASTER_DB_PATH = os.path.join(DB_DIR, "stki_master.db")

def migrate_database(source_db_path, domain_name, master_conn):
    """
    Migrasi 1 file .db (documents, taxonomy_labels, settings) 
    menjadi 3 tabel (tb_docs_X, tb_tax_X, tb_set_X) di stki_master.db.
    """
    master_cursor = master_conn.cursor()
    
    # Buat Schema Tabel Polimorfik untuk Domain ini
    tb_docs = f"tb_docs_{domain_name}"
    tb_tax = f"tb_tax_{domain_name}"
    tb_set = f"tb_set_{domain_name}"
    
    master_cursor.execute(f"DROP TABLE IF EXISTS {tb_docs}")
    master_cursor.execute(f"DROP TABLE IF EXISTS {tb_tax}")
    master_cursor.execute(f"DROP TABLE IF EXISTS {tb_set}")
    
    master_cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {tb_docs} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            content TEXT,
            labels TEXT,
            embedding TEXT
        )
    """)
    master_cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {tb_tax} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            layer TEXT,
            name TEXT UNIQUE
        )
    """)
    master_cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {tb_set} (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    master_conn.commit()

    # Hubungkan ke DB Sumber
    try:
        source_conn = sqlite3.connect(source_db_path)
        source_cursor = source_conn.cursor()
        
        # 1. Migrasi Documents
        source_cursor.execute("SELECT filename, content, labels, embedding FROM documents")
        docs = source_cursor.fetchall()
        if docs:
            master_cursor.executemany(f"""
                INSERT OR REPLACE INTO {tb_docs} (filename, content, labels, embedding)
                VALUES (?, ?, ?, ?)
            """, docs)
            
        # 2. Migrasi Taxonomy Labels
        try:
            source_cursor.execute("SELECT layer, name FROM taxonomy_labels")
            taxes = source_cursor.fetchall()
            if taxes:
                master_cursor.executemany(f"""
                    INSERT OR REPLACE INTO {tb_tax} (layer, name)
                    VALUES (?, ?)
                """, taxes)
        except sqlite3.OperationalError:
            pass # Tabel mungkin tidak ada di DB legacy
            
        # 3. Migrasi Settings
        try:
            source_cursor.execute("SELECT key, value FROM settings")
            sets = source_cursor.fetchall()
            if sets:
                master_cursor.executemany(f"""
                    INSERT OR REPLACE INTO {tb_set} (key, value)
                    VALUES (?, ?)
                """, sets)
        except sqlite3.OperationalError:
            pass # Tabel mungkin tidak ada di DB legacy
            
        master_conn.commit()
        source_conn.close()
        
        return len(docs)
    except Exception as e:
        print(f"[ERROR] Gagal memigrasi {domain_name}: {str(e)}")
        return 0

def main():
    print("="*60)
    print("[*] MEMULAI MIGRASI DATABASE KE stki_master.db [*]")
    print("="*60)
    
    all_dbs = glob.glob(os.path.join(DB_DIR, "*.db"))
    
    # Filter DB yang perlu dimigrasi
    legacy_dbs = []
    for db in all_dbs:
        basename = os.path.basename(db)
        if basename not in ["stki_master.db", "academic_metadata.db"]:
            legacy_dbs.append(db)
            
    if not legacy_dbs:
        print("[!] Tidak ada database legacy yang ditemukan untuk dimigrasi.")
        return
        
    master_conn = sqlite3.connect(MASTER_DB_PATH)
    
    total_migrated = 0
    with tqdm(total=len(legacy_dbs), desc="Migrasi Tabel", unit="db") as pbar:
        for db_path in legacy_dbs:
            basename = os.path.basename(db_path)
            
            # Ekstrak nama domain dari file
            # Contoh: db_politik.db -> politik, academic_demo_real.db -> academic_demo_real
            domain_name = basename.replace(".db", "")
            if domain_name.startswith("db_"):
                domain_name = domain_name[3:]
                
            # Bersihkan karakter spesial agar aman jadi nama tabel
            domain_name = "".join(c for c in domain_name if c.isalnum() or c == '_')
            
            docs_count = migrate_database(db_path, domain_name, master_conn)
            total_migrated += docs_count
            pbar.update(1)
            
    master_conn.close()
    
    print("\n" + "="*60)
    print("[*] MIGRASI SELESAI [*]")
    print(f"Total {len(legacy_dbs)} DB di-shard ke stki_master.db.")
    print(f"Total {total_migrated} baris dokumen diamankan.")
    print("="*60)
    print("PENTING: File .db lama tidak dihapus sebagai cadangan otomatis.")

if __name__ == "__main__":
    main()
