import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from .models import Agent, AgentPolicy, PolicyType, ViolationAction

logger = logging.getLogger(__name__)


@dataclass
class PolicyEvaluationResult:
    allowed: bool
    requires_approval: bool
    violation_action: Optional[str] = None
    reason: str = ""
    violating_policy: Optional[str] = None


class PolicyEngine:
    """
    Evaluates policy guardrails against proposed tool actions before execution.
    """

    @classmethod
    def evaluate(
        cls,
        agent: Agent,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> PolicyEvaluationResult:
        context = context or {}

        # 1. Basic Tool Permission Check:
        # If the agent has specific tools configured in its M2M relation, ensure tool_name is one of them.
        if agent.tools.exists():
            if not agent.tools.filter(name=tool_name, is_enabled=True).exists():
                return PolicyEvaluationResult(
                    allowed=False,
                    requires_approval=False,
                    violation_action=ViolationAction.BLOCK,
                    reason=f"Tool '{tool_name}' is not permitted for Agent '{agent.name}'.",
                    violating_policy="TOOL_PERMISSION_RESTRICTION",
                )

        # 2. Evaluate all attached policies
        policies = agent.policies.filter(is_active=True)
        for policy in policies:
            res = cls._evaluate_single_policy(policy, tool_name, arguments, context)
            if not res.allowed or res.requires_approval:
                return res

        # All policies passed
        return PolicyEvaluationResult(
            allowed=True,
            requires_approval=False,
            reason="All policy guardrails satisfied.",
        )

    @classmethod
    def _evaluate_single_policy(
        cls,
        policy: AgentPolicy,
        tool_name: str,
        arguments: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PolicyEvaluationResult:
        rules = policy.rules or {}

        # A. SPENDING_LIMIT policy
        if policy.policy_type == PolicyType.SPENDING_LIMIT:
            amount = arguments.get("amount")
            if amount is not None:
                try:
                    amount_val = float(amount)
                except (ValueError, TypeError):
                    amount_val = 0.0

                max_amount = rules.get("max_amount")
                if max_amount is not None and amount_val > float(max_amount):
                    reason = f"Transaction amount ₹{amount_val:,.2f} exceeds policy limit ₹{float(max_amount):,.2f} ({policy.name})."
                    return cls._create_violation_result(policy, reason)

        # B. TOOL_ALLOWLIST policy
        elif policy.policy_type == PolicyType.TOOL_ALLOWLIST:
            allowed_tools = rules.get("allowed_tools", [])
            if allowed_tools and tool_name not in allowed_tools:
                reason = f"Tool '{tool_name}' is not in the allowed tools list ({policy.name})."
                return cls._create_violation_result(policy, reason)

        # C. APPROVAL_RULE policy
        elif policy.policy_type == PolicyType.APPROVAL_RULE:
            threshold = rules.get("approval_threshold")
            amount = arguments.get("amount")
            if threshold is not None and amount is not None:
                if float(amount) >= float(threshold):
                    reason = f"Amount ₹{float(amount):,.2f} meets approval threshold ₹{float(threshold):,.2f} ({policy.name})."
                    return PolicyEvaluationResult(
                        allowed=True,
                        requires_approval=True,
                        violation_action=ViolationAction.REQUIRE_APPROVAL,
                        reason=reason,
                        violating_policy=policy.name,
                    )

            sensitive_tools = rules.get("sensitive_tools", [])
            if tool_name in sensitive_tools:
                reason = f"Tool '{tool_name}' is classified as sensitive requiring approval ({policy.name})."
                return PolicyEvaluationResult(
                    allowed=True,
                    requires_approval=True,
                    violation_action=ViolationAction.REQUIRE_APPROVAL,
                    reason=reason,
                    violating_policy=policy.name,
                )

        return PolicyEvaluationResult(allowed=True, requires_approval=False)

    @classmethod
    def _create_violation_result(cls, policy: AgentPolicy, reason: str) -> PolicyEvaluationResult:
        action = policy.violation_action
        if action == ViolationAction.BLOCK:
            return PolicyEvaluationResult(
                allowed=False,
                requires_approval=False,
                violation_action=action,
                reason=reason,
                violating_policy=policy.name,
            )
        elif action == ViolationAction.REQUIRE_APPROVAL:
            return PolicyEvaluationResult(
                allowed=True,
                requires_approval=True,
                violation_action=action,
                reason=reason,
                violating_policy=policy.name,
            )
        else: # WARN_AND_LOG
            logger.warning(f"Policy warning: {reason}")
            return PolicyEvaluationResult(
                allowed=True,
                requires_approval=False,
                violation_action=action,
                reason=reason,
                violating_policy=policy.name,
            )
