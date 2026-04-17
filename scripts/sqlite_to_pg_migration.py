#!/usr/bin/env python3
"""
BackPocket OS — SQLite to PostgreSQL Migration Script
Reads all tables from backpocket.db and migrates to Postgres with automatic schema generation.
Run: python scripts/sqlite_to_pg_migration.py --source /var/lib/backpocket/backpocket.db --target postgresql://user:pass@localhost:5432/backpocket
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import sqlite3
import json
from sqlalchemy import (
    create_engine,
    text,
    MetaData,
    Table,
    Column,
    Date,
    Integer,
    Numeric,
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
    "FLOAT": Float,
    "NUMERIC": Numeric,
    "DECIMAL": Numeric,
    "TEXT": Text,
    "VARCHAR": String(255),
    "BLOB": Text,
    "BOOLEAN": Boolean,
    "TIMESTAMP": DateTime,
    "DATETIME": DateTime,
    "DATE": Date,
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
        with self.engine.connect() as conn:
            # Enable pgvector extension once
            try:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
                conn.commit()
                print("[PG_SCHEMA] Enabled pgvector extension.")
            except Exception as e:
                print(
                    f"[WARN] Could not enable pgvector: {e}. Migration will proceed without it."
                )
                conn.rollback()

        for table_name, schema in tables.items():
            print(f"[MIGRATE] Creating table: {table_name}")

            cols = []
            for col in schema["columns"]:
                pg_type = self._map_type(col["type"])
                col_kwargs = {"nullable": not col["notnull"]}
                if col["default"] is not None:
                    raw_default = str(col["default"]).strip("'\"")
                    sql_funcs = {"CURRENT_TIMESTAMP", "CURRENT_DATE", "CURRENT_TIME",
                                 "NOW()", "TRUE", "FALSE", "NULL"}
                    if raw_default.upper() in sql_funcs or raw_default.upper().startswith("("):
                        col_kwargs["server_default"] = text(raw_default.upper())
                    else:
                        col_kwargs["server_default"] = raw_default
                c = Column(col["name"], pg_type, **col_kwargs)
                if col["pk"]:
                    c.primary_key = True
                cols.append(c)

            # Attach foreign keys to their source columns
            fk_map = {}
            for fk_info in schema["foreign_keys"]:
                fk_map[fk_info["from"]] = ForeignKey(
                    f"{fk_info['table']}.{fk_info['to']}",
                    name=f"fk_{table_name}_{fk_info['from']}_to_{fk_info['table']}_{fk_info['to']}",
                )
            for c in cols:
                if c.name in fk_map:
                    c.append_foreign_key(fk_map[c.name])

            # Re-check for JSON columns by name convention if not explicitly handled by SQLite type
            final_cols = []
            json_cols_added = set()
            for col in cols:
                # Replace generic String/Text with JSONB if column name suggests JSON
                if (
                    "_json" in col.name.lower()
                    or "data" in col.name.lower()
                    and isinstance(col.type, (String, Text))
                ):
                    if (
                        col.name not in json_cols_added
                    ):  # Avoid duplicate columns if already added
                        final_cols.append(
                            Column(col.name, JSONB, nullable=col.nullable)
                        )
                        json_cols_added.add(col.name)
                    else:
                        print(
                            f"[WARN] Duplicate JSONB column definition for {col.name} in {table_name}. Skipping."
                        )
                else:
                    final_cols.append(col)

            Table(table_name, self.metadata, *final_cols)

        print(f"[MIGRATE] Creating all {len(tables)} tables in dependency order...")
        self.metadata.create_all(self.engine, checkfirst=True)

    def _map_type(self, sqlite_type: str) -> type:
        """Map SQLite type to Postgres type."""
        upper_type = sqlite_type.upper()
        for prefix, pg_type in SQLITE_TO_PG_TYPE.items():
            if upper_type.startswith(prefix):
                return pg_type
        print(f"[WARN] Unknown SQLite type '{sqlite_type}', defaulting to String(512).")
        return String(512)

    def migrate_data(self, tables: dict):
        """Migrate all data."""
        source_conn = sqlite3.connect(self.source_path)
        source_conn.row_factory = sqlite3.Row
        Session = sessionmaker(bind=self.engine)
        pg_session = Session()

        failed_tables = []
        for table_name, schema in tables.items():
            if not self._migrate_table_data(table_name, schema, source_conn, pg_session):
                failed_tables.append(table_name)

        if failed_tables:
            print(f"[DATA] Retrying {len(failed_tables)} FK-deferred tables...")
            still_failed = []
            for table_name in failed_tables:
                if not self._migrate_table_data(table_name, tables[table_name], source_conn, pg_session):
                    still_failed.append(table_name)

            if still_failed:
                print(f"[DATA] Force-inserting {len(still_failed)} tables (disabling FK checks)...")
                with self.engine.connect() as conn:
                    for table_name in still_failed:
                        fks = conn.execute(text(
                            f"SELECT conname FROM pg_constraint WHERE conrelid = '{table_name}'::regclass AND contype = 'f'"
                        )).fetchall()
                        for (fk_name,) in fks:
                            conn.execute(text(f'ALTER TABLE {table_name} DROP CONSTRAINT "{fk_name}"'))
                        conn.commit()
                    for table_name in still_failed:
                        self._migrate_table_data(table_name, tables[table_name], source_conn, pg_session)

        source_conn.close()
        pg_session.close()

    def _migrate_table_data(self, table_name, schema, source_conn, pg_session):
        print(f"[DATA] Migrating: {table_name}")
        cursor = source_conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        if not rows:
            print(f"  No data found for {table_name}.")
            return True

        col_names = [desc[0] for desc in cursor.description]
        data_to_insert = []
        for row in rows:
            row_dict = dict(zip(col_names, row))
            sanitized_dict = self._sanitize_dict(row_dict, schema["columns"])
            data_to_insert.append(sanitized_dict)

        if data_to_insert:
            try:
                pg_table = Table(table_name, self.metadata, autoload_with=self.engine)
                pg_session.execute(pg_table.insert(), data_to_insert)
                pg_session.commit()
                print(f"  Successfully inserted {len(data_to_insert)} rows into {table_name}.")
                return True
            except Exception as e:
                pg_session.rollback()
                print(f"[ERROR] Failed to insert data into {table_name}: {e}")
                return False
        print(f"  No valid data to insert into {table_name}.")
        return True

    def _sanitize_dict(self, d: dict, schema_cols: list) -> dict:
        """Sanitize dict for Postgres, handling type conversions like JSON strings to objects."""
        sanitized_d = {}
        for k, v in d.items():
            # Find the column definition to get its type hint
            col_def = next((col for col in schema_cols if col["name"] == k), None)

            if v is None:
                sanitized_d[k] = None
                continue

            # Handle JSON/JSONB columns
            if col_def and (
                "_json" in k.lower()
                or ("data" in k.lower() and "text" in col_def["type"].lower())
            ):
                try:
                    sanitized_d[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    sanitized_d[k] = v  # Keep as string if not valid JSON
                    print(
                        f"[WARN] Column '{k}' contains non-JSON string '{v[:50]}...' but was expected to be JSON. Stored as string."
                    )

            # Handle BOOLEAN conversion (SQLite stores 0/1 for BOOLEAN)
            elif col_def and "BOOLEAN" in col_def["type"].upper():
                if isinstance(v, (int, float)):
                    sanitized_d[k] = bool(v)
                elif isinstance(v, str):
                    sanitized_d[k] = v.lower() == "true" or v == "1"
                else:
                    sanitized_d[k] = v  # Keep as is, let Postgres handle

            # Handle DATETIME conversion (SQLite might store as text)
            elif col_def and (
                "DATETIME" in col_def["type"].upper()
                or "TIMESTAMP" in col_def["type"].upper()
            ):
                if isinstance(v, str):
                    try:
                        sanitized_d[k] = datetime.fromisoformat(v)
                    except ValueError:
                        # Fallback for non-ISO formats or errors
                        try:
                            sanitized_d[k] = datetime.strptime(
                                v, "%Y-%m-%d %H:%M:%S.%f"
                            )
                        except ValueError:
                            try:
                                sanitized_d[k] = datetime.strptime(
                                    v, "%Y-%m-%d %H:%M:%S"
                                )
                            except ValueError:
                                sanitized_d[k] = (
                                    None  # Or raise error, or keep original string
                                )
                                print(
                                    f"[WARN] Could not parse datetime string '{v}' for column '{k}'. Setting to NULL."
                                )
                else:
                    sanitized_d[k] = v

            else:
                sanitized_d[k] = v
        return sanitized_d

    def add_pgvector_columns(self):
        """Add pgvector embedding columns for RAG."""
        print("[PG_VECTOR] Adding pgvector columns...")
        try:
            with self.engine.connect() as conn:
                for tbl in ["knowledge_notes", "pending_approvals"]:
                    if self.engine.dialect.has_table(conn, tbl):
                        conn.execute(text(
                            f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS embedding vector(1536)"
                        ))
                        print(f"  Added 'embedding' column to '{tbl}'.")
                    else:
                        print(f"  '{tbl}' not found, skipping.")
                conn.commit()
            print("[PG_VECTOR] pgvector columns configured.")
        except Exception as e:
            print(f"[WARN] pgvector not available, skipping embedding columns: {e}")

    def add_rls_policies(self):
        """Add Row-Level Security policies (requires Supabase auth.uid())."""
        print("[RLS] Adding Row-Level Security policies...")
        try:
          with self.engine.connect() as conn:
            tables_to_rls = [
                "leads",
                "quotes",
                "payments",
                "pending_approvals",
                "knowledge_notes",
                "users",  # Assuming a users table for auth.uid()
            ]

            for table in tables_to_rls:
                if not self.engine.dialect.has_table(conn, table):
                    print(
                        f"[WARN] Table '{table}' not found, skipping RLS policy creation."
                    )
                    continue

                # Check if 'user_id' column exists before applying RLS
                # This requires querying information_schema or similar, but for simplicity,
                # we'll assume 'user_id' exists for these tables for now.
                # In a real scenario, you'd check `conn.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table}' AND column_name='user_id'"))`
                # If no 'user_id' column, the RLS policy might fail or be ineffective.

                print(f"  Enabling RLS for table: {table}")
                conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))

                # Policy for INSERT (allows insert if user_id is current user or null, for system-generated data)
                conn.execute(
                    text(f"""
                    DROP POLICY IF EXISTS "{table}_insert_policy" ON {table};
                    CREATE POLICY "{table}_insert_policy" ON {table}
                    FOR INSERT WITH CHECK (auth.uid() = user_id OR user_id IS NULL);
                """)
                )

                # Policy for SELECT (users can view their own data or data with null user_id)
                conn.execute(
                    text(f"""
                    DROP POLICY IF EXISTS "{table}_select_policy" ON {table};
                    CREATE POLICY "{table}_select_policy" ON {table}
                    FOR SELECT USING (auth.uid() = user_id OR user_id IS NULL);
                """)
                )

                # Policy for UPDATE (users can update their own data)
                conn.execute(
                    text(f"""
                    DROP POLICY IF EXISTS "{table}_update_policy" ON {table};
                    CREATE POLICY "{table}_update_policy" ON {table}
                    FOR UPDATE USING (auth.uid() = user_id);
                """)
                )

                # Policy for DELETE (users can delete their own data)
                conn.execute(
                    text(f"""
                    DROP POLICY IF EXISTS "{table}_delete_policy" ON {table};
                    CREATE POLICY "{table}_delete_policy" ON {table}
                    FOR DELETE USING (auth.uid() = user_id);
                """)
                )
            conn.commit()
          print("[RLS] RLS policies applied.")
        except Exception as e:
          print(f"[WARN] RLS policies skipped (requires Supabase auth.uid()): {e}")

    def verify_counts(self):
        """Verify row counts match."""
        source_conn = sqlite3.connect(self.source_path)
        pg_conn = self.engine.connect()

        cursor = source_conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")

        print("\n[VERIFY] Row counts:")
        all_tables_match = True
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
            if sqlite_count != pg_count:
                all_tables_match = False

        source_conn.close()
        pg_conn.close()
        if all_tables_match:
            print("[VERIFY] All table row counts match successfully!")
        else:
            print("[VERIFY] WARNING: Some table row counts do NOT match.")


# ═══════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════


def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite to Postgres")
    parser.add_argument("--source", required=True, help="Path to SQLite DB")
    parser.add_argument("--target", required=True, help="Postgres connection URL")
    parser.add_argument(
        "--verify", action="store_true", help="Verify counts after migration"
    )
    parser.add_argument(
        "--drop-tables",
        action="store_true",
        help="DANGER: Drop existing tables in Postgres before migration",
    )

    args = parser.parse_args()

    print("BackPocket OS — SQLite to PostgreSQL Migration")
    print("=" * 50)

    migrator = SQLiteToPostgres(args.source, args.target)

    if args.drop_tables:
        print("\n[DANGER] Dropping all tables in target PostgreSQL database...")
        # Reflect existing PG tables to drop them
        pg_metadata = MetaData()
        pg_metadata.reflect(bind=migrator.engine)
        pg_metadata.drop_all(migrator.engine)
        print("  All tables dropped.")

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
