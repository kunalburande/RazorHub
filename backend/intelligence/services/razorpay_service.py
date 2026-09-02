import razorpay
import time
import uuid
import logging
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)


class RazorpayService:
    """
    Unified Razorpay integration service for RazorHub Agentic Commerce.
    All methods gracefully fall back to mock mode when API keys are absent.
    """

    @classmethod
    def _has_keys(cls):
        return bool(getattr(settings, 'RAZORPAY_KEY_ID', None))

    @classmethod
    def get_client(cls):
        return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # ── Order API ──────────────────────────────────────────────────────────

    @classmethod
    def create_order(cls, amount, receipt, notes=None):
        """Create a Razorpay order. Amount in INR → converted to paise."""
        amount_in_paise = int(Decimal(str(amount)) * 100)

        if not cls._has_keys():
            return {
                "id": f"order_mock_{receipt}_{uuid.uuid4().hex[:8]}",
                "amount": amount_in_paise,
                "currency": "INR",
                "receipt": receipt,
                "status": "created",
                "notes": notes or {},
            }

        client = cls.get_client()
        data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": receipt,
            "payment_capture": 1,
        }
        if notes:
            data["notes"] = notes

        try:
            return client.order.create(data=data)
        except Exception as e:
            logger.error(f"[RazorpayService] create_order failed: {e}")
            raise

    @classmethod
    def fetch_order(cls, order_id):
        """Fetch an existing Razorpay order by ID."""
        if not cls._has_keys() or order_id.startswith("order_mock_"):
            return {
                "id": order_id,
                "status": "created",
                "amount": 0,
                "currency": "INR",
            }

        client = cls.get_client()
        try:
            return client.order.fetch(order_id)
        except Exception as e:
            logger.error(f"[RazorpayService] fetch_order failed: {e}")
            return {"id": order_id, "status": "unknown", "error": str(e)}

    # ── Payment Link API ───────────────────────────────────────────────────

    @classmethod
    def create_payment_link(cls, amount, description, notes=None, expire_by=None,
                            customer=None, callback_url=None):
        """
        Create a Razorpay Payment Link (for upsell, agent-initiated checkout, etc.).
        Amount in INR → paise.  Returns link dict with 'short_url' and 'id'.
        """
        amount_in_paise = int(Decimal(str(amount)) * 100)

        if not cls._has_keys():
            mock_id = f"plink_mock_{uuid.uuid4().hex[:8]}"
            return {
                "id": mock_id,
                "amount": amount_in_paise,
                "currency": "INR",
                "description": description,
                "short_url": f"https://rzp.io/i/{mock_id}",
                "status": "created",
                "notes": notes or {},
                "expire_by": expire_by,
            }

        client = cls.get_client()
        data = {
            "amount": amount_in_paise,
            "currency": "INR",
            "description": description[:250],
            "notes": notes or {},
        }
        if expire_by:
            data["expire_by"] = expire_by
        if customer:
            data["customer"] = customer
        if callback_url:
            data["callback_url"] = callback_url

        try:
            return client.payment_link.create(data=data)
        except Exception as e:
            logger.error(f"[RazorpayService] create_payment_link failed: {e}")
            raise

    # ── Payment API ────────────────────────────────────────────────────────

    @classmethod
    def fetch_payment(cls, payment_id):
        """Fetch payment status by payment ID."""
        if not cls._has_keys() or payment_id.startswith("pay_mock_"):
            return {
                "id": payment_id,
                "status": "captured",
                "amount": 0,
                "currency": "INR",
                "method": "mock",
            }

        client = cls.get_client()
        try:
            return client.payment.fetch(payment_id)
        except Exception as e:
            logger.error(f"[RazorpayService] fetch_payment failed: {e}")
            return {"id": payment_id, "status": "unknown", "error": str(e)}

    # ── Refund API ─────────────────────────────────────────────────────────

    @classmethod
    def create_refund(cls, payment_id, amount=None, notes=None):
        """Create a refund for a payment. Partial refund if amount specified."""
        if not cls._has_keys() or payment_id.startswith("pay_mock_"):
            return {
                "id": f"rfnd_mock_{uuid.uuid4().hex[:8]}",
                "payment_id": payment_id,
                "amount": int(Decimal(str(amount)) * 100) if amount else 0,
                "status": "processed",
            }

        client = cls.get_client()
        data = {}
        if amount:
            data["amount"] = int(Decimal(str(amount)) * 100)
        if notes:
            data["notes"] = notes

        try:
            return client.payment.refund(payment_id, data)
        except Exception as e:
            logger.error(f"[RazorpayService] create_refund failed: {e}")
            raise

    # ── Signature Verification ─────────────────────────────────────────────

    @classmethod
    def verify_signature(cls, order_id, payment_id, signature):
        """Verify the signature returned by Razorpay."""
        client = cls.get_client()
        try:
            return client.utility.verify_payment_signature({
                'razorpay_order_id': order_id,
                'razorpay_payment_id': payment_id,
                'razorpay_signature': signature,
            })
        except razorpay.errors.SignatureVerificationError:
            return False

    @classmethod
    def verify_webhook_signature(cls, body, signature):
        """Verify webhook signature."""
        client = cls.get_client()
        try:
            return client.utility.verify_webhook_signature(
                body,
                signature,
                settings.RAZORPAY_WEBHOOK_SECRET,
            )
        except razorpay.errors.SignatureVerificationError:
            return False
