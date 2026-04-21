"""Stripe billing integration — checkout sessions, webhook handling, subscription status."""
import os
import logging
import sqlite3
import pathlib
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = pathlib.Path(__file__).resolve().parent.parent / "backpocket.db"

# Pricing (AUD Cents)
LIFETIME_PRICE_CENTS = 19900  # $199.00 AUD
MONTHLY_PRICE_CENTS = 2500    # $25.00 AUD

PLAN_MONTHLY = "monthly"
PLAN_LIFETIME = "lifetime"

# ── Schema bootstrap ──────────────────────────────────────────────────────────

def init_billing_table():
    con = sqlite3.connect(DB_PATH)
    # Add plan_type to track subscription vs lifetime
    con.execute("""
        CREATE TABLE IF NOT EXISTS billing_sessions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_email TEXT,
            session_id    TEXT UNIQUE,
            amount_cents  INTEGER,
            currency      TEXT DEFAULT 'aud',
            plan_type     TEXT, -- 'monthly' or 'lifetime'
            status        TEXT DEFAULT 'pending',
            stripe_customer_id TEXT,
            stripe_subscription_id TEXT,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    con.commit()
    con.close()


# ── Stripe API helpers ─────────────────────────────────────────────────────────

def _stripe():
    """Lazy-import stripe so app boots without the package when unused."""
    try:
        import stripe as _s
        _s.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        if not _s.api_key:
            raise RuntimeError("STRIPE_SECRET_KEY not set in environment")
        return _s
    except ImportError:
        raise RuntimeError("stripe package not installed. Run: pip install stripe")


async def create_checkout_session(
    plan: str = PLAN_MONTHLY,
    success_url: str = "https://backpocketsystem.io/success",
    cancel_url: str = "https://backpocketsystem.io/pricing",
    customer_email: str | None = None,
) -> dict:
    """Create a Stripe Checkout session for Monthly ($25) or Lifetime ($199)."""
    s = _stripe()
    
    if plan == PLAN_LIFETIME:
        amount = LIFETIME_PRICE_CENTS
        mode = "payment"
        name = "BackPocket OS — Lifetime Access"
        description = "One-time payment for lifetime access to your Digital Twin."
    else:
        amount = MONTHLY_PRICE_CENTS
        mode = "subscription"
        name = "BackPocket OS — Monthly Plan"
        description = "Full access to your AI Digital Twin for $25/month."

    params: dict = {
        "mode": mode,
        "line_items": [{
            "price_data": {
                "currency": "aud",
                "unit_amount": amount,
                "product_data": {
                    "name": name,
                    "description": description,
                },
            },
            "quantity": 1,
        }],
        "success_url": success_url + "?session_id={CHECKOUT_SESSION_ID}",
        "cancel_url": cancel_url,
    }
    
    # Add recurring interval for monthly plan
    if plan == PLAN_MONTHLY:
        params["line_items"][0]["price_data"]["recurring"] = {"interval": "month"}

    if customer_email:
        params["customer_email"] = customer_email

    session = s.checkout.Session.create(**params)

    # Persist to DB
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "INSERT OR IGNORE INTO billing_sessions (customer_email, session_id, amount_cents, plan_type, status) VALUES (?,?,?,?,?)",
        (customer_email, session.id, amount, plan, "pending"),
    )
    con.commit()
    con.close()

    logger.info(f"Stripe {plan} session created: {session.id}")
    return {"url": session.url, "session_id": session.id}


async def handle_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify Stripe webhook signature and process event."""
    s = _stripe()
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        raise RuntimeError("STRIPE_WEBHOOK_SECRET not set")

    try:
        event = s.Webhook.construct_event(payload, sig_header, webhook_secret)
    except s.error.SignatureVerificationError:
        raise ValueError("Invalid Stripe webhook signature")

    event_type = event["type"]
    logger.info(f"Stripe webhook: {event_type}")

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        _mark_session_paid(
            session["id"], 
            session.get("customer"), 
            session.get("subscription")
        )
    elif event_type == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        _cancel_subscription(subscription["id"])
    elif event_type in ("payment_intent.payment_failed", "checkout.session.expired"):
        session = event["data"]["object"]
        _update_session_status(session.get("id"), "failed")

    return {"received": True, "type": event_type}


def get_subscription_status(customer_email: str | None = None) -> dict:
    """Return latest billing session status for a customer."""
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    row = con.execute(
        "SELECT * FROM billing_sessions ORDER BY created_at DESC LIMIT 1"
        if not customer_email else
        "SELECT * FROM billing_sessions WHERE customer_email=? ORDER BY created_at DESC LIMIT 1",
        () if not customer_email else (customer_email,),
    ).fetchone()
    con.close()
    if not row:
        return {"status": "none", "plan": None, "amount_cents": 0}
    return dict(row)


def _mark_session_paid(session_id: str, stripe_customer_id: str | None, stripe_subscription_id: str | None):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "UPDATE billing_sessions SET status='active', stripe_customer_id=?, stripe_subscription_id=?, updated_at=? WHERE session_id=?",
        (stripe_customer_id, stripe_subscription_id, datetime.utcnow().isoformat(), session_id),
    )
    con.commit()
    con.close()
    logger.info(f"Session {session_id} marked active")


def _cancel_subscription(subscription_id: str):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "UPDATE billing_sessions SET status='canceled', updated_at=? WHERE stripe_subscription_id=?",
        (datetime.utcnow().isoformat(), subscription_id),
    )
    con.commit()
    con.close()
    logger.info(f"Subscription {subscription_id} marked canceled")


def _update_session_status(session_id: str, status: str):
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "UPDATE billing_sessions SET status=?, updated_at=? WHERE session_id=?",
        (status, datetime.utcnow().isoformat(), session_id),
    )
    con.commit()
    con.close()
