from typing import Dict, Any
from ..base import BaseTool, ToolExecutionContext
from ..categories import ToolCategory
from ...models import RiskLevel
from ..providers.factory import get_payment_provider


class CreateRefundTool(BaseTool):
    id = "tool_create_refund"
    name = "createRefund"
    description = "Issues a full or partial refund for a captured payment back to original payment method."
    category = ToolCategory.REFUNDS
    risk_level = RiskLevel.HIGH
    requires_approval = True  # Refunds require explicit approval by default
    is_mutation = True
    max_amount_limit = 25000.0
    required_permissions = ["seller", "admin", "all"]

    input_schema = {
        "type": "object",
        "properties": {
            "payment_id": {"type": "string", "description": "Original payment transaction ID"},
            "amount": {"type": "number", "description": "Refund amount (optional, defaults to full payment amount)"},
            "reason": {"type": "string", "description": "Reason for refund"},
            "idempotency_key": {"type": "string"},
        },
        "required": ["payment_id"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "payment_id": {"type": "string"},
            "amount": {"type": "number"},
            "status": {"type": "string"},
        },
        "required": ["id", "payment_id", "amount", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_payment_provider()
        return provider.create_refund(
            payment_id=input_data["payment_id"],
            amount=input_data.get("amount"),
            reason=input_data.get("reason", "Agent initiated refund"),
        )


class GetRefundsTool(BaseTool):
    id = "tool_get_refunds"
    name = "getRefunds"
    description = "Lists refunds associated with a payment or recent store activity."
    category = ToolCategory.REFUNDS
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "payment_id": {"type": "string", "description": "Optional filter by payment ID"},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "refunds": {"type": "array"},
            "count": {"type": "integer"},
        },
        "required": ["refunds", "count"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_payment_provider()
        refunds = provider.get_refunds(input_data.get("payment_id"))
        return {"refunds": refunds, "count": len(refunds)}
