# Generated routes/billing.py

from fastapi import APIRouter, Request, status, Depends
from pydantic import BaseModel
from services.stripe import create_checkout_session, handle_webhook

router = APIRouter()

# Checkou session request model
class CheckoutRequest(BaseModel):
    amount: float
    success_url: str = 'https://yourdomain.com/success'
    cancel_url: str = 'https://yourdomain.com/cancel'

# Create checkout session endpoint
@router.post('/create-checkout-session')
async def create_session(request: CheckoutRequest):
    try:
        session = await create_checkout_session(
            amount=request.amount,  # Convert to cents in frontend
            success_url=request.success_url,
            cancel_url=request.cancel_url
        )
        return {
            "url": session.url,
            "id": session.id
        }
    except Exception as e:
        return {
            "error": str(e)
        }, status.HTTP_500_INTERNAL_SERVER_ERROR

# Webhook endpoint
@router.post('/webhook', status_code=status.HTTP_200_OK)
async def webhook(request: Request):
    # Extract signature from headers
    signature = request.headers.get('STRIPE_SIGNATURE')
    event_data = await request.json()
    try:
        result = await handle_webhook(event_data, signature)
        return {"status": "success"}
    except Exception as e:
        return {"error": str(e)}, status.HTTP_400_BAD_REQUEST