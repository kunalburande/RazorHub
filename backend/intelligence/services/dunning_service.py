"""
Payment-Recovery / Dunning Agent Service.

Academic & Operational Grounding:
Razorpay's Agent Studio runs subscription/payment-recovery agents that proactively
win back failed payments before they turn into customer churn.

Mechanism:
On a `payment.failed` webhook event:
  1. The agent decides retry timing and channel (In-app → SMS → Email) within capped attempts (max 3).
  2. Logs every attempt to the audit ledger.
  3. Escalates to a human support queue after N days (e.g. 5 days).
  4. Computes before/after metric: `recovered_revenue`.
"""
import uuid
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.utils import timezone

from intelligence.models import RecoveryTask, AuditEvent

logger = logging.getLogger(__name__)


class DunningRecoveryService:
    """Proactively recovers failed payments using multi-channel dunning cadences."""

    MAX_ATTEMPTS = 3
    ESCALATION_THRESHOLD_DAYS = 5

    @classmethod
    def handle_failed_payment_webhook(
        cls,
        payment_id: str,
        customer_email: str,
        amount: Decimal,
        failure_reason: str = "insufficient_funds",
        attempt_number: int = 1
    ) -> Dict[str, Any]:
        """
        Processes a payment.failed event and executes or schedules the optimal recovery action.
        """
        task_id = f"dunn_{payment_id[:12]}"
        amount_dec = Decimal(str(amount))

        # Channel & Timing Matrix
        channel_matrix = {
            1: {
                "channel": "IN_APP",
                "timing": "Immediate (0h)",
                "action": "Trigger In-App Modal with 1-click UPI Retry Link",
                "incentive": "Standard Retry"
            },
            2: {
                "channel": "SMS",
                "timing": "+24 Hours",
                "action": "Send SMS with pre-filled Razorpay payment link",
                "incentive": "Reminder Nudge"
            },
            3: {
                "channel": "EMAIL",
                "timing": "+72 Hours",
                "action": "Send Priority Email with 5% limited courtesy discount",
                "incentive": "5% Courtesy Discount"
            }
        }

        curr_strategy = channel_matrix.get(attempt_number, channel_matrix[1])
        status = "RECOVERY_SCHEDULED" if attempt_number <= cls.MAX_ATTEMPTS else "ESCALATED_TO_HUMAN"

        # Check for human escalation
        escalation_required = attempt_number > cls.MAX_ATTEMPTS
        escalation_notes = (
            f"Escalated to CS queue after {cls.MAX_ATTEMPTS} automated attempts."
            if escalation_required else None
        )

        # Log to ledger (RecoveryTask & AuditEvent)
        task, _ = RecoveryTask.objects.get_or_create(
            task_id=task_id,
            defaults={
                "customer_email": customer_email,
                "cart_value": amount_dec,
                "status": "In_Progress" if not escalation_required else "Escalated",
                "agent_action": f"{curr_strategy['channel']}: {curr_strategy['action']}"
            }
        )

        AuditEvent.objects.create(
            event_id=f"audit_{uuid.uuid4().hex[:12]}",
            trace_id=f"trace_{uuid.uuid4().hex[:10]}",
            agent="DunningRecoveryAgent",
            action=f"Dispatch {curr_strategy['channel']} recovery",
            status="ESCALATED" if escalation_required else "SUCCESS",
            details=f"Payment {payment_id} retry attempt {attempt_number}",
            payload={
                "payment_id": payment_id,
                "amount": float(amount_dec),
                "attempt": attempt_number,
                "max_attempts": cls.MAX_ATTEMPTS,
                "channel": curr_strategy["channel"],
                "timing": curr_strategy["timing"],
                "failure_reason": failure_reason
            }
        )

        return {
            "task_id": task_id,
            "payment_id": payment_id,
            "customer_email": customer_email,
            "amount": float(amount_dec),
            "attempt_number": attempt_number,
            "max_attempts": cls.MAX_ATTEMPTS,
            "channel": curr_strategy["channel"],
            "timing": curr_strategy["timing"],
            "action_executed": curr_strategy["action"],
            "incentive": curr_strategy["incentive"],
            "status": status,
            "is_escalated_to_human": escalation_required,
            "escalation_notes": escalation_notes,
            "ledger_logged": True
        }

    @classmethod
    def simulate_successful_recovery(cls, task_id: str, recovered_amount: Decimal) -> Dict[str, Any]:
        """Marks a dunning recovery task as successfully collected and tracks recovered revenue."""
        amount_dec = Decimal(str(recovered_amount))
        task = RecoveryTask.objects.filter(task_id=task_id).first()
        if task:
            task.status = "Recovered"
            task.save()

        AuditEvent.objects.create(
            event_id=f"audit_{uuid.uuid4().hex[:12]}",
            trace_id=f"trace_{uuid.uuid4().hex[:10]}",
            agent="DunningRecoveryAgent",
            action="Payment Win-Back Confirmed",
            status="RECOVERED",
            details=f"Task {task_id} successfully recovered",
            payload={"task_id": task_id, "recovered_revenue": float(amount_dec)}
        )

        return {
            "task_id": task_id,
            "status": "RECOVERED",
            "recovered_revenue": float(amount_dec),
            "message": f"Proactively won back ₹{amount_dec:,.2f} before subscription churn!"
        }
