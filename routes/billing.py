"""Billing routes — Stripe checkout, webhook, subscription status."""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from services.stripe import (
    create_checkout_session,
    handle_webhook,
    get_subscription_status,
    init_billing_table,
    PLAN_MONTHLY,
    PLAN_LIFETIME,
)

router = APIRouter(prefix="/api/billing", tags=["billing"])

try:
    init_billing_table()
except Exception:
    pass


class CheckoutRequest(BaseModel):
    customer_email: str | None = None
    plan: str = PLAN_MONTHLY
    success_url: str = "https://backpocketsystem.io/success"
    cancel_url: str = "https://backpocketsystem.io/pricing"


@router.post("/checkout")
async def create_session(body: CheckoutRequest):
    """Create a Stripe Checkout session (Monthly or Lifetime)."""
    try:
        return await create_checkout_session(
            plan=body.plan,
            success_url=body.success_url,
            cancel_url=body.cancel_url,
            customer_email=body.customer_email,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events (payment success, failure)."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        result = await handle_webhook(payload, sig_header)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def billing_status(email: str | None = None):
    """Return current billing/subscription status."""
    return get_subscription_status(customer_email=email)
