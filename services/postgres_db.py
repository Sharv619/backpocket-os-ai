"""
BackPocket OS — PostgreSQL Database Service
Replaces services/database.py for Postgres with RLS support.
"""

import os
import uuid
from contextlib import contextmanager
from typing import Any, Generator, Optional

from sqlalchemy import (
    create_engine,
    event,
    text,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy import (
    Column,
    String,
    Boolean,
    DateTime,
    Float,
    Integer,
    Text,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.pool import NullPool

# ═══════════════════════════════════════════════════════════════════════
# Config
# ═══════════════════════════════════════════════════════════════════════

DATABASE_URL = os.getenv(
    "POSTGRES_DB_URL",
    "postgresql+psycopg2://backpocket_user:backpocket_password@localhost:5432/backpocket_db",
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

Base = declarative_base()  # Already defined at line 103, keep this one


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))


class Lead(Base):
    __tablename__ = "leads"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    client_name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String)
    job_type = Column(String)
    location = Column(String)
    pain_points = Column(Text)
    scope_items = Column(Text)
    urgency = Column(String)
    estimated_budget = Column(Float)
    timeline = Column(String)
    status = Column(String, default="new")
    extracted_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))


class Quote(Base):
    __tablename__ = "quotes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True)
    client_name = Column(String)
    job_type = Column(String)
    description = Column(Text)
    scope_items = Column(Text)
    materials_cost = Column(Float)
    labor_cost = Column(Float)
    markup_percent = Column(Float)
    total_amount = Column(Float)
    status = Column(String, default="draft")
    sent_date = Column(DateTime)
    accepted_date = Column(DateTime)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))


class Payment(Base):
    __tablename__ = "payments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=True)
    client_name = Column(String)
    amount = Column(Float)
    currency = Column(String, default="AUD")
    status = Column(String, default="pending")
    due_date = Column(DateTime)
    received_date = Column(DateTime)
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))


class PendingApproval(Base):
    __tablename__ = "pending_approvals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    ref_id = Column(String, index=True)
    sender = Column(String)
    subject = Column(String)
    preview = Column(Text)
    tier = Column(Integer, default=3)
    status = Column(String, default="pending")
    embedding = Column(ARRAY(Float))  # Use ARRAY(Float) for pgvector compatibility
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))


class KnowledgeNote(Base):
    __tablename__ = "knowledge_notes"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    category = Column(String)
    title = Column(String)
    body = Column(Text)
    tags = Column(ARRAY(String))
    author_email = Column(String)
    embedding = Column(ARRAY(Float))  # Use ARRAY(Float) for pgvector compatibility
    created_at = Column(DateTime, server_default=text("NOW()"))
    updated_at = Column(DateTime, server_default=text("NOW()"), onupdate=text("NOW()"))


_db: Optional["PostgresDB"] = None

# ═══════════════════════════════════════════════════════════════════════════════
# Initialization
# ═══════════════════════════════════════════════════════════════════════════════


def get_db() -> PostgresDB:
    """Get DB singleton."""
    global _db
    if _db is None:
        _db = PostgresDB()
    return _db


def init_db() -> None:
    """Initialize database tables."""
    engine = get_db().engine
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(engine)


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
        return [dict(r._mapping) for r in result.fetchall() if r]


def get_lead(lead_id: int, user_id: str) -> Optional[dict]:
    """Get single lead."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("SELECT * FROM leads WHERE id = :id AND user_id = :uid"),
            {"id": lead_id, "uid": user_id},
        )
        lead_data = result.fetchone()
        return dict(lead_data._mapping) if lead_data else None


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
        row = result.fetchone()
        return dict(row._mapping) if row else None


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
        return [dict(r._mapping) for r in result.fetchall() if r]


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
        return dict(result.fetchone()._mapping)


def get_all_payments(user_id: str) -> list[dict]:
    """Get all payments for a user."""
    db = get_db()
    with db.session() as s:
        result = s.execute(
            text("SELECT * FROM payments WHERE user_id = :uid ORDER BY paid_at DESC"),
            {"uid": user_id},
        )
        return [dict(r._mapping) for r in result.fetchall()]


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
        row = result.fetchone()
        return dict(row._mapping) if row else {}


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
import uuid  # Added uuid import
