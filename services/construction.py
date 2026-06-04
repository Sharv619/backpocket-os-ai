"""Construction/Tradie business management."""

import logging
import re
import sqlite3
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)
DB_PATH = "backpocket.db"


def _connect(*, row_factory: bool = False) -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    if row_factory:
        conn.row_factory = sqlite3.Row
    return conn


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "client"


def _placeholder_email(client_name: str) -> str:
    return f"{_slugify(client_name)}@backpocket.local"


class ConstructionManager:
    """Manage leads, quotes, and jobs for construction businesses."""

    def _get_existing_by_action_id(self, table: str, client_action_id: Optional[str]) -> Dict:
        if not client_action_id:
            return {}
        conn = _connect(row_factory=True)
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT * FROM {table} WHERE client_action_id = ?",
            (client_action_id,),
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else {}

    def _sum_payments_for_quote(self, conn: sqlite3.Connection, quote_id: int) -> float:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE quote_id = ?",
            (quote_id,),
        )
        return float(cursor.fetchone()[0] or 0.0)

    # ===== LEADS =====

    def create_lead(
        self,
        client_name: str,
        email: str,
        job_type: str,
        location: str,
        urgency: str,
        budget: float = None,
        client_action_id: str | None = None,
    ) -> Dict:
        """Create a new lead from email extraction."""
        existing = self._get_existing_by_action_id("leads", client_action_id)
        if existing:
            return {
                "lead_id": existing["id"],
                "status": existing.get("status", "new"),
                "client_action_id": client_action_id,
                "deduplicated": True,
            }

        normalized_email = (email or "").strip() or _placeholder_email(client_name)
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO leads
            (client_name, email, job_type, location, urgency, estimated_budget, status, client_action_id)
            VALUES (?, ?, ?, ?, ?, ?, 'new', ?)
            """,
            (
                client_name,
                normalized_email,
                job_type,
                location,
                urgency,
                budget,
                client_action_id,
            ),
        )

        lead_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info("Created lead: %s (%s)", client_name, job_type)
        return {
            "lead_id": lead_id,
            "status": "created",
            "client_action_id": client_action_id,
            "email": normalized_email,
        }

    def get_leads(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get all leads, optionally filtered by status."""
        conn = _connect(row_factory=True)
        cursor = conn.cursor()

        if status:
            cursor.execute(
                """
                SELECT * FROM leads
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (status, limit),
            )
        else:
            cursor.execute(
                """
                SELECT * FROM leads
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )

        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leads

    def get_lead(self, lead_id: int) -> Dict:
        """Get single lead details."""
        conn = _connect(row_factory=True)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()
        conn.close()

        return dict(lead) if lead else {}

    def update_lead_status(self, lead_id: int, status: str) -> Dict:
        """Update lead status (new -> quoted -> accepted)."""
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, lead_id),
        )

        conn.commit()
        conn.close()

        return {"lead_id": lead_id, "status": status}

    # ===== QUOTES =====

    def create_quote(
        self,
        lead_id: int,
        client_name: str = None,
        job_type: str = None,
        materials_cost: float = 0,
        labor_cost: float = 0,
        markup_percent: float = 20,
        client_action_id: str | None = None,
    ) -> Dict:
        """Generate a quote for a lead. Inherits client_name/job_type from lead if not provided."""
        existing = self._get_existing_by_action_id("quotes", client_action_id)
        if existing:
            return {
                "quote_id": existing["id"],
                "total_amount": float(existing.get("total_amount") or 0),
                "status": existing.get("status", "draft"),
                "client_action_id": client_action_id,
                "deduplicated": True,
            }

        conn = _connect()
        cursor = conn.cursor()

        if lead_id:
            cursor.execute(
                "SELECT client_name, job_type FROM leads WHERE id = ?",
                (lead_id,),
            )
            row = cursor.fetchone()
            if row:
                client_name = client_name or row[0]
                job_type = job_type or row[1]

        client_name = client_name or "Unknown Client"
        job_type = job_type or "General"
        total = (materials_cost + labor_cost) * (1 + markup_percent / 100)

        cursor.execute(
            """
            INSERT INTO quotes
            (lead_id, client_action_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                lead_id,
                client_action_id,
                client_name,
                job_type,
                materials_cost,
                labor_cost,
                markup_percent,
                total,
            ),
        )

        quote_id = cursor.lastrowid
        cursor.execute(
            """
            UPDATE leads SET status = 'quoted', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (lead_id,),
        )

        conn.commit()
        conn.close()

        logger.info("Created quote: %s - $%.2f", client_name, total)
        return {
            "quote_id": quote_id,
            "total_amount": total,
            "status": "draft",
            "client_action_id": client_action_id,
        }

    def get_quotes(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get all quotes, optionally filtered by status."""
        conn = _connect(row_factory=True)
        cursor = conn.cursor()

        base_query = """
            SELECT q.*, l.email AS client_email, l.location AS location
            FROM quotes q
            LEFT JOIN leads l ON l.id = q.lead_id
        """
        if status:
            cursor.execute(
                f"""
                {base_query}
                WHERE q.status = ?
                ORDER BY q.created_at DESC
                LIMIT ?
                """,
                (status, limit),
            )
        else:
            cursor.execute(
                f"""
                {base_query}
                ORDER BY q.created_at DESC
                LIMIT ?
                """,
                (limit,),
            )

        quotes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return quotes

    def get_quote(self, quote_id: int) -> Dict:
        """Get single quote details."""
        conn = _connect(row_factory=True)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT q.*, l.email AS client_email, l.location AS location
            FROM quotes q
            LEFT JOIN leads l ON l.id = q.lead_id
            WHERE q.id = ?
            """,
            (quote_id,),
        )
        quote = cursor.fetchone()
        conn.close()

        return dict(quote) if quote else {}

    def get_pipeline_summary(self) -> Dict:
        """Get quote pipeline summary with legacy and normalized keys."""
        conn = _connect()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) AS total FROM quotes")
        total_quotes = int(cursor.fetchone()[0] or 0)

        cursor.execute("SELECT COUNT(*) AS pending FROM quotes WHERE status = 'sent'")
        pending_quotes = int(cursor.fetchone()[0] or 0)

        cursor.execute("SELECT COUNT(*) AS accepted FROM quotes WHERE status = 'accepted'")
        accepted_quotes = int(cursor.fetchone()[0] or 0)

        cursor.execute(
            "SELECT COALESCE(SUM(total_amount), 0) FROM quotes WHERE status IN ('accepted', 'invoiced')"
        )
        revenue_pipeline = float(cursor.fetchone()[0] or 0)

        cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'received'"
        )
        total_paid = float(cursor.fetchone()[0] or 0)
        conn.close()

        outstanding = max(0.0, revenue_pipeline - total_paid)
        return {
            "total_quotes": total_quotes,
            "pending_quotes": pending_quotes,
            "accepted_quotes": accepted_quotes,
            "revenue_pipeline": revenue_pipeline,
            "total_pipeline_value": revenue_pipeline,
            "pending_count": pending_quotes,
            "accepted_count": accepted_quotes,
            "total_revenue": total_paid,
            "outstanding": outstanding,
        }

    def update_quote_status(self, quote_id: int, status: str) -> Dict:
        """Update quote status (draft -> sent -> accepted -> invoiced)."""
        conn = _connect()
        cursor = conn.cursor()

        if status == "sent":
            cursor.execute(
                """
                UPDATE quotes SET status = ?, sent_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, quote_id),
            )
        elif status == "accepted":
            cursor.execute(
                """
                UPDATE quotes SET status = ?, accepted_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, quote_id),
            )
        else:
            cursor.execute(
                """
                UPDATE quotes SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, quote_id),
            )

        conn.commit()
        conn.close()

        return {"quote_id": quote_id, "status": status}

    def draft_quote_followup(self, quote_id: int, tone: str = "friendly") -> Dict:
        """Create a deterministic tradie follow-up message without external AI."""
        quote = self.get_quote(quote_id)
        if not quote:
            return {"error": "Quote not found"}

        client_name = (quote.get("client_name") or "").split(" ")[0] or "there"
        job_type = quote.get("job_type") or "job"

        templates = {
            "friendly": (
                f"Hi {client_name}, just checking in on the {job_type} quote I sent through. "
                "If you want to go ahead or tweak anything, reply here and I will sort it. Cheers."
            ),
            "professional": (
                f"Hi {client_name}, following up on your {job_type} quote. "
                "Let me know if you would like to proceed or if you need any adjustments."
            ),
            "urgent": (
                f"Hi {client_name}, quick follow-up on the {job_type} quote. "
                "My schedule is filling up, so let me know soon if you want me to lock this in."
            ),
        }
        return {
            "quote_id": quote_id,
            "message": templates.get(tone, templates["friendly"]),
            "client_name": quote.get("client_name", ""),
            "job_type": quote.get("job_type", ""),
            "client_email": quote.get("client_email", ""),
        }

    def prepare_invoice_payload(
        self,
        quote_id: int,
        client_email: str = "",
        notes: str = "",
    ) -> Dict:
        """Return a normalized invoice payload for a quote."""
        quote = self.get_quote(quote_id)
        if not quote:
            return {"error": f"Quote {quote_id} not found"}

        items = [
            {
                "description": f"Materials - {quote.get('job_type', 'Job')}",
                "qty": 1,
                "rate": float(quote.get("materials_cost") or 0),
                "gst": True,
            },
            {
                "description": f"Labour - {quote.get('job_type', 'Job')}",
                "qty": 1,
                "rate": float(quote.get("labor_cost") or 0),
                "gst": True,
            },
        ]
        return {
            "quote": quote,
            "client_data": {
                "name": quote.get("client_name", "Client"),
                "email": client_email or quote.get("client_email", ""),
            },
            "invoice_data": {
                "line_items": items,
                "notes": notes or quote.get("description") or f"Invoice for job: {quote.get('job_type', 'Job')}",
            },
        }

    # ===== PAYMENTS =====

    def record_payment(
        self,
        quote_id: int,
        amount: float,
        client_name: str = None,
        client_action_id: str | None = None,
    ) -> Dict:
        """Record a payment received."""
        existing = self._get_existing_by_action_id("payments", client_action_id)
        if existing:
            return {
                "payment_id": existing["id"],
                "status": existing.get("status", "received"),
                "quote_id": existing.get("quote_id", quote_id),
                "amount": float(existing.get("amount") or amount),
                "client_action_id": client_action_id,
                "deduplicated": True,
            }

        conn = _connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT client_name, total_amount FROM quotes WHERE id = ?",
            (quote_id,),
        )
        quote_row = cursor.fetchone()
        resolved_client_name = client_name or (quote_row[0] if quote_row else "")
        total_amount = float(quote_row[1] or 0) if quote_row else 0.0

        cursor.execute(
            """
            INSERT INTO payments
            (quote_id, client_action_id, client_name, amount, status, received_date)
            VALUES (?, ?, ?, ?, 'received', CURRENT_TIMESTAMP)
            """,
            (quote_id, client_action_id, resolved_client_name, amount),
        )

        payment_id = cursor.lastrowid
        paid_after_insert = self._sum_payments_for_quote(conn, quote_id)
        remaining = max(0.0, total_amount - paid_after_insert)
        conn.commit()
        conn.close()

        logger.info("Recorded payment: $%.2f", amount)
        return {
            "payment_id": payment_id,
            "status": "received",
            "quote_id": quote_id,
            "amount": amount,
            "client_name": resolved_client_name,
            "remaining": remaining,
            "client_action_id": client_action_id,
        }

    def get_payments(self, quote_id: int = None) -> List[Dict]:
        """Get all payments, optionally filtered by quote."""
        conn = _connect(row_factory=True)
        cursor = conn.cursor()

        if quote_id:
            cursor.execute(
                "SELECT * FROM payments WHERE quote_id = ? ORDER BY received_date DESC",
                (quote_id,),
            )
        else:
            cursor.execute(
                "SELECT * FROM payments ORDER BY received_date DESC, created_at DESC"
            )

        payments = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return payments


# Module singleton
_manager = None


def get_construction_manager() -> ConstructionManager:
    global _manager
    if _manager is None:
        _manager = ConstructionManager()
    return _manager
