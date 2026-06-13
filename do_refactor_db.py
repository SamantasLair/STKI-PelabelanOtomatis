import os
import re

file_path = "TKI/app_web.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Tambahkan import jika belum ada
if "from TKI.database import DBConnection" not in content:
    # Sisipkan setelah import sqlite3
    content = content.replace("import sqlite3", "import sqlite3\nfrom TKI.database import DBConnection, execute_query")

# Ganti sqlite3.connect(...) menjadi DBConnection(...)
content = re.sub(r'sqlite3\.connect\(([^)]+)\)', r'DBConnection(\1)', content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Berhasil")
