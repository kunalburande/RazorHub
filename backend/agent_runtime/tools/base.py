import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from django.utils import timezone
from datetime import timedelta

from .categories import ToolCategory
from ..models import RiskLevel, AgentAuditLog, AuditEventType, AuditSeverity

logger = logging.getLogger(__name__)


@dataclass
class ToolExecutionContext:
    """Contextual metadata passed into every tool execution."""
    agent: Optional[Any] = None
    user: Optional[Any] = None
    session_id: str = ""
    is_pre_approved: bool = False
    approval_id: Optional[str] = None
    custom_limits: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolResult:
    """Standardized output envelope for all tool executions."""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    approval_required: bool = False
    approval_reason: str = ""
    is_idempotent_replay: bool = False
    risk_score: float = 0.0


class BaseTool(ABC):
    """
    Typed, composable Tool specification adhering to the agentic MCP standard.
    Never allows direct arbitrary function execution.
    """
    id: str
    name: str
    description: str
    category: ToolCategory
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    risk_level: str = RiskLevel.LOW
    requires_approval: bool = False
    is_mutation: bool = False
    max_amount_limit: Optional[float] = None
    required_permissions: List[str] = []

    # Property camelCase aliases for interoperability
    @property
    def inputSchema(self) -> Dict[str, Any]:
        return self.input_schema

    @property
    def outputSchema(self) -> Dict[str, Any]:
        return self.output_schema

    @property
    def riskLevel(self) -> str:
        return self.risk_level

    @property
    def requiresApproval(self) -> bool:
        return self.requires_approval

    def validateInput(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.validate_input(input_data)

    def validateOutput(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        return self.validate_output(output_data)

    def validate_input(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates input payload against input_schema.
        Raises ValueError if validation fails.
        """
        schema = self.input_schema
        required = schema.get("required", [])
        for req in required:
            if req not in input_data or input_data[req] is None:
                raise ValueError(f"Missing required parameter '{req}' for tool '{self.name}'.")

        properties = schema.get("properties", {})
        for key, val in input_data.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "number" and not isinstance(val, (int, float)):
                    raise ValueError(f"Parameter '{key}' must be numeric in tool '{self.name}'.")
                elif expected_type == "integer" and not isinstance(val, int):
                    raise ValueError(f"Parameter '{key}' must be an integer in tool '{self.name}'.")
                elif expected_type == "string" and not isinstance(val, str):
                    raise ValueError(f"Parameter '{key}' must be a string in tool '{self.name}'.")
                elif expected_type == "boolean" and not isinstance(val, bool):
                    raise ValueError(f"Parameter '{key}' must be boolean in tool '{self.name}'.")
                elif expected_type == "array" and not isinstance(val, list):
                    raise ValueError(f"Parameter '{key}' must be a list in tool '{self.name}'.")
                elif expected_type == "object" and not isinstance(val, dict):
                    raise ValueError(f"Parameter '{key}' must be an object in tool '{self.name}'.")

        return input_data

    def validate_output(self, output_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates output payload structure against output_schema.
        """
        if not isinstance(output_data, dict):
            raise ValueError(f"Output of tool '{self.name}' must be a dictionary.")
        return output_data

    @abstractmethod
    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        """Core execution logic. Subclasses implement specific domain actions."""
        pass

    def run_with_guardrails(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> ToolResult:
        """
        Executes the tool with full financial guardrail enforcement:
        1. Input validation
        2. Permission check
        3. Amount limit check
        4. Idempotency key check
        5. Risk evaluation
        6. Approval check
        7. Audit logging
        8. Execution & Output validation
        """
        # 1. Input Validation
        try:
            validated_input = self.validate_input(input_data)
        except ValueError as e:
            return ToolResult(success=False, error=str(e))

        # Financial Mutation Guardrail Pipeline
        if self.is_mutation:
            # 2. Permission Check
            perm_err = self._check_permissions(context)
            if perm_err:
                self._log_audit(
                    event_type=AuditEventType.EXECUTION_FAILED,
                    severity=AuditSeverity.ERROR,
                    context=context,
                    details={"tool": self.name, "reason": perm_err},
                )
                return ToolResult(success=False, error=perm_err)

            # 3. Amount Limit Check
            amt_err = self._check_amount_limit(validated_input, context)
            if amt_err:
                self._log_audit(
                    event_type=AuditEventType.EXECUTION_FAILED,
                    severity=AuditSeverity.ERROR,
                    context=context,
                    details={"tool": self.name, "reason": amt_err},
                )
                return ToolResult(success=False, error=amt_err)

            # 4. Idempotency Key Check
            idempotency_key = validated_input.get("idempotency_key")
            if idempotency_key:
                cached_res = self._check_idempotency(idempotency_key, validated_input)
                if cached_res is not None:
                    logger.info(f"Idempotency hit for key '{idempotency_key}'. Returning cached response.")
                    return ToolResult(
                        success=True,
                        result=cached_res,
                        is_idempotent_replay=True,
                    )

            # 5. Risk Evaluation
            risk_score = self._evaluate_risk(validated_input, context)

            # 6. Approval Requirement Check
            if not context.is_pre_approved:
                needs_appr, appr_reason = self._check_approval_requirement(validated_input, context, risk_score)
                if needs_appr:
                    self._log_audit(
                        event_type=AuditEventType.APPROVAL_REQUIRED,
                        severity=AuditSeverity.WARNING,
                        context=context,
                        details={"tool": self.name, "reason": appr_reason, "risk_score": risk_score},
                    )
                    return ToolResult(
                        success=False,
                        approval_required=True,
                        approval_reason=appr_reason,
                        risk_score=risk_score,
                    )

        # 7. Execute Core Tool Logic
        try:
            raw_output = self.execute(validated_input, context)
            validated_output = self.validate_output(raw_output)

            # Save Idempotency Record if key present
            idempotency_key = validated_input.get("idempotency_key")
            if idempotency_key and self.is_mutation:
                self._save_idempotency(idempotency_key, validated_input, validated_output)

            # 8. Audit Log Success
            if self.is_mutation:
                self._log_audit(
                    event_type=AuditEventType.TOOL_EXECUTED,
                    severity=AuditSeverity.INFO,
                    context=context,
                    details={"tool": self.name, "output": validated_output},
                )

            return ToolResult(success=True, result=validated_output)
        except Exception as e:
            logger.error(f"Error executing tool '{self.name}': {e}", exc_info=True)
            self._log_audit(
                event_type=AuditEventType.EXECUTION_FAILED,
                severity=AuditSeverity.ERROR,
                context=context,
                details={"tool": self.name, "error": str(e)},
            )
            return ToolResult(success=False, error=str(e))

    def to_mcp_tool(self) -> Dict[str, Any]:
        """
        Converts this tool definition into official Model Context Protocol (MCP) JSON schema.
        """
        return {
            "name": self.name,
            "description": self.description,
            "category": str(self.category),
            "riskLevel": self.risk_level,
            "requiresApproval": self.requires_approval,
            "inputSchema": self.input_schema,
            "outputSchema": self.output_schema,
        }

    # ── PRIVATE GUARDRAIL CHECKS ──────────────────────────────────────────────
    def _check_permissions(self, context: ToolExecutionContext) -> Optional[str]:
        if not self.required_permissions:
            return None
        user = context.user
        if not user or not getattr(user, "is_authenticated", False):
            return f"Action '{self.name}' requires authentication with permissions: {self.required_permissions}"

        role = getattr(user, "effective_role", getattr(user, "role", ""))
        if role != "admin" and not any(perm in [role, "all"] for perm in self.required_permissions):
            return f"User role '{role}' is not authorized to execute '{self.name}'."
        return None

    def _check_amount_limit(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Optional[str]:
        amount = input_data.get("amount")
        if amount is None:
            return None

        try:
            amt_val = float(amount)
        except (ValueError, TypeError):
            return "Invalid amount value."

        # Check tool's intrinsic ceiling
        if self.max_amount_limit is not None and amt_val > self.max_amount_limit:
            return f"Amount ₹{amt_val:,.2f} exceeds tool hard ceiling of ₹{self.max_amount_limit:,.2f}."

        # Check agent/context limits
        custom_max = context.custom_limits.get("max_amount")
        if custom_max is not None and amt_val > float(custom_max):
            return f"Amount ₹{amt_val:,.2f} exceeds agent limit of ₹{float(custom_max):,.2f}."

        return None

    def _check_idempotency(self, key: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        from orders.models import IdempotencyRecord
        try:
            record = IdempotencyRecord.objects.get(key=key)
            if record.expires_at and record.expires_at < timezone.now():
                record.delete()
                return None
            return record.response_body
        except IdempotencyRecord.DoesNotExist:
            return None
        except Exception:
            return None

    def _save_idempotency(self, key: str, input_data: Dict[str, Any], output_data: Dict[str, Any]):
        from orders.models import IdempotencyRecord
        req_hash = hashlib.sha256(json.dumps(input_data, sort_keys=True).encode()).hexdigest()
        expires = timezone.now() + timedelta(hours=24)
        try:
            IdempotencyRecord.objects.update_or_create(
                key=key,
                defaults={
                    "request_hash": req_hash,
                    "response_status": 200,
                    "response_body": output_data,
                    "expires_at": expires,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to record idempotency key: {e}")

    def _evaluate_risk(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> float:
        score = 0.1
        if self.risk_level == RiskLevel.MEDIUM:
            score = 0.4
        elif self.risk_level == RiskLevel.HIGH:
            score = 0.75
        elif self.risk_level == RiskLevel.CRITICAL:
            score = 0.95

        amount = input_data.get("amount")
        if amount and float(amount) > 10000:
            score = min(1.0, score + 0.2)
        return round(score, 2)

    def _check_approval_requirement(self, input_data: Dict[str, Any], context: ToolExecutionContext, risk_score: float) -> (bool, str):
        if self.requires_approval:
            return True, f"Tool '{self.name}' is explicitly configured to require approval."
        if risk_score >= 0.7:
            return True, f"High risk score ({risk_score}) requires explicit confirmation for '{self.name}'."

        amount = input_data.get("amount")
        if amount and float(amount) >= 5000.0:
            return True, f"Transaction amount ₹{float(amount):,.2f} meets approval threshold."

        return False, ""

    def _log_audit(self, event_type: str, severity: str, context: ToolExecutionContext, details: dict):
        try:
            AgentAuditLog.objects.create(
                agent=context.agent,
                event_type=event_type,
                severity=severity,
                actor_type="AGENT" if context.agent else "SYSTEM",
                actor_id=str(context.agent.id) if context.agent else "system",
                details=details,
            )
        except Exception as e:
            logger.warning(f"Audit log failed in tool '{self.name}': {e}")


# Universal alias conforming to both BaseTool and Tool naming conventions
Tool = BaseTool

