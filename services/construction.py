"""Construction/Tradie business management"""

import sqlite3
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)
DB_PATH = "backpocket.db"

class ConstructionManager:
    """Manage leads, quotes, and jobs for construction businesses"""

    # ===== LEADS =====

    def create_lead(self, client_name: str, email: str, job_type: str,
                   location: str, urgency: str, budget: float = None) -> Dict:
        """Create a new lead from email extraction"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO leads
            (client_name, email, job_type, location, urgency, estimated_budget, status)
            VALUES (?, ?, ?, ?, ?, ?, 'new')
        """, (client_name, email, job_type, location, urgency, budget))

        lead_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"✅ Created lead: {client_name} ({job_type})")
        return {"lead_id": lead_id, "status": "created"}

    def get_leads(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get all leads, optionally filtered by status"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute("""
                SELECT * FROM leads
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM leads
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

        leads = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return leads

    def get_lead(self, lead_id: int) -> Dict:
        """Get single lead details"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead = cursor.fetchone()
        conn.close()

        return dict(lead) if lead else {}

    def update_lead_status(self, lead_id: int, status: str) -> Dict:
        """Update lead status (new → quoted → accepted)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE leads SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (status, lead_id))

        conn.commit()
        conn.close()

        return {"lead_id": lead_id, "status": status}

    # ===== QUOTES =====

    def create_quote(self, lead_id: int, client_name: str = None, job_type: str = None,
                    materials_cost: float = 0, labor_cost: float = 0,
                    markup_percent: float = 20) -> Dict:
        """Generate a quote for a lead. Inherits client_name/job_type from lead if not provided."""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # Auto-inherit contact data from lead record
        if lead_id:
            cursor.execute("SELECT client_name, job_type FROM leads WHERE id = ?", (lead_id,))
            row = cursor.fetchone()
            if row:
                client_name = client_name or row[0]
                job_type = job_type or row[1]

        client_name = client_name or "Unknown Client"
        job_type = job_type or "General"
        total = (materials_cost + labor_cost) * (1 + markup_percent / 100)

        cursor.execute("""
            INSERT INTO quotes
            (lead_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total_amount)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (lead_id, client_name, job_type, materials_cost, labor_cost, markup_percent, total))

        quote_id = cursor.lastrowid

        # Update lead status
        cursor.execute("""
            UPDATE leads SET status = 'quoted', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (lead_id,))

        conn.commit()
        conn.close()

        logger.info(f"✅ Created quote: {client_name} - ${total:,.2f}")
        return {
            "quote_id": quote_id,
            "total_amount": total,
            "status": "draft"
        }

    def get_quotes(self, status: str = None, limit: int = 50) -> List[Dict]:
        """Get all quotes, optionally filtered by status"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if status:
            cursor.execute("""
                SELECT * FROM quotes
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (status, limit))
        else:
            cursor.execute("""
                SELECT * FROM quotes
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))

        quotes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return quotes

    def get_quote(self, quote_id: int) -> Dict:
        """Get single quote details"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM quotes WHERE id = ?", (quote_id,))
        quote = cursor.fetchone()
        conn.close()

        return dict(quote) if quote else {}

    def get_pipeline_summary(self) -> Dict:
        """Get quote pipeline summary (total, pending, accepted, revenue)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM quotes")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) as pending FROM quotes WHERE status = 'sent'")
        pending = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) as accepted FROM quotes WHERE status = 'accepted'")
        accepted = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(total_amount) as revenue FROM quotes WHERE status IN ('accepted', 'invoiced')")
        revenue = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_quotes": total,
            "pending_quotes": pending,
            "accepted_quotes": accepted,
            "revenue_pipeline": float(revenue)
        }

    def update_quote_status(self, quote_id: int, status: str) -> Dict:
        """Update quote status (draft → sent → accepted → invoiced)"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        if status == 'sent':
            cursor.execute("""
                UPDATE quotes SET status = ?, sent_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, quote_id))
        elif status == 'accepted':
            cursor.execute("""
                UPDATE quotes SET status = ?, accepted_date = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, quote_id))
        else:
            cursor.execute("""
                UPDATE quotes SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, quote_id))

        conn.commit()
        conn.close()

        return {"quote_id": quote_id, "status": status}

    # ===== PAYMENTS =====

    def record_payment(self, quote_id: int, amount: float, client_name: str = None) -> Dict:
        """Record a payment received"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO payments
            (quote_id, client_name, amount, status, received_date)
            VALUES (?, ?, ?, 'received', CURRENT_TIMESTAMP)
        """, (quote_id, client_name, amount))

        payment_id = cursor.lastrowid
        conn.commit()
        conn.close()

        logger.info(f"✅ Recorded payment: ${amount:,.2f}")
        return {"payment_id": payment_id, "status": "received"}

    def get_payments(self, quote_id: int = None) -> List[Dict]:
        """Get all payments, optionally filtered by quote"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if quote_id:
            cursor.execute("SELECT * FROM payments WHERE quote_id = ?", (quote_id,))
        else:
            cursor.execute("SELECT * FROM payments ORDER BY received_date DESC")

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
