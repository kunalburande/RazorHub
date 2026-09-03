import uuid
import time
from typing import Dict, Any, List, Optional
from .interfaces import PaymentProvider


class MockPaymentProvider(PaymentProvider):
    """
    Deterministic, in-memory mock payment provider.
    Works with 100% reliability offline without external credentials.
    """

    def __init__(self):
        self._payments: Dict[str, Dict[str, Any]] = {
            "pay_mock_1001": {
                "id": "pay_mock_1001",
                "amount": 2999.0,
                "currency": "INR",
                "status": "captured",
                "method": "upi",
                "customer_email": "buyer@example.com",
                "created_at": int(time.time()) - 3600,
            },
            "pay_mock_1002": {
                "id": "pay_mock_1002",
                "amount": 14999.0,
                "currency": "INR",
                "status": "authorized",
                "method": "card",
                "customer_email": "vip@example.com",
                "created_at": int(time.time()) - 1800,
            },
        }
        self._refunds: Dict[str, Dict[str, Any]] = {}

    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        if payment_id in self._payments:
            return self._payments[payment_id]
        return {
            "id": payment_id,
            "amount": 1000.0,
            "currency": "INR",
            "status": "captured",
            "method": "upi",
            "created_at": int(time.time()),
        }

    def search_payments(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        status = filters.get("status")
        results = list(self._payments.values())
        if status:
            results = [p for p in results if p.get("status") == status]
        return results

    def create_payment_intent(self, amount: float, currency: str, customer_id: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        pid = f"pi_mock_{uuid.uuid4().hex[:10]}"
        record = {
            "id": pid,
            "amount": float(amount),
            "currency": currency or "INR",
            "status": "requires_payment_method",
            "customer_id": customer_id,
            "client_secret": f"{pid}_secret_{uuid.uuid4().hex[:8]}",
            "metadata": metadata or {},
            "created_at": int(time.time()),
        }
        self._payments[pid] = record
        return record

    def create_payment_link(self, amount: float, currency: str, customer_email: str, description: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        plink_id = f"plink_mock_{uuid.uuid4().hex[:10]}"
        return {
            "id": plink_id,
            "short_url": f"https://rzp.io/i/{plink_id[6:]}",
            "amount": float(amount),
            "currency": currency or "INR",
            "status": "created",
            "customer": {"email": customer_email},
            "description": description or "Order Payment",
            "created_at": int(time.time()),
        }

    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        p = self.get_payment(payment_id)
        return {
            "payment_id": payment_id,
            "status": p.get("status", "captured"),
            "amount": p.get("amount", 0.0),
            "currency": p.get("currency", "INR"),
            "captured": p.get("status") == "captured",
        }

    def create_refund(self, payment_id: str, amount: Optional[float] = None, reason: str = "") -> Dict[str, Any]:
        ref_id = f"rfnd_mock_{uuid.uuid4().hex[:10]}"
        orig = self.get_payment(payment_id)
        refund_amount = float(amount) if amount is not None else float(orig.get("amount", 0.0))
        record = {
            "id": ref_id,
            "payment_id": payment_id,
            "amount": refund_amount,
            "currency": orig.get("currency", "INR"),
            "status": "processed",
            "reason": reason or "Customer requested refund",
            "created_at": int(time.time()),
        }
        self._refunds[ref_id] = record
        return record

    def get_refunds(self, payment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        results = list(self._refunds.values())
        if payment_id:
            results = [r for r in results if r.get("payment_id") == payment_id]
        return results
