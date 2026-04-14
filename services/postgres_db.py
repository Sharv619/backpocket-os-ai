"""
BackPocket OS — PostgreSQL Database Service
Replaces services/database.py for Postgres with RLS support.
"""

import os
from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import (
    create_engine,
    event,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

# ═══════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════

DATABASE_URL = os.getenv(
    "DATABASE_URL", "postgresql://backpocket:backpocket@localhost:5432/backpocket"
)

# ═══════════════════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════════════════


class PostgresDB:
    """PostgreSQL database connection with RLS."""

    _instance: Optional["PostgresDB"] = None
    _engine: Optional[Engine] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def engine(self) -> Engine:
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine

    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with RLS support."""
        engine = create_engine(
            DATABASE_URL,
            poolclass=NullPool,
            echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        )

        # Enable RLS at transaction level
        @event.listens_for(engine, "begin")
        def do_begin(conn):
            conn.execute(text("SET search_path TO public, extensions"))
            # RLS enabled per-transaction
            conn.execute(text("SET row_security = ON"))

        return engine

    @property
    def session_factory(self) -> sessionmaker:
        return sessionmaker(bind=self.engine)

    @contextmanager
    def session(self) -> Generator[Session, None, None]:
        """Context-managed session."""
        with self.session_factory() as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    @contextmanager
    def transaction(self) -> Generator[Session, None, None]:
        """Explicit transaction."""
        with self.session() as s:
            with s.begin():
                yield s

    def execute(self, query: str, params: dict = None) -> Any:
        """Execute raw query."""
        with self.session() as s:
            return s.execute(text(query), params or {})

    def execute_many(self, query: str, params_list: list) -> None:
        """Execute many."""
        with self.session() as s:
            s.execute(text(query), params_list)


# ═══════════════════════════════════════════════════════════════════════
# Base Model
# ═══════════════════════════════════════════════════════════════════════

Base = declarative_base()


class Lead(Base):
    """Lead model."""

    __tablename__ = "leads"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    client_name = Column(String(255), nullable=False)
    email = Column(String(255))
    phone = Column(String(50))
    job_type = Column(String(100))
    location = Column(String(255))
    urgency = Column(String(50))
    estimated_budget = Column(Integer)
    status = Column(String(50), default="new")
    created_at = Column(Time, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"))


# ═══════════════════════════════════════════════════════════════════════════════
# Initialization
# ═══════════════════════════════════════════════════════════════════════════════

_db: Optional[PostgresDB] = None


def get_db() -> PostgresDB:
    """Get DB singleton."""
    global _db
    if _db is None:
        _db = PostgresDB()
    return _db


def init_db() -> None:
    """Initialize database tables."""
    Base.metadata.create_all(get_db().engine)


# ═══════════════════════════════════════════════════════════════════════
# Convenience Functions
# ═══════════════════════════════════════════════════════════════════════


def get_all_leads(user_id: str) -> list[dict]:
    """Get all leads for a user."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("SELECT * FROM leads WHERE user_id = :uid ORDER BY created_at DESC"),
            {"uid": user_id},
        )
        return [dict(r) for r in result.fetchall()]


def get_lead(lead_id: int, user_id: str) -> Optional[dict]:
    """Get single lead."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("SELECT * FROM leads WHERE id = :id AND user_id = :uid"),
            {"id": lead_id, "uid": user_id},
        )
        return dict(result.fetchone()) if result.fetchone() else None


def create_lead(user_id: str, data: dict) -> dict:
    """Create new lead."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("""
                INSERT INTO leads (user_id, client_name, email, phone, job_type, location, urgency, estimated_budget)
                VALUES (:user_id, :client_name, :email, :phone, :job_type, :location, :urgency, :estimated_budget)
                RETURNING *
            """),
            {
                "user_id": user_id,
                "client_name": data["client_name"],
                "email": data.get("email"),
                "phone": data.get("phone"),
                "job_type": data.get("job_type"),
                "location": data.get("location"),
                "urgency": data.get("urgency"),
                "estimated_budget": data.get("estimated_budget"),
            },
        )
        return dict(result.fetchone())


def update_lead_status(lead_id: int, user_id: str, status: str) -> dict:
    """Update lead status."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("""
                UPDATE leads SET status = :status, updated_at = NOW()
                WHERE id = :id AND user_id = :uid
                RETURNING *
            """),
            {"id": lead_id, "uid": user_id, "status": status},
        )
        return dict(result.fetchone())


def get_all_quotes(user_id: str) -> list[dict]:
    """Get all quotes for a user."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("SELECT * FROM quotes WHERE user_id = :uid ORDER BY created_at DESC"),
            {"uid": user_id},
        )
        return [dict(r) for r in result.fetchall()]


def create_quote(user_id: str, data: dict) -> dict:
    """Create new quote."""
    db = get_db()

    # Calculate totals
    materials = data.get("materials_cost", 0)
    labor = data.get("labor_hours", 0) * 85
    markup = data.get("markup_percent", 20)
    total = (materials + labor) * (1 + markup / 100)

    with db.session() as s:
        result = s.execute(
            text("""
                INSERT INTO quotes (user_id, lead_id, materials_cost, labor_hours, markup_percent, total)
                VALUES (:user_id, :lead_id, :materials_cost, :labor_hours, :markup_percent, :total)
                RETURNING *
            """),
            {
                "user_id": user_id,
                "lead_id": data["lead_id"],
                "materials_cost": materials,
                "labor_hours": labor,
                "markup_percent": markup,
                "total": total,
            },
        )
        return dict(result.fetchone())


def get_all_payments(user_id: str) -> list[dict]:
    """Get all payments for a user."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("SELECT * FROM payments WHERE user_id = :uid ORDER BY paid_at DESC"),
            {"uid": user_id},
        )
        return [dict(r) for r in result.fetchall()]


def record_payment(user_id: str, data: dict) -> dict:
    """Record payment."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("""
                INSERT INTO payments (user_id, quote_id, amount)
                VALUES (:user_id, :quote_id, :amount)
                RETURNING *
            """),
            {
                "user_id": user_id,
                "quote_id": data["quote_id"],
                "amount": data["amount"],
            },
        )
        return dict(result.fetchone())


# ═══════════════════════════════════════════════════════════════════════════════
# RLS Helper
# ═══════════════════════════════════════════════════════════════════════


def set_user_id(user_id: str) -> None:
    """Set the user_id for RLS (called from auth middleware)."""
    db = get_db()
    with db.engine.connect() as conn:
        conn.execute(text(f"SET LOCAL backpocket.user_id = '{user_id}'"))
        conn.commit()


# Import needed for type hints
from datetime import Time, DateTime
