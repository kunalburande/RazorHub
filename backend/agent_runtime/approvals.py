import logging
from django.utils import timezone
from typing import Dict, Any, Tuple
from .models import (
    Agent,
    AgentExecution,
    AgentExecutionStep,
    AgentApproval,
    ApprovalMode,
    ApprovalStatus,
    RiskLevel,
)
from .policies import PolicyEvaluationResult

logger = logging.getLogger(__name__)


class ApprovalManager:
    """
    Manages human-in-the-loop approvals according to agent configuration and policy evaluation.
    """

    @classmethod
    def requires_approval(
        cls,
        agent: Agent,
        tool_name: str,
        arguments: Dict[str, Any],
        policy_result: PolicyEvaluationResult,
    ) -> Tuple[bool, str]:
        """
        Determines whether a proposed tool execution must pause for human approval.
        Returns: (needs_approval: bool, reason: str)
        """
        mode = agent.approval_mode

        # 1. Blocked mode -> Prohibited completely
        if mode == ApprovalMode.BLOCKED:
            return True, f"Agent '{agent.name}' is in BLOCKED mode. All actions prohibited."

        # 2. Always confirm mode -> Every tool action requires user confirmation
        if mode == ApprovalMode.ALWAYS_CONFIRM:
            return True, f"Agent '{agent.name}' is configured for ALWAYS_CONFIRM. User approval is mandatory for all tool executions."

        # 3. Policy triggered approval requirement
        if policy_result.requires_approval:
            return True, policy_result.reason or "Action flagged by policy guardrail requiring user confirmation."

        # 4. Review Required mode -> Check tool risk level
        if mode == ApprovalMode.REVIEW_REQUIRED:
            from .registry import ToolRegistry
            tool = ToolRegistry.get(tool_name)
            if tool and tool.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                return True, f"Tool '{tool_name}' carries {tool.risk_level} risk level under REVIEW_REQUIRED mode."
            if agent.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
                return True, f"Agent '{agent.name}' operates at {agent.risk_level} risk level under REVIEW_REQUIRED mode."

        # AUTO mode with passing policy
        return False, ""

    @classmethod
    def create_approval_request(
        cls,
        execution: AgentExecution,
        step: AgentExecutionStep,
        tool_name: str,
        arguments: Dict[str, Any],
        reason: str,
    ) -> AgentApproval:
        """Create a pending AgentApproval record and halt execution."""
        approval = AgentApproval.objects.create(
            execution=execution,
            step=step,
            requested_action=f"Execute Tool: {tool_name}",
            action_payload={"tool": tool_name, "arguments": arguments},
            reason=reason,
            status=ApprovalStatus.PENDING,
        )
        logger.info(f"Created AgentApproval [{approval.approval_id}] for execution [{execution.execution_id}]")
        return approval

    @classmethod
    def decide(
        cls,
        approval_id: str,
        decision: str, # "APPROVED" or "REJECTED"
        approver=None,
        notes: str = "",
    ) -> AgentApproval:
        """
        Record user approval decision and return the updated approval record.
        """
        approval = AgentApproval.objects.get(approval_id=approval_id)
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError(f"Approval {approval_id} is already in state '{approval.status}'.")

        decision_upper = decision.upper()
        if decision_upper not in [ApprovalStatus.APPROVED, ApprovalStatus.REJECTED]:
            raise ValueError(f"Invalid decision '{decision}'. Expected APPROVED or REJECTED.")

        approval.status = decision_upper
        approval.approver = approver
        approval.decision_notes = notes
        approval.decided_at = timezone.now()
        approval.save(update_fields=["status", "approver", "decision_notes", "decided_at"])

        return approval
