import uuid
import time
from typing import Dict, Any, Optional
from .interfaces import BankingProvider


class MockBankingProvider(BankingProvider):
    """
    Simulated banking, treasury, payouts, and settlement provider.
    Enables realistic cashflow forecasting and autonomous payout handling offline.
    """

    def __init__(self):
        self._payouts: Dict[str, Dict[str, Any]] = {}
        self._settlements: Dict[str, Dict[str, Any]] = {
            "setl_mock_001": {
                "id": "setl_mock_001",
                "amount": 142500.0,
                "fees": 2850.0,
                "tax": 513.0,
                "net_amount": 139137.0,
                "status": "processed",
                "utr": "UTR99283819283",
                "created_at": int(time.time()) - 86400,
            }
        }

    def create_payout(self, recipient_account: str, amount: float, currency: str = "INR", narration: str = "") -> Dict[str, Any]:
        payout_id = f"pout_mock_{uuid.uuid4().hex[:10]}"
        record = {
            "id": payout_id,
            "recipient_account": recipient_account,
            "amount": float(amount),
            "currency": currency or "INR",
            "status": "queued",
            "mode": "NEFT",
            "narration": narration or "Agent Payout Disbursement",
            "created_at": int(time.time()),
        }
        self._payouts[payout_id] = record
        return record

    def get_payout(self, payout_id: str) -> Dict[str, Any]:
        if payout_id in self._payouts:
            return self._payouts[payout_id]
        return {
            "id": payout_id,
            "recipient_account": "ACC_VEND_99",
            "amount": 5000.0,
            "currency": "INR",
            "status": "processed",
            "mode": "IMPS",
            "utr": f"UTR_{uuid.uuid4().hex[:12].upper()}",
            "created_at": int(time.time()),
        }

    def get_settlement(self, settlement_id: Optional[str] = None) -> Dict[str, Any]:
        if settlement_id and settlement_id in self._settlements:
            return self._settlements[settlement_id]
        return list(self._settlements.values())[0]

    def get_cashflow(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        return {
            "period": f"{start_date or '30_days_ago'} to {end_date or 'today'}",
            "opening_balance": 245000.0,
            "total_inflows": 182500.0,
            "total_outflows": 74200.0,
            "net_cashflow": 108300.0,
            "closing_balance": 353300.0,
            "currency": "INR",
            "projected_30d_burn": 65000.0,
            "runway_months": 5.4,
        }
