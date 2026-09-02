"""
Universal Commerce Audit Service for RazorHub Agentic Commerce.

Every agent action that touches money logs a structured audit event matching
the schema defined in analysis_results.md Section 5.
"""
import uuid
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class CommerceAuditService:

    @classmethod
    def log_audit_event(cls, agent, action, outcome="success",
                        trace_id=None, razorpay_entity=None,
                        bounded=None, gated_by=None,
                        explainable="", failure_detail="",
                        extra_payload=None):
        """
        Log a structured audit event matching the universal schema:
        {
            trace_id, agent, action, razorpay_entity,
            bounded {max_amount, currency, expiry},
            gated_by, explainable, outcome, failure_detail
        }
        """
        from intelligence.models import AuditEvent

        trace = trace_id or str(uuid.uuid4())
        payload = {
            "razorpay_entity": razorpay_entity or {},
            "bounded": bounded or {},
            "gated_by": gated_by or "none",
            "explainable": explainable,
            "failure_detail": failure_detail,
        }
        if extra_payload:
            payload.update(extra_payload)

        try:
            event = AuditEvent.objects.create(
                event_id=f"aud_{uuid.uuid4().hex[:12]}",
                trace_id=trace,
                agent=agent,
                action=action,
                details=explainable,
                status=outcome,
                payload=payload,
            )
            logger.info(
                f"[Audit] {agent}.{action} → {outcome} | trace={trace[:12]}..."
            )
            return event
        except Exception as e:
            logger.error(f"[Audit] Failed to log event: {e}")
            return None

    @classmethod
    def log_webhook(cls, event_type, payment_id, order_id, status):
        """Log a Razorpay webhook event."""
        # Use the new structured logging
        cls.log_audit_event(
            agent="razorpay_webhook",
            action=f"webhook_{event_type}",
            outcome=status,
            razorpay_entity={"type": "payment", "id": payment_id},
            explainable=f"Webhook {event_type} for payment {payment_id}",
            extra_payload={"provider_reference": order_id},
        )

        # Also log to legacy ActivityLog for backward compatibility
        try:
            from crm.models import ActivityLog
            ActivityLog.objects.create(
                actor_id=None,
                verb=f"webhook_{event_type}",
                target_type="payment",
                target_id=payment_id,
                metadata={
                    "provider_reference": order_id,
                    "status": status,
                    "event": event_type,
                },
            )
        except Exception as e:
            logger.warning(f"[Audit] Legacy ActivityLog failed: {e}")

    @classmethod
    def log_agent_action(cls, actor_id, verb, target_type, target_id,
                         metadata=None, agent_name=None):
        """Log an agent action (e.g., checkout quote, authorize)."""
        # Structured audit event
        cls.log_audit_event(
            agent=agent_name or "agent",
            action=verb,
            outcome="success",
            explainable=f"Agent action: {verb} on {target_type}/{target_id}",
            extra_payload={"target_type": target_type, "target_id": target_id,
                           **(metadata or {})},
        )

        # Legacy ActivityLog
        try:
            from crm.models import ActivityLog
            ActivityLog.objects.create(
                actor_id=actor_id,
                verb=verb,
                target_type=target_type,
                target_id=target_id,
                metadata=metadata or {},
            )
        except Exception as e:
            logger.warning(f"[Audit] Legacy ActivityLog failed: {e}")

    @classmethod
    def log_upsell_event(cls, agent, action, product_id, customer_id=None,
                         signal=None, payment_link_id=None,
                         revenue_impact=None, outcome="success",
                         trace_id=None):
        """Log an upsell/cross-sell event with full audit trail."""
        return cls.log_audit_event(
            agent=agent,
            action=action,
            outcome=outcome,
            trace_id=trace_id,
            razorpay_entity={
                "type": "payment_link",
                "id": payment_link_id,
            } if payment_link_id else {},
            bounded={
                "max_amount": str(revenue_impact) if revenue_impact else "0",
                "currency": "INR",
            },
            gated_by="user_confirmation",
            explainable=f"Signal: {signal or 'manual'}. Product: {product_id}",
            extra_payload={
                "product_id": product_id,
                "customer_id": customer_id,
                "signal": signal,
                "revenue_impact": str(revenue_impact) if revenue_impact else None,
            },
        )

    @classmethod
    def log_campaign_event(cls, action, campaign_id, outcome="success",
                           budget_limit=None, current_spend=None,
                           trace_id=None, explainable=""):
        """Log a campaign orchestration event."""
        return cls.log_audit_event(
            agent="campaign_agent",
            action=action,
            outcome=outcome,
            trace_id=trace_id,
            bounded={
                "max_amount": str(budget_limit) if budget_limit else "0",
                "currency": "INR",
            },
            gated_by="merchant_approval",
            explainable=explainable,
            extra_payload={
                "campaign_id": campaign_id,
                "current_spend": str(current_spend) if current_spend else "0",
                "budget_limit": str(budget_limit) if budget_limit else "0",
            },
        )

