"""
DB Router — transparently switches between SQLite (default) and Postgres.

Usage in services:
    from services.db_router import get_conn, DB_BACKEND

If POSTGRES_DB_URL is set and psycopg2 is importable → Postgres.
Otherwise → SQLite (backpocket.db). No code changes needed in callers.
"""
import os
import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

SQLITE_PATH = Path(__file__).resolve().parent.parent / "backpocket.db"
POSTGRES_URL = os.environ.get("POSTGRES_DB_URL", "")


def _postgres_available() -> bool:
    if not POSTGRES_URL:
        return False
    try:
        import psycopg2  # noqa: F401
        return True
    except ImportError:
        return False


DB_BACKEND: str = "postgres" if _postgres_available() else "sqlite"


def get_conn():
    """
    Return a DB connection. SQLite returns sqlite3.Connection.
    Postgres returns a psycopg2 connection.
    Both support .cursor(), .execute(), .commit(), .close().
    """
    if DB_BACKEND == "postgres":
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(POSTGRES_URL)
        return conn
    else:
        conn = sqlite3.connect(str(SQLITE_PATH))
        conn.row_factory = sqlite3.Row
        return conn


def run_migration(source_sqlite: str | None = None, target_url: str | None = None) -> dict:
    """
    Run SQLite → Postgres migration.
    Returns {success, tables_migrated, rows_migrated, errors}.
    """
    import subprocess, sys
    src = source_sqlite or str(SQLITE_PATH)
    tgt = target_url or POSTGRES_URL
    if not tgt:
        return {"success": False, "error": "POSTGRES_DB_URL not set"}
    result = subprocess.run(
        [sys.executable, "scripts/sqlite_to_pg_migration.py", "--source", src, "--target", tgt],
        capture_output=True, text=True, cwd=str(Path(__file__).resolve().parent.parent)
    )
    return {
        "success": result.returncode == 0,
        "stdout": result.stdout[-2000:],
        "stderr": result.stderr[-1000:],
    }


def status() -> dict:
    """Return current DB backend status."""
    return {
        "backend": DB_BACKEND,
        "postgres_url_set": bool(POSTGRES_URL),
        "sqlite_path": str(SQLITE_PATH),
        "postgres_available": DB_BACKEND == "postgres",
    }
