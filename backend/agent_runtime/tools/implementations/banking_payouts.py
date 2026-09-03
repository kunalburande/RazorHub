from typing import Dict, Any, Optional
from ..base import BaseTool, ToolExecutionContext
from ..categories import ToolCategory
from ...models import RiskLevel
from ..providers.factory import get_banking_provider


class CreatePayoutTool(BaseTool):
    id = "tool_create_payout"
    name = "createPayout"
    description = "Disburses funds to an external vendor, supplier, or seller bank account."
    category = ToolCategory.PAYOUTS
    risk_level = RiskLevel.CRITICAL
    requires_approval = True  # Payouts always require approval by default
    is_mutation = True
    max_amount_limit = 50000.0
    required_permissions = ["seller", "admin"]

    input_schema = {
        "type": "object",
        "properties": {
            "recipient_account": {"type": "string", "description": "Bank account number or VPA"},
            "amount": {"type": "number", "description": "Payout amount in INR"},
            "currency": {"type": "string", "default": "INR"},
            "narration": {"type": "string", "description": "Statement reference note"},
            "idempotency_key": {"type": "string"},
        },
        "required": ["recipient_account", "amount"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["id", "amount", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_banking_provider()
        return provider.create_payout(
            recipient_account=input_data["recipient_account"],
            amount=input_data["amount"],
            currency=input_data.get("currency", "INR"),
            narration=input_data.get("narration", "Agentic Payout"),
        )


class GetPayoutTool(BaseTool):
    id = "tool_get_payout"
    name = "getPayout"
    description = "Checks status, UTR reference, and clearing mode of a payout disbursement."
    category = ToolCategory.PAYOUTS
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "payout_id": {"type": "string", "description": "Payout transaction ID"},
        },
        "required": ["payout_id"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "amount": {"type": "number"},
            "status": {"type": "string"},
            "mode": {"type": "string"},
        },
        "required": ["id", "amount", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_banking_provider()
        return provider.get_payout(input_data["payout_id"])


class GetSettlementTool(BaseTool):
    id = "tool_get_settlement"
    name = "getSettlement"
    description = "Fetches payment gateway settlement cycles, deductions, and credited amounts."
    category = ToolCategory.BANKING
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "settlement_id": {"type": "string", "description": "Settlement ID"},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "amount": {"type": "number"},
            "fees": {"type": "number"},
            "net_amount": {"type": "number"},
            "status": {"type": "string"},
        },
        "required": ["id", "amount", "net_amount", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_banking_provider()
        return provider.get_settlement(input_data.get("settlement_id"))
