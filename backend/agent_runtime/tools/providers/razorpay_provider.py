import os
import uuid
import time
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from .interfaces import PaymentProvider
from .mock_payment_provider import MockPaymentProvider

logger = logging.getLogger(__name__)


class RazorpayTestProvider(PaymentProvider):
    """
    Razorpay Test Mode provider with seamless fallback to deterministic simulation
    when external Razorpay APIs are unreachable or unconfigured.
    """

    def __init__(self):
        self.fallback = MockPaymentProvider()
        self.key_id = getattr(settings, "RAZORPAY_KEY_ID", "") or os.environ.get("RAZORPAY_KEY_ID", "")
        self.key_secret = getattr(settings, "RAZORPAY_KEY_SECRET", "") or os.environ.get("RAZORPAY_KEY_SECRET", "")
        self.has_credentials = bool(self.key_id and self.key_secret)

    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        if not self.has_credentials:
            return self.fallback.get_payment(payment_id)
        try:
            import requests
            res = requests.get(
                f"https://api.razorpay.com/v1/payments/{payment_id}",
                auth=(self.key_id, self.key_secret),
                timeout=4,
            )
            if res.status_code == 200:
                data = res.json()
                return {
                    "id": data.get("id"),
                    "amount": data.get("amount", 0) / 100.0,
                    "currency": data.get("currency", "INR"),
                    "status": data.get("status"),
                    "method": data.get("method"),
                    "created_at": data.get("created_at"),
                }
        except Exception as e:
            logger.warning(f"Razorpay API call failed, falling back to simulator: {e}")
        return self.fallback.get_payment(payment_id)

    def search_payments(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.fallback.search_payments(filters)

    def create_payment_intent(self, amount: float, currency: str, customer_id: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.has_credentials:
            return self.fallback.create_payment_intent(amount, currency, customer_id, metadata)
        try:
            import requests
            amount_paise = int(round(amount * 100))
            res = requests.post(
                "https://api.razorpay.com/v1/orders",
                auth=(self.key_id, self.key_secret),
                json={"amount": amount_paise, "currency": currency or "INR", "receipt": f"rcpt_{uuid.uuid4().hex[:8]}"},
                timeout=4,
            )
            if res.status_code in (200, 201):
                data = res.json()
                return {
                    "id": data.get("id"),
                    "amount": amount,
                    "currency": currency or "INR",
                    "status": data.get("status", "created"),
                    "client_secret": data.get("id"),
                    "created_at": int(time.time()),
                }
        except Exception as e:
            logger.warning(f"Razorpay order creation failed, falling back: {e}")
        return self.fallback.create_payment_intent(amount, currency, customer_id, metadata)

    def create_payment_link(self, amount: float, currency: str, customer_email: str, description: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        if not self.has_credentials:
            return self.fallback.create_payment_link(amount, currency, customer_email, description, metadata)
        try:
            import requests
            amount_paise = int(round(amount * 100))
            payload = {
                "amount": amount_paise,
                "currency": currency or "INR",
                "description": description or "Order Payment",
                "customer": {"email": customer_email},
                "notify": {"sms": False, "email": True},
            }
            res = requests.post(
                "https://api.razorpay.com/v1/payment_links",
                auth=(self.key_id, self.key_secret),
                json=payload,
                timeout=4,
            )
            if res.status_code in (200, 201):
                data = res.json()
                return {
                    "id": data.get("id"),
                    "short_url": data.get("short_url"),
                    "amount": amount,
                    "currency": currency or "INR",
                    "status": data.get("status"),
                    "created_at": int(time.time()),
                }
        except Exception as e:
            logger.warning(f"Razorpay payment link creation failed, falling back: {e}")
        return self.fallback.create_payment_link(amount, currency, customer_email, description, metadata)

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        return self.fallback.get_payment_status(payment_id)

    def create_refund(self, payment_id: str, amount: Optional[float] = None, reason: str = "") -> Dict[str, Any]:
        return self.fallback.create_refund(payment_id, amount, reason)

    def get_refunds(self, payment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.fallback.get_refunds(payment_id)
