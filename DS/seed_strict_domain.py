import sqlite3
import os
import requests
import time
import sys
import json

# Setup Database targets and their specific search keywords
# NOTE: db_ekonomi.db is intentionally skipped as it is our "Demo Kontaminasi".
DB_TARGETS = {
    "academic_metadata.db": {
        "name": "Akademik Kampus",
        "keywords": ["Universitas", "Penelitian Ilmiah", "Pendidikan Tinggi", "Jurnal Akademik", "Gelar Sarjana"]
    },
    "db_politik.db": {
        "name": "Politik & Regulasi",
        "keywords": ["Pemilihan Umum", "Dewan Perwakilan Rakyat", "Partai Politik", "Demokrasi", "Kebijakan Publik"]
    },
    "db_bisnis.db": {
        "name": "Bisnis & Korporat",
        "keywords": ["Pasar Saham", "Perusahaan Multinasional", "Ekspor Impor", "Investasi", "Kewirausahaan"]
    },
    "db_etika.db": {
        "name": "Etika & Hak Asasi",
        "keywords": ["Filsafat Moral", "Hak Asasi Manusia", "Etika Profesi", "Norma Sosial", "Keadilan"]
    },
    "academic_demo_real.db": {
        "name": "Teknologi (Demo Real)",
        "keywords": ["Kecerdasan Buatan", "Sistem Komputer", "Teknologi Informasi", "Perangkat Lunak", "Jaringan Komputer"]
    }
}

# Strict Lexical Filter for Contamination Prevention
CONTAMINATION_WORDS = {"lalat", "hewan", "spesies", "habitat", "tumbuhan", "biologi", "kerajaan", "sultan", "sejarah", "kuno", "purba", "mamalia", "burung", "ikan"}

API_URL = "https://id.wikipedia.org/w/api.php"
HEADERS = {'User-Agent': 'STKI_ZeroContamination_Bot/1.0 (https://github.com/your-repo)'}

# Konfigurasi Path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)

# ----------------- FUNGSI UTILITAS -----------------

def print_progress(current, total, prefix='', suffix='', length=40):
    percent = ("{0:.1f}").format(100 * (current / float(total)))
    filled = int(length * current // total)
    bar = '█' * filled + '-' * (length - filled)
    sys.stdout.write(f'\r{prefix} |{bar}| {current}/{total} [{percent}%] {suffix}')
    sys.stdout.flush()
    if current == total:
        print()

def is_contaminated(text):
    text_lower = text.lower()
    bad_count = sum(1 for word in CONTAMINATION_WORDS if word in text_lower)
    return bad_count >= 2  # Strict: Jika ada 2+ kata kontaminasi, DROP!

def get_wiki_search_results(keyword, limit=50, offset=0):
    params = {
        'action': 'query',
        'list': 'search',
        'srsearch': keyword,
        'utf8': 1,
        'format': 'json',
        'srlimit': limit,
        'sroffset': offset
    }
    try:
        r = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
        return r.json().get('query', {}).get('search', [])
    except:
        return []

def get_wiki_page_extract(page_id):
    params = {
        'action': 'query',
        'prop': 'extracts',
        'pageids': page_id,
        'explaintext': 1,
        'format': 'json'
    }
    try:
        r = requests.get(API_URL, params=params, headers=HEADERS, timeout=10)
        pages = r.json().get('query', {}).get('pages', {})
        for pid, pdata in pages.items():
            return pdata.get('extract', '')
    except:
        return ""

def wipe_database(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS documents")
    c.execute("""
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            content TEXT,
            labels TEXT,
            embedding TEXT
        )
    """)
    conn.commit()
    conn.close()

def chunk_text(text, filename_base, target_words=150):
    # Memecah artikel panjang menjadi beberapa dokumen agar dataset kaya secara semantik
    words = text.split()
    chunks = []
    for i in range(0, len(words), target_words):
        chunk = " ".join(words[i:i+target_words])
        if len(chunk.split()) > 50:  # Minimal 50 kata
            chunks.append({
                "filename": f"{filename_base}_part{len(chunks)+1}.txt",
                "content": chunk
            })
    return chunks

# ----------------- PROSES UTAMA -----------------

def run_seeding(target_per_db=200):
    print("\n" + "="*60)
    print("   STKI ZERO-CONTAMINATION SEEDING PROTOCOL (v4.6.0)   ")
    print("="*60)
    print(f"Target: {target_per_db} dokumen per Database.")
    print("Mekanisme: Wikipedia Action API dengan Hard-Lexical Filter.\n")

    for db_file, meta in DB_TARGETS.items():
        db_path = os.path.join(ROOT_DIR, db_file)
        
        print(f"\n[+] Wiping & Preparing Database: {meta['name']} ({db_file})...")
        wipe_database(db_path)
        
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        total_inserted = 0
        keyword_idx = 0
        offset = 0
        
        print_progress(0, target_per_db, prefix=f"Seeding {meta['name']:<20}")
        
        while total_inserted < target_per_db:
            if keyword_idx >= len(meta['keywords']):
                keyword_idx = 0
                offset += 50
                
            current_keyword = meta['keywords'][keyword_idx]
            search_results = get_wiki_search_results(current_keyword, limit=50, offset=offset)
            
            if not search_results:
                keyword_idx += 1
                offset = 0
                time.sleep(1)
                continue
                
            for res in search_results:
                if total_inserted >= target_per_db:
                    break
                    
                page_id = res['pageid']
                title = res['title'].replace(" ", "_")
                
                # Jeda agar tidak terkena Rate Limit 429
                time.sleep(0.5) 
                
                extract = get_wiki_page_extract(page_id)
                if not extract or len(extract.split()) < 50:
                    continue
                    
                # [STRICT PROTOCOL] Cek Kontaminasi sebelum chunking
                if is_contaminated(extract):
                    continue
                    
                chunks = chunk_text(extract, title)
                for chunk in chunks:
                    if total_inserted >= target_per_db:
                        break
                    
                    try:
                        c.execute(
                            "INSERT INTO documents (filename, content, labels, embedding) VALUES (?, ?, ?, ?)",
                            (chunk['filename'], chunk['content'], json.dumps([]), None)  # None for embedding (diisi nanti lewat UI)
                        )
                        total_inserted += 1
                        print_progress(total_inserted, target_per_db, prefix=f"Seeding {meta['name']:<20}")
                    except sqlite3.IntegrityError:
                        pass # Ignore duplicate chunks
                        
            keyword_idx += 1
            
        conn.commit()
        conn.close()
        
    print("\n" + "="*60)
    print("✅ SEEDING SELESAI!")
    print("Seluruh database telah diisi dengan data murni (0% kontaminasi).")
    print("Silakan buka UI, masuk ke masing-masing database, dan klik [EKSEKUSI K-MEANS] untuk membangkitkan taksonomi dan embedding.")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        # Default target = 200 documents per database for fast, clean generation
        run_seeding(target_per_db=200)
    except KeyboardInterrupt:
        print("\n\n[!] Seeding dibatalkan oleh pengguna.")
        sys.exit(0)
