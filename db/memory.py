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
            conn.execute(
                "CREATE TABLE IF NOT EXISTS _migrations (id TEXT PRIMARY KEY)"
            )
        self._run_migrations()

    def _run_migrations(self):
        with self.get_conn() as conn:
            # v1 — 5-digit prefix match (kept for idempotency)
            cur = conn.execute(
                "SELECT 1 FROM _migrations WHERE id = 'split_tribunal_sources'"
            )
            if not cur.fetchone():
                self._migrate_tribunal_sources(conn, prefix_len=5)
                conn.execute("INSERT INTO _migrations VALUES ('split_tribunal_sources')")

            # v2 — 2-digit department prefix; catches municipal radicados and Bogotá DC
            cur = conn.execute(
                "SELECT 1 FROM _migrations WHERE id = 'split_tribunal_sources_v2'"
            )
            if not cur.fetchone():
                self._migrate_tribunal_sources(conn, prefix_len=2)
                conn.execute("INSERT INTO _migrations VALUES ('split_tribunal_sources_v2')")

            # v3 — add local_path column for Drive pending-upload lookup
            cur = conn.execute(
                "SELECT 1 FROM _migrations WHERE id = 'add_local_path'"
            )
            if not cur.fetchone():
                conn.execute(
                    "ALTER TABLE downloaded ADD COLUMN local_path TEXT"
                )
                conn.execute("INSERT INTO _migrations VALUES ('add_local_path')")

    def _migrate_tribunal_sources(self, conn, prefix_len: int):
        """Map 'Tribunales Administrativos' rows to per-tribunal names.

        Uses the first `prefix_len` chars of the radicado (title) to identify the
        department — each tribunal's corp_code starts with the departmental DANE code.
        Bogotá DC (dept 11) is also mapped to Cundinamarca's tribunal (corp_code 2500023).
        """
        from scrappers.samai import _SAMAI_CORPS as _TRIBUNALES

        # Build dept-prefix → tribunal-name mapping
        prefix_map = {}
        for corp_code, corp_name in _TRIBUNALES.items():
            prefix_map[corp_code[:prefix_len]] = corp_name

        # Bogotá DC (11) falls under the Cundinamarca tribunal
        if prefix_len == 2 and "2500023"[:2] in prefix_map:
            prefix_map["11"] = prefix_map["25"]

        for prefix, corp_name in prefix_map.items():
            conn.execute(
                "UPDATE downloaded SET source = ? "
                "WHERE source = 'Tribunales Administrativos' AND title LIKE ?",
                (corp_name, f"{prefix}%"),
            )
        logging.info("Migration split_tribunal_sources (prefix_len=%d) completed.", prefix_len)

    def get_conn(self):
        return sqlite3.connect(DB_PATH)

    def seen(self, doc_id):
        with self.get_conn() as conn:
            cur = conn.execute(
                "SELECT 1 FROM downloaded WHERE doc_id = ?",
                (doc_id,)
            )
            return cur.fetchone() is not None

    def get_doc_by_id(self, doc_id: str) -> dict | None:
        with self.get_conn() as conn:
            cur = conn.execute(
                "SELECT source, title, f_public FROM downloaded WHERE doc_id = ?", (doc_id,)
            )
            row = cur.fetchone()
            return {"source": row[0], "title": row[1], "f_public": row[2]} if row else None

    def get_doc_id_by_local_path(self, rel_path: str) -> str | None:
        with self.get_conn() as conn:
            cur = conn.execute(
                "SELECT doc_id FROM downloaded WHERE local_path = ?", (rel_path,)
            )
            row = cur.fetchone()
            return row[0] if row else None

    def mark(self, doc_id, doc: RawDocModel, local_path: str | None = None):
        with self.get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO downloaded(doc_id, source, title, f_public, downloaded_at, local_path) "
                "VALUES (?, ?, ?, ?, datetime('now'), ?)",
                (doc_id, doc['source'], doc["title"], doc["f_public"], local_path)
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

    def get_counts_by_source(self):
        """Return list of (source, count) sorted by count descending."""
        with self.get_conn() as conn:
            cur = conn.execute(
                "SELECT source, COUNT(*) as cnt FROM downloaded GROUP BY source ORDER BY cnt DESC"
            )
            return [(row[0], row[1]) for row in cur.fetchall()]

    def get_counts_grouped(self):
        """Return counts grouped by entity family.

        Returns list of (display_name, total, children) where children is a list of
        (source, count) tuples. Single-scraper sources have an empty children list.
        Sources that share a common family (e.g. all Tribunal Administrativo X) are
        collapsed into one parent row with the individual breakdown as children.
        """
        flat = self.get_counts_by_source()
        adm_children = []
        sup_children = []
        singles = []

        for source, count in flat:
            if source.startswith("Tribunal Administrativo"):
                adm_children.append((source, count))
            elif source.startswith("Tribunal Superior"):
                sup_children.append((source, count))
            else:
                singles.append((source, count, []))

        result = list(singles)
        if adm_children:
            total = sum(c for _, c in adm_children)
            result.append(("Tribunales Administrativos", total, adm_children))
        if sup_children:
            total = sum(c for _, c in sup_children)
            result.append(("Tribunales Superiores", total, sup_children))

        result.sort(key=lambda x: -x[1])
        return result

    def get_all_downloaded(self, source=None):
        """Return all downloaded documents from the database."""
        with self.get_conn() as conn:
            if source:
                cur = conn.execute(
                    "SELECT doc_id, source, title, f_public, downloaded_at FROM downloaded WHERE source = ? ORDER BY downloaded_at DESC",
                    (source,),
                )
            else:
                cur = conn.execute(
                    "SELECT doc_id, source, title, f_public, downloaded_at FROM downloaded ORDER BY downloaded_at DESC"
                )
            rows = cur.fetchall()

        return [
            {
                "doc_id": r[0],
                "source": r[1],
                "title": r[2],
                "f_public": r[3],
                "downloaded_at": r[4],
            }
            for r in rows
        ]