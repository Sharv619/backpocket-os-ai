"""Tests for billing service (offline — no real Stripe calls)."""
import sqlite3
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture(autouse=True)
def tmp_db(tmp_path, monkeypatch):
    """Use a temp SQLite DB for each test."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_fake")
    import services.stripe as s
    monkeypatch.setattr(s, "DB_PATH", tmp_path / "test.db")
    s.init_billing_table()
    yield db_file


class TestBillingTable:
    def test_table_created(self, tmp_path):
        import services.stripe as s
        con = sqlite3.connect(str(s.DB_PATH))
        tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "billing_sessions" in tables
        con.close()

    def test_pilot_price_is_19900(self):
        from services.stripe import PILOT_PRICE_AUD_CENTS
        assert PILOT_PRICE_AUD_CENTS == 19900


class TestCheckoutSession:
    @pytest.mark.asyncio
    async def test_create_session_returns_url_and_id(self, monkeypatch):
        import services.stripe as svc

        mock_session = MagicMock()
        mock_session.id = "cs_test_abc123"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_abc123"

        mock_stripe = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch.object(svc, "_stripe", return_value=mock_stripe):
            result = await svc.create_checkout_session(
                amount=19900,
                success_url="https://example.com/success",
                cancel_url="https://example.com/cancel",
                customer_email="test@example.com",
            )

        assert result["url"] == "https://checkout.stripe.com/pay/cs_test_abc123"
        assert result["session_id"] == "cs_test_abc123"

    @pytest.mark.asyncio
    async def test_creates_db_record(self, monkeypatch):
        import services.stripe as svc

        mock_session = MagicMock()
        mock_session.id = "cs_test_xyz"
        mock_session.url = "https://checkout.stripe.com/pay/cs_test_xyz"
        mock_stripe = MagicMock()
        mock_stripe.checkout.Session.create.return_value = mock_session

        with patch.object(svc, "_stripe", return_value=mock_stripe):
            await svc.create_checkout_session(customer_email="tradie@example.com")

        status = svc.get_subscription_status("tradie@example.com")
        assert status["session_id"] == "cs_test_xyz"
        assert status["status"] == "pending"


class TestWebhookHandler:
    @pytest.mark.asyncio
    async def test_invalid_signature_raises(self):
        import services.stripe as svc

        mock_stripe = MagicMock()
        mock_stripe.error.SignatureVerificationError = Exception
        mock_stripe.Webhook.construct_event.side_effect = Exception("bad sig")

        with patch.object(svc, "_stripe", return_value=mock_stripe):
            with pytest.raises(ValueError, match="Invalid Stripe webhook signature"):
                await svc.handle_webhook(b'{"type":"test"}', "bad_sig")


class TestSubscriptionStatus:
    def test_no_sessions_returns_none_status(self):
        from services.stripe import get_subscription_status
        result = get_subscription_status("nobody@example.com")
        assert result["status"] == "none"
