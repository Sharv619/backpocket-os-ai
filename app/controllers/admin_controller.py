"""Admin / Kanban route — read-only team activity board powered by the knowledge bank + construction tables."""
import pathlib
import sqlite3
from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(prefix="/admin", tags=["admin"])

DB_PATH = pathlib.Path(__file__).resolve().parent.parent / "backpocket.db"
KANBAN_HTML = pathlib.Path(__file__).resolve().parent.parent / "static" / "kanban.html"


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


@router.get("/kanban")
async def kanban_page():
    return FileResponse(KANBAN_HTML, headers={"Cache-Control": "no-cache"})


@router.get("/api/kanban")
async def kanban_data():
    """Team activity board: everything auto-populates from the knowledge bank + git-signed merges."""
    con = _conn()
    try:
        has_knowledge = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='knowledge_notes'"
        ).fetchone() is not None

        columns = {"in_progress": [], "merged_this_week": [], "audited": []}
        leaderboard = []
        category_counts = []
        recent = []

        if has_knowledge:
            # Merged this week — auto-merge rows from the last 7 days
            columns["merged_this_week"] = [dict(r) for r in con.execute("""
                SELECT id, category, title, author_name, author_email, branch, commit_sha, created_at
                FROM knowledge_notes
                WHERE source = 'auto_merge' AND datetime(created_at) >= datetime('now', '-7 days')
                ORDER BY created_at DESC LIMIT 30
            """).fetchall()]

            # Audited — anything older than 7 days is considered settled / audited
            columns["audited"] = [dict(r) for r in con.execute("""
                SELECT id, category, title, author_email, branch, commit_sha, created_at
                FROM knowledge_notes
                WHERE source = 'auto_merge' AND datetime(created_at) < datetime('now', '-7 days')
                ORDER BY created_at DESC LIMIT 20
            """).fetchall()]

            # In progress — manual notes (work-in-flight findings, not yet merged)
            columns["in_progress"] = [dict(r) for r in con.execute("""
                SELECT id, category, title, author_name, author_email, branch, created_at
                FROM knowledge_notes
                WHERE source = 'manual'
                ORDER BY created_at DESC LIMIT 30
            """).fetchall()]

            # Leaderboard — notes per author this week
            leaderboard = [dict(r) for r in con.execute("""
                SELECT COALESCE(author_name, author_email, 'unknown') AS author,
                       author_email,
                       COUNT(*) AS notes_this_week
                FROM knowledge_notes
                WHERE datetime(created_at) >= datetime('now', '-7 days')
                GROUP BY author_email
                ORDER BY notes_this_week DESC LIMIT 10
            """).fetchall()]

            category_counts = [dict(r) for r in con.execute("""
                SELECT category, COUNT(*) AS n
                FROM knowledge_notes
                GROUP BY category ORDER BY n DESC
            """).fetchall()]

            recent = [dict(r) for r in con.execute("""
                SELECT id, category, title, author_email, source, created_at
                FROM knowledge_notes
                ORDER BY created_at DESC LIMIT 15
            """).fetchall()]

        # Business pulse — drawn from existing construction tables
        pipeline = con.execute("""
            SELECT COUNT(*) AS total_quotes,
                   SUM(CASE WHEN status='draft' THEN 1 ELSE 0 END) AS draft,
                   SUM(CASE WHEN status='sent' THEN 1 ELSE 0 END) AS sent,
                   SUM(CASE WHEN status='accepted' THEN 1 ELSE 0 END) AS accepted,
                   COALESCE(SUM(CASE WHEN status IN ('accepted','invoiced') THEN total_amount ELSE 0 END), 0) AS revenue_pipeline
            FROM quotes
        """).fetchone()
        open_leads = con.execute("SELECT COUNT(*) AS n FROM leads WHERE status = 'new'").fetchone()["n"]

        return {
            "columns": columns,
            "leaderboard": leaderboard,
            "categories": category_counts,
            "recent": recent,
            "pulse": {
                "open_leads": open_leads,
                **(dict(pipeline) if pipeline else {}),
            },
            "knowledge_bank_ready": has_knowledge,
        }
    finally:
        con.close()
