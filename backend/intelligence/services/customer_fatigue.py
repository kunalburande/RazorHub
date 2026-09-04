"""
Customer Fatigue Protection & Suppression Guardrail Service.

Academic grounding:
Conversational agent literature highlights trust, usefulness, experience,
privacy/security, and context as essential adoption factors (2023 systematic review).
While most growth agents only optimize to "sell more", RazorHub implements
the counterbalancing objective: "don't annoy customers".

Fatigue Score Weights:
  +1 offer shown
  +2 offer rejected
  +3 offer explicitly declined
  +5 complaint
  +4 recent purchase
  +2 multiple interactions today

Rule:
  Fatigue > threshold  →  suppress recommendation

Benchmark Example:
  Customer rejected 3 offers today.
  Fatigue score = (3 * 1) + (3 * 2) = 9  (Threshold = 6)
  Agent: "No additional commercial recommendation will be shown."
"""
import logging
from typing import Dict, Any, Optional
from django.utils import timezone

from intelligence.models import AuditEvent

logger = logging.getLogger(__name__)


class CustomerFatigueService:
    """Computes customer fatigue score and enforces recommendation suppression."""

    FATIGUE_WEIGHTS = {
        "offer_shown": 1,
        "offer_rejected": 2,
        "offer_explicitly_declined": 3,
        "complaint": 5,
        "recent_purchase": 4,
        "multiple_interactions_today": 2
    }

    DEFAULT_THRESHOLD = 6

    # In-memory customer event tracker: customer_id -> dict of counts
    _customer_events: Dict[str, Dict[str, int]] = {}

    @classmethod
    def calculate_fatigue_score(cls, events: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the additive fatigue score from an interaction event breakdown.
        """
        shown = int(events.get("offers_shown", 0) or events.get("offer_shown", 0))
        rejected = int(events.get("offers_rejected", 0) or events.get("offer_rejected", 0))
        declined = int(events.get("offers_explicitly_declined", 0) or events.get("offer_explicitly_declined", 0))
        complaints = int(events.get("complaints", 0) or events.get("complaint", 0))
        recent_purchases = int(events.get("recent_purchases", 0) or events.get("recent_purchase", 0))
        multi_interactions = 1 if events.get("multiple_interactions_today") else 0

        score = (
            (shown * cls.FATIGUE_WEIGHTS["offer_shown"]) +
            (rejected * cls.FATIGUE_WEIGHTS["offer_rejected"]) +
            (declined * cls.FATIGUE_WEIGHTS["offer_explicitly_declined"]) +
            (complaints * cls.FATIGUE_WEIGHTS["complaint"]) +
            (recent_purchases * cls.FATIGUE_WEIGHTS["recent_purchase"]) +
            (multi_interactions * cls.FATIGUE_WEIGHTS["multiple_interactions_today"])
        )

        breakdown = {
            "offers_shown": {"count": shown, "weight": 1, "points": shown * 1},
            "offers_rejected": {"count": rejected, "weight": 2, "points": rejected * 2},
            "offers_explicitly_declined": {"count": declined, "weight": 3, "points": declined * 3},
            "complaints": {"count": complaints, "weight": 5, "points": complaints * 5},
            "recent_purchases": {"count": recent_purchases, "weight": 4, "points": recent_purchases * 4},
            "multiple_interactions_today": {"count": multi_interactions, "weight": 2, "points": multi_interactions * 2},
        }

        return {
            "fatigue_score": score,
            "breakdown": breakdown
        }

    @classmethod
    def evaluate_suppression(
        cls,
        customer_id_or_events: Any,
        threshold: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Evaluates whether recommendations should be suppressed for a customer.
        Returns is_suppressed=True and benchmark explanation copy when score >= threshold.
        """
        limit = threshold if threshold is not None else cls.DEFAULT_THRESHOLD

        if isinstance(customer_id_or_events, dict):
            events = customer_id_or_events
            cid = str(events.get("customer_id", "guest"))
        else:
            cid = str(customer_id_or_events or "guest")
            events = cls._customer_events.get(cid, {
                "offers_shown": 0,
                "offers_rejected": 0,
                "offers_explicitly_declined": 0,
                "complaints": 0,
                "recent_purchases": 0,
                "multiple_interactions_today": 0
            })

        calc = cls.calculate_fatigue_score(events)
        score = calc["fatigue_score"]
        is_suppressed = score >= limit

        if is_suppressed:
            response_msg = "No additional commercial recommendation will be shown."
            reason = (
                f"Customer fatigue score ({score}) exceeds threshold ({limit}). "
                f"Commercial offers suppressed to protect customer trust and long-term value."
            )
        else:
            response_msg = None
            reason = f"Customer fatigue score ({score}) within safe limit ({limit})."

        return {
            "customer_id": cid,
            "fatigue_score": score,
            "threshold": limit,
            "is_suppressed": is_suppressed,
            "response_message": response_msg,
            "suppression_reason": reason,
            "breakdown": calc["breakdown"]
        }

    @classmethod
    def record_customer_rejection(cls, customer_id: str = "guest", count: int = 1) -> Dict[str, Any]:
        """Convenience method to register rejected offers for a customer."""
        current = cls._customer_events.setdefault(customer_id, {
            "offers_shown": 0,
            "offers_rejected": 0,
            "offers_explicitly_declined": 0,
            "complaints": 0,
            "recent_purchases": 0,
            "multiple_interactions_today": 0
        })
        current["offers_shown"] += count
        current["offers_rejected"] += count
        return cls.evaluate_suppression(current)
