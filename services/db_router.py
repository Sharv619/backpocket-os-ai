"""
DB Router — transparently switches between SQLite (default) and Postgres.
Now supports DUAL-WRITE: writes to both, reads from Postgres (if available).
"""
import os
import logging
import sqlite3
import threading
from pathlib import Path

logger = logging.getLogger(__name__)

SQLITE_PATH = Path(__file__).resolve().parent.parent / "backpocket.db"
POSTGRES_URL = os.environ.get(
    "POSTGRES_DB_URL", 
    "postgresql+psycopg2://backpocket_user:backpocket_password@localhost:5432/backpocket_db"
)

def _postgres_available() -> bool:
    if not POSTGRES_URL:
        return False
    try:
        import psycopg2
        # Try a quick connection
        conn = psycopg2.connect(POSTGRES_URL, connect_timeout=2)
        conn.close()
        return True
    except Exception:
        return False

DB_BACKEND: str = "postgres" if _postgres_available() else "sqlite"
logger.info(f"Database Backend: {DB_BACKEND}")

class DualWriteCursor:
    def __init__(self, pg_cursor, sl_cursor):
        self.pg_cursor = pg_cursor
        self.sl_cursor = sl_cursor

    def execute(self, query, params=None):
        # 1. Execute on Postgres (Primary)
        pg_res = None
        if self.pg_cursor:
            # Simple SQL translation for common differences
            pg_query = query.replace("INSERT OR IGNORE", "INSERT").replace("INSERT OR REPLACE", "INSERT")
            if "INSERT" in pg_query.upper() and "ON CONFLICT" not in pg_query.upper():
                # Note: This is a very basic translation. Complex queries might need manual handling.
                if "processed_messages" in pg_query:
                    pg_query += " ON CONFLICT (message_id) DO NOTHING"
                elif "pending_approvals" in pg_query:
                    pg_query += " ON CONFLICT (ref_id) DO UPDATE SET updated_at = EXCLUDED.updated_at"
            
            try:
                pg_res = self.pg_cursor.execute(pg_query, params or ())
            except Exception as e:
                logger.error(f"Postgres Execute Error: {e}")
        
        # 2. Execute on SQLite (Fallback/Mirror)
        if self.sl_cursor:
            try:
                sl_query = query.replace("%s", "?")
                self.sl_cursor.execute(sl_query, params or ())
            except Exception as e:
                logger.error(f"SQLite Execute Error: {e}")
        
        return pg_res

    def fetchone(self):
        return self.pg_cursor.fetchone() if self.pg_cursor else self.sl_cursor.fetchone()

    def fetchall(self):
        return self.pg_cursor.fetchall() if self.pg_cursor else self.sl_cursor.fetchall()

    def __iter__(self):
        return iter(self.pg_cursor) if self.pg_cursor else iter(self.sl_cursor)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.pg_cursor and hasattr(self.pg_cursor, 'close'):
            self.pg_cursor.close()
        if self.sl_cursor and hasattr(self.sl_cursor, 'close'):
            self.sl_cursor.close()

class DualWriteConnection:
    def __init__(self, pg_conn, sl_conn):
        self.pg_conn = pg_conn
        self.sl_conn = sl_conn

    def cursor(self, **kwargs):
        pg_cur = self.pg_conn.cursor() if self.pg_conn else None
        sl_cur = self.sl_conn.cursor() if self.sl_conn else None
        return DualWriteCursor(pg_cur, sl_cur)

    def commit(self):
        if self.pg_conn: self.pg_conn.commit()
        if self.sl_conn: self.sl_conn.commit()

    def rollback(self):
        if self.pg_conn: self.pg_conn.rollback()
        if self.sl_conn: self.sl_conn.rollback()

    def close(self):
        if self.pg_conn: self.pg_conn.close()
        if self.sl_conn: self.sl_conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

from services.request_context import get_current_user_id

def get_conn(user_id: str | None = None):
    """
    Return a connection. If Postgres is active, returns a DualWriteConnection.
    If user_id is provided or found in context, sets it for RLS in Postgres.
    """
    sl_conn = sqlite3.connect(str(SQLITE_PATH))
    sl_conn.row_factory = sqlite3.Row

    # Auto-resolve user_id from context if not passed
    if not user_id:
        user_id = get_current_user_id()

    if DB_BACKEND == "postgres":
        try:
            import psycopg2
            pg_conn = psycopg2.connect(POSTGRES_URL)
            if user_id:
                with pg_conn.cursor() as cur:
                    # Set the session variable for RLS
                    cur.execute(f"SET LOCAL backpocket.user_id = %s", (user_id,))
            return DualWriteConnection(pg_conn, sl_conn)
        except Exception as e:
            logger.error(f"Failed to connect to Postgres, falling back to SQLite: {e}")
            return sl_conn
    
    return sl_conn

def run_migration(source_sqlite: str | None = None, target_url: str | None = None) -> dict:
    import subprocess
    import sys
    src = source_sqlite or str(SQLITE_PATH)
    tgt = target_url or POSTGRES_URL
    if not tgt:
        return {"success": False, "error": "POSTGRES_DB_URL not set"}
    result = subprocess.run(
        [sys.executable, "scripts/sqlite_to_pg_migration.py", "--source", src, "--target", tgt, "--verify"],
        capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent)
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-1000:],
    }

def status() -> dict:
    return {
        "backend": DB_BACKEND,
        "postgres_url_set": bool(POSTGRES_URL),
        "sqlite_path": str(SQLITE_PATH),
        "postgres_available": _postgres_available(),
    }
