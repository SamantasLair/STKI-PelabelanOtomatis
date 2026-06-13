import os
import sqlite3
import re

try:
    import psycopg2
    from psycopg2.extras import DictCursor
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False

DATABASE_URL = os.environ.get("DATABASE_URL")

class CustomCursorWrapper:
    def __init__(self, cursor, is_postgres):
        self.cursor = cursor
        self.is_postgres = is_postgres

    def _translate_query(self, query):
        if not self.is_postgres:
            return query
            
        # 1. Parameter binding: ? -> %s
        # Kita replace ? dengan %s. (Aman karena STKI tidak pakai literal string '?')
        query = query.replace('?', '%s')
        
        # 2. AUTOINCREMENT -> SERIAL
        query = re.sub(r'\bAUTOINCREMENT\b', 'SERIAL', query, flags=re.IGNORECASE)
        
        # 3. JSON array length function translation
        query = re.sub(r'json_array_length\(([^)]+)\)', r'jsonb_array_length(\1::jsonb)', query)
        
        # 4. JSON each translation
        query = re.sub(r'json_each\(([^)]+)\)', r'jsonb_array_elements_text(\1::jsonb) as json_each(value)', query)
        
        # 5. INSERT OR REPLACE -> INSERT ... ON CONFLICT
        if "INSERT OR REPLACE INTO" in query.upper():
            query = re.sub(r'INSERT OR REPLACE INTO ([a-zA-Z0-9_]+) \(([^)]+)\) VALUES \(([^)]+)\)', 
                           r'INSERT INTO \1 (\2) VALUES (\3) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value', 
                           query, flags=re.IGNORECASE)
                           
        # 6. sqlite_master -> information_schema.tables
        if "sqlite_master" in query:
            query = query.replace("sqlite_master", "information_schema.tables")
            query = query.replace("SELECT name", "SELECT table_name")
            query = query.replace("type='table'", "table_schema='public'")
            query = query.replace("name LIKE", "table_name LIKE")
            
        # 7. PRAGMA table_info (SQLite specific) -> PostgreSQL equivalent
        if "PRAGMA table_info" in query:
            # Mengubah "PRAGMA table_info(tb_docs_domain)" 
            # Menjadi select column_name dari information_schema
            match = re.search(r'PRAGMA table_info\(([^)]+)\)', query)
            if match:
                table_name = match.group(1)
                query = f"SELECT ordinal_position, column_name FROM information_schema.columns WHERE table_name = '{table_name}'"

        return query

    def execute(self, query, params=None):
        translated = self._translate_query(query)
        # Fix for PRAGMA table_info translating column shape (app expects column name at index 1)
        # Postgres query above: SELECT ordinal_position, column_name -> column_name is index 1. 
        if params is not None:
            # psycopg2 strict about tuple params, sqlite allows list or tuple
            if isinstance(params, list): params = tuple(params)
            return self.cursor.execute(translated, params)
        return self.cursor.execute(translated)

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

class DBConnection:
    def __init__(self, db_path=None, timeout=15):
        self.is_postgres = bool(DATABASE_URL and HAS_PSYCOPG2)
        if self.is_postgres:
            self.conn = psycopg2.connect(DATABASE_URL)
        else:
            self.conn = sqlite3.connect(db_path, timeout=timeout)
            
    def cursor(self):
        # Kembalikan wrapped cursor
        return CustomCursorWrapper(self.conn.cursor(), self.is_postgres)

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()

# Alias execute_query agar tidak breaking
def execute_query(conn, query, params=(), commit=False, fetchone=False, fetchall=False):
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if commit:
            conn.commit()
        if fetchone:
            return cursor.fetchone()
        if fetchall:
            return cursor.fetchall()
    finally:
        # Psycopg2 cursors are generally cleaned up with conn, but safe to close
        pass
