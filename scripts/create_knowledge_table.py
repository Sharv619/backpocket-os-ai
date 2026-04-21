"""Create the shared knowledge_notes table. Idempotent."""
import sqlite3
import pathlib

DB = pathlib.Path(__file__).resolve().parent.parent / "backpocket.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_notes (
  id            INTEGER PRIMARY KEY AUTOINCREMENT,
  category      TEXT NOT NULL,
  title         TEXT NOT NULL,
  body          TEXT NOT NULL,
  tags          TEXT,
  author_name   TEXT,
  author_email  TEXT,
  branch        TEXT,
  commit_sha    TEXT,
  source        TEXT DEFAULT 'manual',
  created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_notes(category);
CREATE INDEX IF NOT EXISTS idx_knowledge_author   ON knowledge_notes(author_email);
CREATE INDEX IF NOT EXISTS idx_knowledge_branch   ON knowledge_notes(branch);
"""

def main():
    con = sqlite3.connect(DB)
    con.executescript(SCHEMA)
    con.commit()
    con.close()
    print(f"[ok] knowledge_notes ready in {DB}")

if __name__ == "__main__":
    main()
