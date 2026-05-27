import sqlite3
import os
import sys
import json
import numpy as np
import requests
import math
import time
import random
import traceback
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'TKI')))
from app_web import get_onnx_embedding

DB_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DATABASES = {
    "akademik": os.path.join(DB_DIR, 'academic_demo_real.db'),
    "politik": os.path.join(DB_DIR, 'db_politik.db'),
    "ekonomi": os.path.join(DB_DIR, 'db_ekonomi.db'),
    "bisnis": os.path.join(DB_DIR, 'db_bisnis.db'),
    "etika": os.path.join(DB_DIR, 'db_etika.db'),
    "demo_real": os.path.join(DB_DIR, 'db_demo_real.db')
}

CATEGORIES = {
    "akademik": "Kategori:Pendidikan_di_Indonesia",
    "politik": "Kategori:Politik_Indonesia",
    "ekonomi": "Kategori:Ekonomi_Indonesia",
    "bisnis": "Kategori:Perusahaan_Indonesia",
    "etika": "Kategori:Hak_asasi_manusia",
    "demo_real": "Kategori:Ilmu_pengetahuan"
}

def create_table_if_not_exists(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS documents")
    c.execute('''
        CREATE TABLE documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            content TEXT,
            labels TEXT,
            embedding TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_articles_from_category(category, limit=1000):
    url = "https://id.wikipedia.org/w/api.php"
    titles = set()
    cmcontinue = None
    
    print(f"Mengumpulkan judul dari {category}...")
    while len(titles) < limit:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmlimit": "500",
            "cmtype": "page",
            "format": "json"
        }
        if cmcontinue:
            params["cmcontinue"] = cmcontinue
            
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if 'query' in data and 'categorymembers' in data['query']:
                for page in data['query']['categorymembers']:
                    titles.add(page['title'])
                    if len(titles) >= limit:
                        break
            
            if 'continue' in data:
                cmcontinue = data['continue']['cmcontinue']
            else:
                break
        except Exception as e:
            print(f"Error fetching category {category}: {e}")
            break
            
    while len(titles) < limit:
        params = {
            "action": "query",
            "generator": "random",
            "grnnamespace": "0",
            "grnlimit": "50",
            "format": "json"
        }
        try:
            r = requests.get(url, params=params, timeout=10)
            data = r.json()
            if 'query' in data and 'pages' in data['query']:
                for page_id, page in data['query']['pages'].items():
                    titles.add(page['title'])
                    if len(titles) >= limit:
                        break
        except Exception as e:
            time.sleep(2)
            continue
            
    return list(titles)[:limit]

def fetch_page_content_and_tables(title):
    url = "https://id.wikipedia.org/w/api.php"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    params_text = {
        "action": "query",
        "prop": "extracts",
        "explaintext": 1,
        "titles": title,
        "format": "json"
    }
    
    content = None
    try:
        r = requests.get(url, params=params_text, headers=headers, timeout=10)
        data = r.json()
        pages = data.get('query', {}).get('pages', {})
        for page_id, page in pages.items():
            if 'extract' in page:
                content = page['extract'].strip()
                break
    except Exception as e:
        pass

    # Ambil data tabel secara riil tanpa sintesis
    table_csv = None
    if content and len(content) > 200:
        try:
            from io import StringIO
            # Mencoba membaca tabel HTML aktual dari wikipedia dengan custom headers
            page_url = f"https://id.wikipedia.org/wiki/{title.replace(' ', '_')}"
            r_html = requests.get(page_url, headers=headers, timeout=10)
            dfs = pd.read_html(StringIO(r_html.text))
            if dfs and len(dfs) > 0:
                # Ambil tabel dengan baris terbanyak
                best_df = max(dfs, key=len)
                if len(best_df) > 2:
                    table_csv = best_df.to_csv(index=False)
        except Exception as e:
            pass
            
    return title, content, table_csv

def seed_database(db_key, db_path):
    print(f"\n--- Memulai Seeding {db_key.upper()} (Target: 1000) ---")
    create_table_if_not_exists(db_path)
    
    category = CATEGORIES.get(db_key, "Kategori:Indonesia")
    titles = get_articles_from_category(category, limit=2000) # Ambil banyak untuk buffer karena tidak semua punya tabel
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    success_count = 0
    pdf_count, docx_count, csv_count, xlsx_count = 0, 0, 0, 0
    
    def process_title(title):
        t, content, table_csv = fetch_page_content_and_tables(title)
        if not content or len(content) < 200:
            return None
            
        content = content[:10000]
        
        # Alokasi kuota format: 400 PDF, 300 DOCX, 150 CSV, 150 XLSX
        nonlocal pdf_count, docx_count, csv_count, xlsx_count
        
        ext = None
        final_content = None
        
        # Prioritaskan mengisi CSV/XLSX jika tabel riil ditemukan
        if table_csv and (csv_count < 150 or xlsx_count < 150):
            if csv_count <= xlsx_count:
                ext = ".csv"
                final_content = table_csv[:10000] # Batasi ukuran
                csv_count += 1
            else:
                ext = ".xlsx"
                final_content = f"Dokumen spreadsheet tabel.\nData Real:\n{table_csv[:10000]}"
                xlsx_count += 1
        else:
            if pdf_count < 400:
                ext = ".pdf"
                final_content = content
                pdf_count += 1
            elif docx_count < 300:
                ext = ".docx"
                final_content = content
                docx_count += 1
            else:
                return None
                
        if not ext:
            return None
            
        safe_title = "".join([char if char.isalnum() else "_" for char in t])
        filename = f"{safe_title}{ext}"
        
        try:
            emb = get_onnx_embedding(final_content)
            return (filename, final_content, json.dumps([]), json.dumps(emb.tolist()))
        except Exception as e:
            return None

    # Eksekusi serial untuk keamanan Thread Local (ONNX Runtime dan SQLite cursor conflicts)
    for title in titles:
        if success_count >= 1000:
            break
            
        res = process_title(title)
        if res:
            try:
                c.execute("INSERT INTO documents (filename, content, labels, embedding) VALUES (?, ?, ?, ?)", res)
                conn.commit()
                success_count += 1
                if success_count % 10 == 0:
                    print(f"[{db_key.upper()}] Progress: {success_count} / 1000 (PDF:{pdf_count} DOCX:{docx_count} CSV:{csv_count} XLSX:{xlsx_count})")
            except sqlite3.IntegrityError:
                pass
            
    conn.close()
    print(f"--- Selesai Seeding {db_key.upper()}: {success_count} dokumen dimasukkan ---")

if __name__ == "__main__":
    for key, path in DATABASES.items():
        seed_database(key, path)
    
    print("\n[+] MASSIVE SEEDING SELESAI UNTUK 6 DATABASE!")
