import re
import logging
from decimal import Decimal
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from django.utils import timezone
from datetime import timedelta

from .models import (
    Agent,
    GovernanceDecision,
    AgentGovernancePolicy,
    GovernanceDecisionRecord,
    AgentApproval,
    ApprovalStatus,
    AgentAuditLog,
    AuditEventType,
    AuditSeverity,
    FinancialRiskRecord,
)
from .tools.registry import ToolRegistry
from .tools.base import ToolExecutionContext, ToolResult
from .risk import FinancialRiskEngine


logger = logging.getLogger(__name__)


@dataclass
class GovernanceEvaluationResult:
    decision: str  # ALLOW, ALLOW_WITH_CONFIRMATION, DENY, ESCALATE
    allowed: bool
    requires_human_approval: bool = False
    requires_double_confirmation: bool = False
    reason: str = ""
    policy_triggered: str = ""
    risk_score: float = 0.0
    approval_id: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)


# ── 1. INTENT VALIDATOR ───────────────────────────────────────────────────────
class IntentValidator:
    """
    Validates user & agent prompts against adversarial inputs, prompt injection,
    negative values, arithmetic bypasses, and security exploits.
    """
    MALICIOUS_PATTERNS = [
        r"ignore\s+(?:all\s+)?(?:previous|prior)\s+instructions",
        r"bypass\s+(?:all\s+)?(?:security|limits|guardrails|policies)",
        r"override\s+(?:spending|transaction)\s+limits",
        r"jailbreak",
        r"disable\s+(?:firewall|governance|policy)",
        r"transfer\s+all\s+(?:funds|money|balance)",
        r"(?:drop|delete|truncate)\s+table",
    ]

    @classmethod
    def validate(cls, raw_prompt: str, arguments: Dict[str, Any]) -> Tuple[bool, str, str]:
        """
        Returns: (is_valid: bool, code: str, reason: str)
        """
        # A. Prompt pattern inspection
        if raw_prompt:
            prompt_lower = raw_prompt.lower()
            for pattern in cls.MALICIOUS_PATTERNS:
                if re.search(pattern, prompt_lower):
                    return (
                        False,
                        "MALICIOUS_PROMPT_DETECTED",
                        f"Malicious adversarial pattern detected in prompt: '{pattern}'.",
                    )

        # B. Arithmetic / payload sanity
        amount = arguments.get("amount")
        if amount is not None:
            try:
                amt_float = float(amount)
                import math
                if math.isnan(amt_float) or math.isinf(amt_float):
                    return False, "INVALID_NUMERIC_VALUE", "Amount contains non-finite numeric representation."
                if amt_float <= 0:
                    return False, "NEGATIVE_AMOUNT_DISALLOWED", "Transaction amount must be strictly greater than zero."
            except (ValueError, TypeError):
                return False, "INVALID_AMOUNT_TYPE", "Amount must be a valid numeric quantity."

        return True, "INTENT_VALID", "Intent verified and secure."


# ── 2. PERMISSION VALIDATOR ───────────────────────────────────────────────────
class PermissionValidator:
    """
    Enforces category restrictions, merchant allow/blocklists, operating hours,
    and payment method restrictions.
    """

    @classmethod
    def validate(
        cls,
        policy: AgentGovernancePolicy,
        tool_name: str,
        category: str,
        merchant: str,
        payment_method: str,
    ) -> Tuple[bool, str, str]:
        # A. Category checks
        cat_lower = (category or "").lower().strip()
        blocked_cats = [c.lower().strip() for c in (policy.blocked_categories or [])]
        if cat_lower in blocked_cats:
            return (
                False,
                "BLOCKED_CATEGORY",
                f"Category '{category}' is blocked by governance policy '{policy.name}'.",
            )

        allowed_cats = [c.lower().strip() for c in (policy.allowed_categories or [])]
        if allowed_cats and cat_lower not in allowed_cats:
            return (
                False,
                "CATEGORY_NOT_ALLOWED",
                f"Category '{category}' is not in allowed categories list for '{policy.name}'.",
            )

        # B. Merchant checks
        merch_clean = (merchant or "").lower().strip()
        blocked_merchs = [m.lower().strip() for m in (policy.blocked_merchants or [])]
        if merch_clean and merch_clean in blocked_merchs:
            return (
                False,
                "BLOCKED_MERCHANT",
                f"Merchant '{merchant}' is blocked by governance policy '{policy.name}'.",
            )

        allowed_merchs = [m.lower().strip() for m in (policy.allowed_merchants or [])]
        if allowed_merchs and merch_clean and merch_clean not in allowed_merchs and "*" not in allowed_merchs:
            return (
                False,
                "UNAUTHORIZED_MERCHANT",
                f"Merchant '{merchant}' is not in allowed merchants list.",
            )

        # C. Payment method checks
        method_clean = (payment_method or "").lower().strip()
        allowed_methods = [m.lower().strip() for m in (policy.allowed_payment_methods or [])]
        if allowed_methods and method_clean and method_clean not in allowed_methods:
            return (
                False,
                "PAYMENT_METHOD_DISALLOWED",
                f"Payment method '{payment_method}' is not permitted by policy.",
            )

        # D. Operating hours check
        hours = policy.allowed_hours or {}
        start_hr = hours.get("start")
        end_hr = hours.get("end")
        if start_hr and end_hr:
            now_time = timezone.localtime().strftime("%H:%M")
            if not (start_hr <= now_time <= end_hr):
                return (
                    False,
                    "OFF_HOURS_RESTRICTION",
                    f"Transactions restricted outside operating hours ({start_hr} - {end_hr}). Current time: {now_time}.",
                )

        return True, "PERMISSIONS_VALID", "All permission constraints satisfied."


# ── 3. SPENDING POLICY VALIDATOR ──────────────────────────────────────────────
class SpendingPolicyValidator:
    """
    Enforces maximum single transaction ceilings.
    """

    @classmethod
    def validate(cls, policy: AgentGovernancePolicy, amount: Optional[float]) -> Tuple[bool, str, str]:
        if amount is None or amount <= 0:
            return True, "NO_AMOUNT", "No amount constraint."

        amt_decimal = Decimal(str(amount))
        if amt_decimal > policy.max_transaction_amount:
            return (
                False,
                "MAX_TRANSACTION_EXCEEDED",
                f"Amount ₹{amt_decimal:,.2f} exceeds maximum transaction limit ₹{policy.max_transaction_amount:,.2f}.",
            )

        return True, "WITHIN_LIMIT", "Transaction amount is within spending limits."


# ── 4. BUDGET VALIDATOR ───────────────────────────────────────────────────────
class BudgetValidator:
    """
    Calculates aggregated velocities over daily, weekly, and monthly rolling windows.
    """

    @classmethod
    def validate(
        cls,
        policy: AgentGovernancePolicy,
        agent: Optional[Agent],
        amount: Optional[float],
    ) -> Tuple[bool, str, str]:
        if amount is None or amount <= 0 or not agent:
            return True, "NO_BUDGET_RESTRICTION", "No budget restriction."

        amt_decimal = Decimal(str(amount))
        now = timezone.now()

        # Aggregate approved decisions and executions in last 24h
        day_ago = now - timedelta(days=1)
        records_today = GovernanceDecisionRecord.objects.filter(
            agent=agent,
            decision__in=[GovernanceDecision.ALLOW, GovernanceDecision.ALLOW_WITH_CONFIRMATION],
            created_at__gte=day_ago,
        )
        total_today = sum(r.amount for r in records_today if r.amount) or Decimal("0.00")

        if (total_today + amt_decimal) > policy.daily_spend_limit:
            return (
                False,
                "DAILY_LIMIT_EXCEEDED",
                f"Daily spend limit of ₹{policy.daily_spend_limit:,.2f} exceeded. (Spent: ₹{total_today:,.2f}, Requested: ₹{amt_decimal:,.2f}).",
            )

        # Weekly window (7 days)
        week_ago = now - timedelta(days=7)
        records_week = GovernanceDecisionRecord.objects.filter(
            agent=agent,
            decision__in=[GovernanceDecision.ALLOW, GovernanceDecision.ALLOW_WITH_CONFIRMATION],
            created_at__gte=week_ago,
        )
        total_week = sum(r.amount for r in records_week if r.amount) or Decimal("0.00")
        if (total_week + amt_decimal) > policy.weekly_spend_limit:
            return (
                False,
                "WEEKLY_LIMIT_EXCEEDED",
                f"Weekly spend limit of ₹{policy.weekly_spend_limit:,.2f} exceeded. (Spent: ₹{total_week:,.2f}, Requested: ₹{amt_decimal:,.2f}).",
            )

        # Monthly window (30 days)
        month_ago = now - timedelta(days=30)
        records_month = GovernanceDecisionRecord.objects.filter(
            agent=agent,
            decision__in=[GovernanceDecision.ALLOW, GovernanceDecision.ALLOW_WITH_CONFIRMATION],
            created_at__gte=month_ago,
        )
        total_month = sum(r.amount for r in records_month if r.amount) or Decimal("0.00")
        if (total_month + amt_decimal) > policy.monthly_spend_limit:
            return (
                False,
                "MONTHLY_LIMIT_EXCEEDED",
                f"Monthly spend limit of ₹{policy.monthly_spend_limit:,.2f} exceeded. (Spent: ₹{total_month:,.2f}, Requested: ₹{amt_decimal:,.2f}).",
            )

        return True, "BUDGET_OK", "Budget constraints satisfied."



# ── 5. RISK ENGINE ────────────────────────────────────────────────────────────
class RiskEngine:
    """
    Multi-factor risk scoring engine (0.00 to 1.00) powered by FinancialRiskEngine.
    """

    @classmethod
    def calculate_score(
        cls,
        policy: AgentGovernancePolicy,
        amount: Optional[float],
        merchant: str,
        is_mutation: bool,
        extra_inputs: Optional[Dict[str, Any]] = None,
    ) -> float:
        if not is_mutation:
            return 0.05

        customer_avg = float(policy.max_transaction_amount) * 0.25 if policy.max_transaction_amount else 5000.0
        inputs = {
            "transaction_amount": amount,
            "customer_avg_amount": customer_avg,
            "merchant_history": {
                "merchant_name": merchant,
                "is_new": bool(merchant and merchant.lower() not in [m.lower() for m in (policy.allowed_merchants or [])]),
            },
        }
        if extra_inputs:
            inputs.update(extra_inputs)

        res = FinancialRiskEngine.evaluate(inputs)
        return round(res["riskScore"] / 100.0, 2)

    @classmethod
    def evaluate_full(cls, inputs: Dict[str, Any], include_llm_explanation: bool = False) -> Dict[str, Any]:
        return FinancialRiskEngine.evaluate(inputs, include_llm_explanation=include_llm_explanation)



# ── 6. TRANSACTION GOVERNANCE FIREWALL ORCHESTRATOR ───────────────────────────
class TransactionGovernanceFirewall:
    """
    The deterministic Agent Firewall layer sitting directly between
    the agent and every financial mutation action.
    """

    @classmethod
    def evaluate(
        cls,
        agent: Agent,
        tool_name: str,
        arguments: Dict[str, Any],
        raw_prompt: str = "",
        user: Any = None,
        context: Optional[ToolExecutionContext] = None,
    ) -> GovernanceEvaluationResult:
        """
        Executes the full 10-stage governance pipeline and returns structured decisions:
        ALLOW | ALLOW_WITH_CONFIRMATION | DENY | ESCALATE
        """
        # Resolve policy for agent (or agent's custom governance policy or fallback default)
        policy = getattr(agent, "governance_policy", None)
        if not policy:
            policy, _ = AgentGovernancePolicy.objects.get_or_create(
                agent=agent,
                defaults={"name": f"{agent.name} Governance Policy"},
            )

        amount = arguments.get("amount")
        amt_float = float(amount) if amount is not None else None
        merchant = arguments.get("recipient_id") or arguments.get("recipient_account") or arguments.get("customer_email") or ""
        category = arguments.get("category") or "PAYMENTS"
        payment_method = arguments.get("method") or arguments.get("payment_method") or "upi"

        tool = ToolRegistry.get(tool_name)
        is_mutation = getattr(tool, "is_mutation", False) or (tool_name in [
            "transfer_funds",
            "createPaymentIntent",
            "createPaymentLink",
            "createRefund",
            "createPayout",
            "sendNotification",
            "createAlert",
        ])

        # ── STAGE 1: INTENT VALIDATOR ──
        valid_intent, intent_code, intent_msg = IntentValidator.validate(raw_prompt, arguments)
        if not valid_intent:
            return cls._record_and_return(
                decision=GovernanceDecision.DENY,
                reason=intent_msg,
                policy_triggered=intent_code,
                agent=agent,
                user=user,
                action=tool_name,
                amount=amt_float,
                merchant=merchant,
                raw_prompt=raw_prompt,
                risk_score=1.0,
            )

        # ── STAGE 2: PERMISSION VALIDATOR ──
        # Check tool permission
        if agent.tools.exists() and not agent.tools.filter(name=tool_name).exists():
            return cls._record_and_return(
                decision=GovernanceDecision.DENY,
                reason=f"Tool '{tool_name}' is not permitted for agent '{agent.name}'.",
                policy_triggered="INVALID_AGENT_PERMISSIONS",
                agent=agent,
                user=user,
                action=tool_name,
                amount=amt_float,
                merchant=merchant,
                raw_prompt=raw_prompt,
                risk_score=0.9,
            )

        valid_perm, perm_code, perm_msg = PermissionValidator.validate(
            policy=policy,
            tool_name=tool_name,
            category=category,
            merchant=merchant,
            payment_method=payment_method,
        )
        if not valid_perm:
            return cls._record_and_return(
                decision=GovernanceDecision.DENY,
                reason=perm_msg,
                policy_triggered=perm_code,
                agent=agent,
                user=user,
                action=tool_name,
                amount=amt_float,
                merchant=merchant,
                raw_prompt=raw_prompt,
                risk_score=0.85,
            )

        # If not a mutation tool (e.g. read-only lookup), allow immediately
        if not is_mutation:
            return GovernanceEvaluationResult(
                decision=GovernanceDecision.ALLOW,
                allowed=True,
                reason="Read-only operation permitted.",
                risk_score=0.05,
            )

        # ── STAGE 3: SPENDING POLICY ──
        valid_spend, spend_code, spend_msg = SpendingPolicyValidator.validate(policy, amt_float)
        if not valid_spend:
            return cls._record_and_return(
                decision=GovernanceDecision.DENY,
                reason=spend_msg,
                policy_triggered=spend_code,
                agent=agent,
                user=user,
                action=tool_name,
                amount=amt_float,
                merchant=merchant,
                raw_prompt=raw_prompt,
                risk_score=0.8,
            )

        # ── STAGE 4: BUDGET VALIDATOR ──
        valid_budget, budget_code, budget_msg = BudgetValidator.validate(policy, agent, amt_float)
        if not valid_budget:
            # Escalated decision for budget overrun
            return cls._record_and_return(
                decision=GovernanceDecision.ESCALATE,
                reason=budget_msg,
                policy_triggered=budget_code,
                agent=agent,
                user=user,
                action=tool_name,
                amount=amt_float,
                merchant=merchant,
                raw_prompt=raw_prompt,
                risk_score=0.85,
            )

        # ── STAGE 5: EXPLAINABLE FINANCIAL RISK ENGINE ──
        customer_avg = float(policy.max_transaction_amount) * 0.25 if policy.max_transaction_amount else 5000.0
        risk_inputs = {
            "transaction_amount": amt_float,
            "customer_avg_amount": arguments.get("customer_avg_amount", customer_avg),
            "customer_age_days": arguments.get("customer_age_days", arguments.get("customer_age", 365)),
            "merchant_history": arguments.get("merchant_history", {
                "merchant_name": merchant,
                "is_new": bool(merchant and merchant.lower() not in [m.lower() for m in (policy.allowed_merchants or [])]),
            }),
            "payment_history": arguments.get("payment_history", {}),
            "refund_history": arguments.get("refund_history", {}),
            "chargeback_history": arguments.get("chargeback_history", {}),
            "velocity": arguments.get("velocity", {}),
            "category": category,
            "device": arguments.get("device", {}),
            "location": arguments.get("location", {}),
            "failed_attempts": arguments.get("failed_attempts", 0),
        }

        risk_evaluation = FinancialRiskEngine.evaluate(risk_inputs)
        raw_risk_score = risk_evaluation["riskScore"]
        risk_level = risk_evaluation["riskLevel"]
        risk_reasons = risk_evaluation["reasons"]
        critical_rule_triggered = risk_evaluation["critical_rule_triggered"]

        risk_score = round(raw_risk_score / 100.0, 2)

        # Deterministic Critical Firewall Halt:
        if critical_rule_triggered or risk_level == "CRITICAL":
            return cls._record_and_return(
                decision=GovernanceDecision.DENY,
                reason=f"Blocked by Explainable Risk Engine (Score: {raw_risk_score}/100, CRITICAL). Reasons: {'; '.join(risk_reasons)}",
                policy_triggered="CRITICAL_FINANCIAL_RISK_RULE",
                agent=agent,
                user=user,
                action=tool_name,
                amount=amt_float,
                merchant=merchant,
                raw_prompt=raw_prompt,
                risk_score=risk_score,
                details={"risk_evaluation": risk_evaluation},
            )

        # ── STAGE 6: APPROVAL ENGINE ──
        requires_approval = False
        requires_double_confirmation = policy.require_double_confirmation or (risk_score >= 0.8) or (risk_level == "HIGH")
        approval_reason = ""

        if policy.require_human_approval:
            requires_approval = True
            approval_reason = f"Policy '{policy.name}' mandates human approval for all mutations."
        elif amt_float and Decimal(str(amt_float)) >= Decimal(str(policy.require_approval_above)):
            requires_approval = True
            approval_reason = f"Amount ₹{amt_float:,.2f} exceeds automatic approval limit ₹{policy.require_approval_above:,.2f}."
        elif risk_level == "HIGH" or risk_score >= 0.60:
            requires_approval = True
            approval_reason = f"High risk score ({raw_risk_score}/100 - {risk_level}) requires explicit human confirmation: {'; '.join(risk_reasons[:2]) if risk_reasons else 'Elevated multi-factor risk'}"
        elif getattr(tool, "requires_approval", False):
            requires_approval = True
            approval_reason = f"Tool '{tool_name}' carries mandatory approval requirement."

        # If approval required and not pre-approved:
        is_pre_approved = False
        if context:
            if isinstance(context, dict):
                is_pre_approved = context.get("is_pre_approved", False)
            else:
                is_pre_approved = getattr(context, "is_pre_approved", False)

        if requires_approval and not is_pre_approved:
            execution_obj = context.get("execution") if isinstance(context, dict) else getattr(context, "execution", None)
            approval_record = AgentApproval.objects.create(
                agent=agent,
                execution=execution_obj,
                requested_action=f"Execute Tool: {tool_name}",
                action_payload={"tool": tool_name, "arguments": arguments},
                reason=approval_reason,
                status=ApprovalStatus.PENDING,
                amount=Decimal(str(amt_float)) if amt_float else None,
                merchant=merchant,
                risk_score=risk_score,
                policy_triggered="REQUIRE_APPROVAL_ABOVE",
                requires_double_confirmation=requires_double_confirmation,
            )

            res = cls._record_and_return(
                decision=GovernanceDecision.ALLOW_WITH_CONFIRMATION,
                reason=approval_reason,
                policy_triggered="APPROVAL_REQUIRED",
                agent=agent,
                user=user,
                action=tool_name,
                amount=amt_float,
                merchant=merchant,
                raw_prompt=raw_prompt,
                risk_score=risk_score,
                approval_id=str(approval_record.approval_id),
                requires_double_confirmation=requires_double_confirmation,
                details={"risk_evaluation": risk_evaluation},
            )
            return res

        # ── STAGE 7: DECISION ALLOW ──
        try:
            FinancialRiskRecord.objects.create(
                user=user if getattr(user, "is_authenticated", False) else None,
                agent=agent,
                transaction_amount=Decimal(str(amt_float)) if amt_float is not None else None,
                risk_score=raw_risk_score,
                risk_level=risk_level,
                reasons=risk_reasons,
                critical_rule_triggered=critical_rule_triggered,
                rule_breakdown=risk_evaluation.get("rule_breakdown", []),
                inputs_snapshot=risk_evaluation.get("inputs_summary", {}),
                explanation=risk_evaluation.get("explanation", ""),
            )
        except Exception:
            pass

        return GovernanceEvaluationResult(
            decision=GovernanceDecision.ALLOW,
            allowed=True,
            reason="All governance validators passed.",
            risk_score=risk_score,
            requires_double_confirmation=requires_double_confirmation,
            details={"risk_evaluation": risk_evaluation},
        )

    @classmethod
    def _record_and_return(
        cls,
        decision: str,
        reason: str,
        policy_triggered: str,
        agent: Optional[Agent],
        user: Any,
        action: str,
        amount: Optional[float],
        merchant: str,
        raw_prompt: str,
        risk_score: float,
        approval_id: Optional[str] = None,
        requires_double_confirmation: bool = False,
        details: Optional[Dict[str, Any]] = None,
    ) -> GovernanceEvaluationResult:
        # Every DENY, ESCALATE, and ALLOW_WITH_CONFIRMATION must be permanently recorded
        rec_details = {"approval_id": approval_id, "double_confirmation": requires_double_confirmation}
        if details:
            rec_details.update(details)

        try:
            GovernanceDecisionRecord.objects.create(
                agent=agent,
                user=user if getattr(user, "is_authenticated", False) else None,
                decision=decision,
                action=action,
                amount=Decimal(str(amount)) if amount is not None else None,
                merchant=merchant,
                reason=reason,
                risk_score=risk_score,
                policy_triggered=policy_triggered,
                raw_prompt=raw_prompt,
                details=rec_details,
            )
        except Exception as e:
            logger.error(f"Failed to record governance decision: {e}")

        # Also create FinancialRiskRecord if risk_evaluation provided
        if details and "risk_evaluation" in details:
            risk_eval = details["risk_evaluation"]
            try:
                FinancialRiskRecord.objects.create(
                    user=user if getattr(user, "is_authenticated", False) else None,
                    agent=agent,
                    transaction_amount=Decimal(str(amount)) if amount is not None else None,
                    risk_score=risk_eval.get("riskScore", int(risk_score * 100)),
                    risk_level=risk_eval.get("riskLevel", "LOW"),
                    reasons=risk_eval.get("reasons", []),
                    critical_rule_triggered=risk_eval.get("critical_rule_triggered", False),
                    rule_breakdown=risk_eval.get("rule_breakdown", []),
                    inputs_snapshot=risk_eval.get("inputs_summary", {}),
                    explanation=risk_eval.get("explanation", ""),
                )
            except Exception as e:
                logger.warning(f"Failed to record FinancialRiskRecord: {e}")

        # Also emit audit log

        severity = AuditSeverity.ERROR if decision == GovernanceDecision.DENY else AuditSeverity.WARNING
        try:
            AgentAuditLog.objects.create(
                agent=agent,
                event_type=AuditEventType.POLICY_CHECKED,
                severity=severity,
                actor_type="FIREWALL",
                actor_id="governance_firewall",
                details={
                    "decision": decision,
                    "reason": reason,
                    "policy_triggered": policy_triggered,
                    "amount": amount,
                    "merchant": merchant,
                },
            )
        except Exception:
            pass

        return GovernanceEvaluationResult(
            decision=decision,
            allowed=(decision == GovernanceDecision.ALLOW),
            requires_human_approval=(decision == GovernanceDecision.ALLOW_WITH_CONFIRMATION),
            requires_double_confirmation=requires_double_confirmation,
            reason=reason,
            policy_triggered=policy_triggered,
            risk_score=risk_score,
            approval_id=approval_id,
        )
