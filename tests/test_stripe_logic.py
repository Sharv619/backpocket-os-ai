
import os
import sqlite3
import asyncio
from unittest.mock import MagicMock, patch
from services.stripe import (
    init_billing_table, 
    create_checkout_session, 
    handle_webhook, 
    get_subscription_status,
    PLAN_MONTHLY,
    PLAN_LIFETIME,
    DB_PATH
)

async def test_stripe_logic():
    print("Testing Stripe Logic...")
    
    # Setup test DB
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    init_billing_table()
    
    # Mock Stripe
    mock_stripe = MagicMock()
    mock_session = MagicMock()
    mock_session.id = "cs_test_123"
    mock_session.url = "https://checkout.stripe.com/test"
    mock_stripe.checkout.Session.create.return_value = mock_session
    
    with patch("services.stripe._stripe", return_value=mock_stripe):
        # Test 1: Create Monthly Session
        print("1. Creating Monthly Session...")
        res = await create_checkout_session(plan=PLAN_MONTHLY, customer_email="test@example.com")
        assert res["session_id"] == "cs_test_123"
        
        status = get_subscription_status("test@example.com")
        assert status["plan_type"] == PLAN_MONTHLY
        assert status["status"] == "pending"
        
        # Test 2: Webhook - Mark Paid
        print("2. Handling Webhook (Completed)...")
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "checkout.session.completed",
            "data": {"object": {"id": "cs_test_123", "customer": "cus_test", "subscription": "sub_test"}}
        }
        os.environ["STRIPE_WEBHOOK_SECRET"] = "whsec_test"
        
        await handle_webhook(b"payload", "sig")
        
        status = get_subscription_status("test@example.com")
        assert status["status"] == "active"
        assert status["stripe_customer_id"] == "cus_test"
        assert status["stripe_subscription_id"] == "sub_test"

        # Test 3: Webhook - Cancel Subscription
        print("3. Handling Webhook (Canceled)...")
        mock_stripe.Webhook.construct_event.return_value = {
            "type": "customer.subscription.deleted",
            "data": {"object": {"id": "sub_test"}}
        }
        
        await handle_webhook(b"payload", "sig")
        
        status = get_subscription_status("test@example.com")
        assert status["status"] == "canceled"
        
    print("✅ All Stripe logic tests passed!")

if __name__ == "__main__":
    os.environ["STRIPE_SECRET_KEY"] = "sk_test_mock"
    asyncio.run(test_stripe_logic())
