import os
import re

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
APP_WEB_PATH = os.path.join(CURRENT_DIR, "TKI", "app_web.py")

with open(APP_WEB_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace Top-Level DB state
content = re.sub(
    r'def get_available_databases\(\):.*?return dbs\n',
    r'''def get_available_domains():
    domains = []
    master_path = os.path.join(DB_DIR, "stki_master.db")
    if os.path.exists(master_path):
        try:
            conn = sqlite3.connect(master_path)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'tb_docs_%'")
            for row in c.fetchall():
                domains.append(row[0].replace('tb_docs_', ''))
            conn.close()
        except:
            pass
    if not domains:
        domains = ["default"]
    return domains
''', content, flags=re.DOTALL)

content = re.sub(
    r'def get_active_db_type\(\):.*?return dbs\[0\] if dbs else "default\.db"\n',
    r'''def get_active_domain():
    state_file = os.path.join(DB_DIR, "active_db.txt")
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r') as f:
                target = f.read().strip()
                if target in get_available_domains():
                    return target
        except:
            pass
    return get_available_domains()[0]
''', content, flags=re.DOTALL)

# Delete get_active_db_path
content = re.sub(r'def get_active_db_path\(\):\n    return os\.path\.join\(DB_DIR, get_active_db_type\(\)\)\n', '', content)

content = re.sub(
    r'def set_active_db_type\(target\):',
    r'def set_active_domain(target):', content
)

content = re.sub(
    r'active_db_type = get_active_db_type\(\)\nif not get_available_databases\(\):\n    open\(get_active_db_path\(\), \'a\'\)\.close\(\)\nactive_db_path = get_active_db_path\(\)',
    r'''active_domain = get_active_domain()
MASTER_DB_PATH = os.path.join(DB_DIR, "stki_master.db")
if not os.path.exists(MASTER_DB_PATH):
    open(MASTER_DB_PATH, 'a').close()''', content
)

# 2. sync_global_db_state
content = re.sub(
    r'def sync_global_db_state\(\):\n    global active_db_type, active_db_path, TAXONOMY, DB_EMBEDDING_CACHE\n    current_type = get_active_db_type\(\)\n    if \'active_db_type\' not in globals\(\) or active_db_type != current_type:\n        active_db_type = current_type\n        active_db_path = get_active_db_path\(\)\n        TAXONOMY = load_taxonomy\(active_db_path\)',
    r'''def sync_global_db_state():
    global active_domain, TAXONOMY, DB_EMBEDDING_CACHE
    current_domain = get_active_domain()
    if 'active_domain' not in globals() or active_domain != current_domain:
        active_domain = current_domain
        TAXONOMY = load_taxonomy(active_domain)''', content
)

# 3. get_db_embedding
content = content.replace("def get_db_embedding(active_db_type, doc_id, emb_str):", "def get_db_embedding(active_domain, doc_id, emb_str):")

# 4. load_taxonomy
content = re.sub(
    r'def load_taxonomy\(db_path\):.*?try:\n        conn = sqlite3\.connect\(db_path, timeout=15\)',
    r'''def load_taxonomy(domain):
    tax = {"Layer_1_Domain": [], "Layer_2_Detail": [], "threshold_l1": 0.50, "threshold_l2": 0.55}
    try:
        conn = sqlite3.connect(MASTER_DB_PATH, timeout=15)''', content, flags=re.DOTALL
)
content = content.replace("CREATE TABLE IF NOT EXISTS taxonomy_labels", "CREATE TABLE IF NOT EXISTS tb_tax_{domain}")
content = content.replace("CREATE TABLE IF NOT EXISTS settings", "CREATE TABLE IF NOT EXISTS tb_set_{domain}")
content = content.replace("FROM taxonomy_labels", "FROM tb_tax_{domain}")
content = content.replace("FROM settings", "FROM tb_set_{domain}")

# fix the f-strings inside load_taxonomy: we need them to evaluate dynamically in Python
content = re.sub(r'c\.execute\("CREATE TABLE IF NOT EXISTS tb_tax_\{domain\}', r'c.execute(f"CREATE TABLE IF NOT EXISTS tb_tax_{domain}', content)
content = re.sub(r'c\.execute\("CREATE TABLE IF NOT EXISTS tb_set_\{domain\}', r'c.execute(f"CREATE TABLE IF NOT EXISTS tb_set_{domain}', content)
content = re.sub(r'c\.execute\("SELECT name FROM tb_tax_\{domain\}', r'c.execute(f"SELECT name FROM tb_tax_{domain}', content)
content = re.sub(r'c\.execute\("SELECT key, value FROM tb_set_\{domain\}', r'c.execute(f"SELECT key, value FROM tb_set_{domain}', content)

# 5. save_setting
content = re.sub(
    r'def save_setting\(db_path, key, value\):\n    try:\n        conn = sqlite3\.connect\(db_path, timeout=15\)\n        c = conn\.cursor\(\)\n        c\.execute\("CREATE TABLE IF NOT EXISTS tb_set_\{domain\}.*?c\.execute\("INSERT OR REPLACE INTO tb_set_\{domain\}',
    r'''def save_setting(domain, key, value):
    try:
        conn = sqlite3.connect(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS tb_set_{domain} (key TEXT PRIMARY KEY, value TEXT)")
        c.execute(f"INSERT OR REPLACE INTO tb_set_{domain}''', content, flags=re.DOTALL
)

# 6. save_taxonomy
content = re.sub(
    r'def save_taxonomy\(db_type, taxonomy_dict\):\n    db_path = os\.path\.join\(DB_DIR, db_type\)\n    try:\n        conn = sqlite3\.connect\(db_path, timeout=15\)\n        c = conn\.cursor\(\)\n        c\.execute\("CREATE TABLE IF NOT EXISTS tb_tax_\{domain\}.*?c\.execute\("DELETE FROM tb_tax_\{domain\}"\)',
    r'''def save_taxonomy(domain, taxonomy_dict):
    try:
        conn = sqlite3.connect(MASTER_DB_PATH, timeout=15)
        c = conn.cursor()
        c.execute(f"CREATE TABLE IF NOT EXISTS tb_tax_{domain} (id INTEGER PRIMARY KEY AUTOINCREMENT, layer TEXT, name TEXT UNIQUE)")
        c.execute(f"DELETE FROM tb_tax_{domain}")''', content, flags=re.DOTALL
)
content = re.sub(r'c\.execute\("INSERT INTO tb_tax_\{domain\}', r'c.execute(f"INSERT INTO tb_tax_{domain}', content)

# Replace remaining active_db_path with MASTER_DB_PATH
content = content.replace("active_db_path", "MASTER_DB_PATH")

# Replace all occurrences of sqlite3.connect(get_active_db_path()...) with MASTER_DB_PATH
content = content.replace("sqlite3.connect(get_active_db_path()", "sqlite3.connect(MASTER_DB_PATH")

# Generic SQL Replacements (Dangerous, but handled with format strings)
content = content.replace("FROM documents", "FROM tb_docs_{active_domain}")
content = content.replace("INTO documents", "INTO tb_docs_{active_domain}")
content = content.replace("UPDATE documents", "UPDATE tb_docs_{active_domain}")
content = content.replace("TABLE documents", "TABLE tb_docs_{active_domain}")
content = content.replace("table_info(documents)", "table_info(tb_docs_{active_domain})")
content = content.replace("documents.labels", "tb_docs_{active_domain}.labels")
content = content.replace("documents.id", "tb_docs_{active_domain}.id")

content = content.replace("INTO taxonomy_labels", "INTO tb_tax_{active_domain}")
content = content.replace("UPDATE taxonomy_labels", "UPDATE tb_tax_{active_domain}")
content = content.replace("FROM taxonomy_labels", "FROM tb_tax_{active_domain}")

# Fix f-strings where we injected {active_domain} inside an already f-string or normal string
def fix_sql_fstrings(match):
    s = match.group(0)
    if not s.startswith('f"'):
        return f'f"{s[1:]}' # Convert to f-string
    return s

content = re.sub(r'".*?tb_docs_\{active_domain\}.*?"', fix_sql_fstrings, content)
content = re.sub(r'".*?tb_tax_\{active_domain\}.*?"', fix_sql_fstrings, content)
content = re.sub(r'".*?tb_set_\{active_domain\}.*?"', fix_sql_fstrings, content)

# Fix multi-line strings
content = re.sub(r'""".*?tb_docs_\{active_domain\}.*?"""', lambda m: f'f{m.group(0)}' if not m.group(0).startswith('f') else m.group(0), content, flags=re.DOTALL)

with open(APP_WEB_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("[*] Refactoring string selesai.")
