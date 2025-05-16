
import sqlite3
import hashlib


import threading

class RequestCache(object):
    db_path = ""
    db_conn = None
    db_cursor = None
    def __init__(self, tar_path):
        self.db_path = tar_path
        self.db_conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute("""
            CREATE TABLE IF NOT EXISTS request_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_hash VARCHAR(70),
                request_content TEXT,
                response_content TEXT
            );
        """)
        self.db_conn.commit()
        self.lock = threading.Lock()
        
    
    def add_request_cache(self, request_content, response_content):
        
        request_hash = hashlib.sha256(request_content.encode()).hexdigest()
        
        self.lock.acquire()
        
        self.db_cursor.execute("""
            INSERT INTO request_cache (request_hash, request_content, response_content)
            VALUES (?, ?, ?)
        """, (request_hash, request_content, response_content))
        self.db_conn.commit()
        
        self.lock.release()
    
    def get_request_cache(self, request_content):
        request_hash = hashlib.sha256(request_content.encode()).hexdigest()
        
        self.lock.acquire()
        
        self.db_cursor.execute("""
            SELECT request_content, response_content FROM request_cache WHERE request_hash = ?
        """, (request_hash,))
        res = self.db_cursor.fetchone()
        
        self.lock.release()
        
        if res and res[0] == request_content:
            return res[1]
        else:
            return None



