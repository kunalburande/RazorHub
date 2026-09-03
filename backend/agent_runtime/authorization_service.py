import logging
from decimal import Decimal
from typing import Dict, Any, Optional
from django.db import transaction
from django.utils import timezone

from .models import (
    AgentPaymentAuthorization,
    AgentAuthorizationLedger,
    Agent,
)

logger = logging.getLogger(__name__)


class AuthorizationDecision:
    AUTO_APPROVED = "AUTO_APPROVED"
    REQUIRES_CONFIRMATION = "REQUIRES_CONFIRMATION"
    BLOCKED = "BLOCKED"
    DUPLICATE = "DUPLICATE"


class AgentAuthorizationService:
    """
    Simulated agent payment authorization service inspired by consent-based pre-authorized
    payment concepts (e.g. UPI Reserve Pay).
    Provides atomic concurrency protection, idempotency enforcement, and real-time limit depletion.
    """

    @classmethod
    def verify_and_consume(
        cls,
        auth_id: str,
        amount: Decimal,
        merchant: str,
        category: str,
        idempotency_key: str,
        is_confirmation: bool = False,
    ) -> Dict[str, Any]:
        """
        Atomically verifies authorization and consumes daily/monthly limits.
        Protected by database row-level locking (select_for_update) and idempotency deduplication.
        """
        if amount <= Decimal("0.00"):
            return {
                "decision": AuthorizationDecision.BLOCKED,
                "reason": "Transaction amount must be strictly greater than zero.",
            }

        with transaction.atomic():
            # 1. Row-level lock to prevent concurrent race conditions
            try:
                auth = (
                    AgentPaymentAuthorization.objects.select_for_update()
                    .get(id=auth_id)
                )
            except AgentPaymentAuthorization.DoesNotExist:
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": "Payment authorization record not found.",
                }

            # 2. Check for duplicate payment via idempotency key
            existing_ledger = AgentAuthorizationLedger.objects.filter(
                idempotency_key=idempotency_key
            ).first()
            if existing_ledger:
                return {
                    "decision": AuthorizationDecision.DUPLICATE,
                    "reason": "Duplicate transaction detected; idempotency key already consumed.",
                    "cached_decision": existing_ledger.decision,
                    "idempotency_key": idempotency_key,
                    "used_today": float(auth.used_today),
                    "used_this_month": float(auth.used_this_month),
                }

            # 3. Handle calendar day and month rollovers
            auth.check_and_reset_rollover()

            # 4. Status Check
            if auth.status != AgentPaymentAuthorization.AuthStatus.ACTIVE:
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": f"Authorization is not active (Current status: {auth.status}).",
                    "status": auth.status,
                }

            # 5. Check Expiration
            if auth.expires_at and timezone.now() > auth.expires_at:
                auth.status = AgentPaymentAuthorization.AuthStatus.EXPIRED
                auth.save(update_fields=["status", "updated_at"])
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": f"Authorization expired at {auth.expires_at.isoformat()}.",
                    "status": auth.status,
                }

            # 6. Check Category Constraints
            cat_lower = category.lower().strip()
            if auth.blocked_categories and any(b.lower().strip() == cat_lower for b in auth.blocked_categories):
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": f"Category '{category}' is blocked by consent policy.",
                }

            if auth.allowed_categories and not any(a.lower().strip() == cat_lower for a in auth.allowed_categories):
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": f"Category '{category}' is not within authorized categories.",
                }

            # 7. Check Merchant Constraints
            merch_lower = merchant.lower().strip()
            if auth.blocked_merchants and any(b.lower().strip() in merch_lower for b in auth.blocked_merchants):
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": f"Merchant '{merchant}' is blocked by consent policy.",
                }

            if auth.allowed_merchants and not any(a.lower().strip() in merch_lower for a in auth.allowed_merchants):
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": f"Merchant '{merchant}' is not within authorized merchants list.",
                }

            # 8. Check Max Per-Transaction Ceiling
            if amount > auth.max_transaction_amount:
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": (
                        f"Amount ₹{amount:,.2f} exceeds maximum authorized transaction limit "
                        f"of ₹{auth.max_transaction_amount:,.2f}."
                    ),
                }

            # 9. Check Daily Limit
            if auth.used_today + amount > auth.daily_limit:
                remaining_today = max(Decimal("0.00"), auth.daily_limit - auth.used_today)
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": (
                        f"Transaction of ₹{amount:,.2f} exceeds remaining daily limit "
                        f"(Available today: ₹{remaining_today:,.2f} of ₹{auth.daily_limit:,.2f})."
                    ),
                }

            # 10. Check Monthly Limit
            if auth.used_this_month + amount > auth.monthly_limit:
                remaining_month = max(Decimal("0.00"), auth.monthly_limit - auth.used_this_month)
                return {
                    "decision": AuthorizationDecision.BLOCKED,
                    "reason": (
                        f"Transaction of ₹{amount:,.2f} exceeds remaining monthly limit "
                        f"(Available this month: ₹{remaining_month:,.2f} of ₹{auth.monthly_limit:,.2f})."
                    ),
                }

            # 11. Check Automatic Approval Threshold
            before_today = auth.used_today
            before_month = auth.used_this_month

            if amount >= auth.approval_threshold and not is_confirmation:
                # Requires explicit human confirmation
                return {
                    "decision": AuthorizationDecision.REQUIRES_CONFIRMATION,
                    "reason": (
                        f"Amount ₹{amount:,.2f} reaches confirmation threshold "
                        f"(₹{auth.approval_threshold:,.2f} - ₹{auth.max_transaction_amount:,.2f})."
                    ),
                    "auth_id": str(auth.id),
                    "amount": float(amount),
                    "merchant": merchant,
                    "category": category,
                    "used_today": float(auth.used_today),
                    "used_this_month": float(auth.used_this_month),
                    "daily_limit": float(auth.daily_limit),
                    "monthly_limit": float(auth.monthly_limit),
                }

            # 12. Consume Limits Atomically
            auth.used_today += amount
            auth.used_this_month += amount
            auth.save(update_fields=["used_today", "used_this_month", "updated_at"])

            # 13. Write Ledger Entry with Idempotency Key
            decision = (
                AuthorizationDecision.AUTO_APPROVED
                if amount < auth.approval_threshold
                else "CONFIRMED_AND_CONSUMED"
            )

            AgentAuthorizationLedger.objects.create(
                authorization=auth,
                idempotency_key=idempotency_key,
                amount=amount,
                merchant=merchant,
                category=category,
                decision=decision,
                reason="Pre-authorized consent criteria validated and limits deducted.",
                before_today=before_today,
                after_today=auth.used_today,
                before_month=before_month,
                after_month=auth.used_this_month,
            )

            return {
                "decision": AuthorizationDecision.AUTO_APPROVED,
                "status": "CONSUMED",
                "auth_id": str(auth.id),
                "amount": float(amount),
                "merchant": merchant,
                "category": category,
                "used_today": float(auth.used_today),
                "used_this_month": float(auth.used_this_month),
                "remaining_today": float(auth.daily_limit - auth.used_today),
                "remaining_month": float(auth.monthly_limit - auth.used_this_month),
                "idempotency_key": idempotency_key,
            }
