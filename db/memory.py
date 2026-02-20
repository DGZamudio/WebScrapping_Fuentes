from datetime import datetime
import logging
import sqlite3
from config.config import DB_PATH
from models.models import RawDocModel

class Memory:
    def __init__(self):
        with self.get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloaded (
                    doc_id TEXT PRIMARY KEY,
                    source TEXT,
                    title TEXT,
                    f_public DATETIME,
                    downloaded_at DATETIME
                )
            """)

    def get_conn(self):
        return sqlite3.connect(DB_PATH)

    def seen(self, doc_id):
        with self.get_conn() as conn:
            cur = conn.execute(
                "SELECT 1 FROM downloaded WHERE doc_id = ?",
                (doc_id,)
            )
            return cur.fetchone() is not None

    def mark(self, doc_id, doc:RawDocModel):
        with self.get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO downloaded(doc_id, source, title, f_public, downloaded_at) VALUES (?, ?, ?, ?, datetime('now'))",
                (doc_id, doc['source'], doc["title"], doc["f_public"])
            )

    def get_last_inserted(self, source=None):
        with self.get_conn() as conn:
            cur = conn.execute("""
                SELECT f_public FROM downloaded
                ORDER BY f_public DESC
                LIMIT 1
            """)
            if source:
                cur = conn.execute("""
                    SELECT f_public FROM 'downloaded'
                    WHERE source = ?
                    ORDER BY f_public DESC
                    LIMIT 1
                """, (source,))

            ultima_fecha = cur.fetchone()

            if not ultima_fecha:
                hoy = datetime.now().strftime("%Y-%m-%d")
                ultima_fecha = [hoy]

            logging.info(f"Empezando desde: {ultima_fecha[0]}")

            return ultima_fecha[0]

    def total_docs(self, source=None):
        with self.get_conn() as conn:
            if source:
                cur = conn.execute("SELECT COUNT(*) FROM downloaded WHERE source = ?", (source,))
            else:
                cur = conn.execute("SELECT COUNT(*) FROM downloaded")
            row = cur.fetchone()
            return row[0] if row else 0