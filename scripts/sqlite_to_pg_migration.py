#!/usr/bin/env python3
"""
BackPocket OS — SQLite to PostgreSQL Migration Script
Reads all tables from backpocket.db and migrates to Postgres with automatic schema generation.
Run: python scripts/sqlite_to_pg_migration.py --source /var/lib/backpocket/backpocket.db --target postgresql://user:pass@localhost:5432/backpocket
"""

import argparse
import sys
from pathlib import Path

import sqlite3
from sqlalchemy import (
    create_engine,
    text,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSON, JSONB
from sqlalchemy.orm import sessionmaker


# ═══════════════════════════════════════════════════════════════════════════
# Type Mapping: SQLite → Postgres
# ═══════════════════════════════════════════════════════════════════════

SQLITE_TO_PG_TYPE = {
    "INTEGER": Integer,
    "INT": Integer,
    "BIGINT": Integer,
    "REAL": Float,
    "TEXT": Text,
    "VARCHAR": String(255),
    "BLOB": Text,
    "BOOLEAN": Boolean,
    "TIMESTAMP": DateTime,
}

# ═══════════════════════════════════════════════════════════════════════════
# Migration Logic
# ═══════════════════════════════════════════════════════════════════════


class SQLiteToPostgres:
    def __init__(self, source_path: str, target_url: str):
        self.source_path = source_path
        self.target_url = target_url
        self.engine = create_engine(target_url)
        self.metadata = MetaData()

    def get_sqlite_schema(self) -> dict:
        """Read SQLite schema."""
        conn = sqlite3.connect(self.source_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        tables = {}
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        for row in cursor.fetchall():
            table_name = row[0]
            if table_name.startswith("sqlite_"):
                continue

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = []
            for col in cursor.fetchall():
                columns.append(
                    {
                        "name": col[1],
                        "type": col[2],
                        "notnull": col[3],
                        "default": col[4],
                        "pk": col[5],
                    }
                )

            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            fks = []
            for fk in cursor.fetchall():
                fks.append(
                    {
                        "table": fk[2],
                        "from": fk[3],
                        "to": fk[4],
                    }
                )

            tables[table_name] = {"columns": columns, "foreign_keys": fks}

        conn.close()
        return tables

    def create_pg_schema(self, tables: dict):
        """Create Postgres tables."""
        for table_name, schema in tables.items():
            print(f"[MIGRATE] Creating table: {table_name}")

            cols = []
            for col in schema["columns"]:
                pg_type = self._map_type(col["type"])
                c = Column(col["name"], pg_type, nullable=not col["notnull"])
                if col["default"]:
                    c = c.default(col["default"])
                if col["pk"]:
                    c.primary_key = True
                cols.append(c)

            # Handle JSON columns (detect by _json suffix)
            for col in schema["columns"]:
                if "_json" in col["name"]:
                    cols.append(Column(col["name"], JSONB))

            t = Table(table_name, self.metadata, *cols)
            t.create(self.engine, checkfirst=True)

        # Enable pgvector extension
        with self.engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

    def _map_type(self, sqlite_type: str) -> type:
        """Map SQLite type to Postgres type."""
        upper_type = sqlite_type.upper()
        for prefix, pg_type in SQLITE_TO_PG_TYPE.items():
            if upper_type.startswith(prefix):
                return pg_type
        return String(512)

    def migrate_data(self, tables: dict):
        """Migrate all data."""
        source_conn = sqlite3.connect(self.source_path)
        source_conn.row_factory = sqlite3.Row
        Session = sessionmaker(bind=self.engine)
        pg_session = Session()

        for table_name in tables.keys():
            print(f"[DATA] Migrating: {table_name}")
            cursor = source_conn.cursor()
            cursor.execute(f"SELECT * FROM {table_name}")

            rows = cursor.fetchall()
            if not rows:
                continue

            col_names = [desc[0] for desc in cursor.description]

            for row in rows:
                row_dict = dict(zip(col_names, row))
                self._sanitize_dict(row_dict)

                try:
                    pg_session.execute(
                        text(f"INSERT INTO {table_name} (:cols) VALUES (:vals)"),
                        {"cols": row_dict, "vals": row_dict},
                    )
                except Exception as e:
                    print(f"[WARN] Skipping row in {table_name}: {e}")

            pg_session.commit()

        source_conn.close()
        pg_session.close()

    def _sanitize_dict(self, d: dict):
        """Sanitize dict for Postgres."""
        for k, v in d.items():
            if v is None:
                continue
            if isinstance(v, str):
                if v == "None":
                    d[k] = None
                elif v.startswith("[") or v.startswith("{"):
                    try:
                        d[k] = __import__("json").loads(v)
                    except Exception:
                        pass

    def add_pgvector_columns(self):
        """Add pgvector embedding columns for RAG."""
        with self.engine.connect() as conn:
            # Knowledge notes vector column
            conn.execute(
                text("""
                ALTER TABLE knowledge_notes 
                ADD COLUMN IF NOT EXISTS embedding vector(1536)
            """)
            )

            # Email embeddings
            conn.execute(
                text("""
                ALTER TABLE pending_approvals 
                ADD COLUMN IF NOT EXISTS embedding vector(1536)
            """)
            )

            conn.commit()

    def add_rls_policies(self):
        """Add Row-Level Security policies."""
        with self.engine.connect() as conn:
            tables = [
                "leads",
                "quotes",
                "payments",
                "pending_approvals",
                "knowledge_notes",
            ]
            for table in tables:
                conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))

                # Policy for INSERT
                conn.execute(
                    text(f"""
                    CREATE POLICY IF NOT EXISTS "{table}_insert_policy" ON {table}
                    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL)
                """)
                )

                # Policy for SELECT
                conn.execute(
                    text(f"""
                    CREATE POLICY "{table}_select_policy" ON {table}
                    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL)
                """)
                )

            conn.commit()

    def verify_counts(self):
        """Verify row counts match."""
        source_conn = sqlite3.connect(self.source_path)
        pg_conn = self.engine.connect()

        cursor = source_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        print("\n[VERIFY] Row counts:")
        for row in cursor.fetchall():
            table = row[0]
            if table.startswith("sqlite_"):
                continue

            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            sqlite_count = cursor.fetchone()[0]

            result = pg_conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
            pg_count = result.fetchone()[0]

            status = "✓" if sqlite_count == pg_count else "✗"
            print(f"  {status} {table}: SQLite={sqlite_count}, PG={pg_count}")

        source_conn.close()
        pg_conn.close()


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite to Postgres")
    parser.add_argument("--source", required=True, help="Path to SQLite DB")
    parser.add_argument("--target", required=True, help="Postgres connection URL")
    parser.add_argument(
        "--verify", action="store_true", help="Verify counts after migration"
    )

    args = parser.parse_args()

    print("BackPocket OS — SQLite to PostgreSQL Migration")
    print("=" * 50)

    migrator = SQLiteToPostgres(args.source, args.target)

    # Step 1: Read schema
    print("\n[1/5] Reading SQLite schema...")
    tables = migrator.get_sqlite_schema()
    print(f"  Found {len(tables)} tables")

    # Step 2: Create PG schema
    print("\n[2/5] Creating PostgreSQL schema...")
    migrator.create_pg_schema(tables)

    # Step 3: Migrate data
    print("\n[3/5] Migrating data...")
    migrator.migrate_data(tables)

    # Step 4: Add pgvector
    print("\n[4/5] Adding pgvector columns...")
    migrator.add_pgvector_columns()

    # Step 5: Add RLS
    print("\n[5/5] Adding RLS policies...")
    migrator.add_rls_policies()

    # Verify
    if args.verify:
        print("\n[VERIFY] Verifying counts...")
        migrator.verify_counts()

    print("\n" + "=" * 50)
    print("Migration complete!")


if __name__ == "__main__":
    main()
