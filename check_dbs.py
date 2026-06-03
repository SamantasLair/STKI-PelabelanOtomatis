import sqlite3
import os

dbs = [
    'academic_metadata.db', 
    'academic_demo_real.db', 
    'db_politik.db', 
    'db_ekonomi.db', 
    'db_bisnis.db', 
    'db_etika.db'
]

for db in dbs:
    if os.path.exists(db):
        try:
            conn = sqlite3.connect(db)
            c = conn.cursor()
            c.execute("SELECT COUNT(1) FROM documents")
            count = c.fetchone()[0]
            print(f"{db}: {count} docs")
            conn.close()
        except Exception as e:
            print(f"{db}: ERROR - {e}")
    else:
        print(f"{db}: NOT FOUND")
