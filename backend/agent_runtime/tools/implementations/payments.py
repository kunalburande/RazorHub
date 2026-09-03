from typing import Dict, Any
from ..base import BaseTool, ToolExecutionContext
from ..categories import ToolCategory
from ...models import RiskLevel
from ..providers.factory import get_payment_provider


class GetPaymentTool(BaseTool):
    id = "tool_get_payment"
    name = "getPayment"
    description = "Retrieves payment details by payment ID or gateway transaction reference."
    category = ToolCategory.PAYMENTS
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "payment_id": {"type": "string", "description": "Payment ID (e.g. pay_123)"},
        },
        "required": ["payment_id"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string"},
            "method": {"type": "string"},
        },
        "required": ["id", "amount", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_payment_provider()
        return provider.get_payment(input_data["payment_id"])


class SearchPaymentsTool(BaseTool):
    id = "tool_search_payments"
    name = "searchPayments"
    description = "Searches and filters payments by status, customer, or date range."
    category = ToolCategory.PAYMENTS
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "description": "Filter by payment status (captured, authorized, failed)"},
            "limit": {"type": "integer", "description": "Maximum records to return"},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "payments": {"type": "array"},
            "count": {"type": "integer"},
        },
        "required": ["payments", "count"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_payment_provider()
        results = provider.search_payments(input_data)
        limit = input_data.get("limit", 10)
        return {"payments": results[:limit], "count": len(results[:limit])}


class CreatePaymentIntentTool(BaseTool):
    id = "tool_create_payment_intent"
    name = "createPaymentIntent"
    description = "Authorizes and creates a new payment intent with defined amount and currency."
    category = ToolCategory.PAYMENTS
    risk_level = RiskLevel.HIGH
    requires_approval = False
    is_mutation = True
    max_amount_limit = 100000.0  # Max ₹1,00,000 ceiling per intent
    required_permissions = ["seller", "admin", "all"]

    input_schema = {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Payment amount in INR"},
            "currency": {"type": "string", "default": "INR"},
            "customer_id": {"type": "string"},
            "idempotency_key": {"type": "string", "description": "Unique key to prevent duplicate charges"},
        },
        "required": ["amount"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string"},
            "client_secret": {"type": "string"},
        },
        "required": ["id", "amount", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_payment_provider()
        return provider.create_payment_intent(
            amount=input_data["amount"],
            currency=input_data.get("currency", "INR"),
            customer_id=input_data.get("customer_id", ""),
            metadata=input_data.get("metadata", {}),
        )


class CreatePaymentLinkTool(BaseTool):
    id = "tool_create_payment_link"
    name = "createPaymentLink"
    description = "Generates a shareable payment link with automated customer notification."
    category = ToolCategory.PAYMENTS
    risk_level = RiskLevel.MEDIUM
    requires_approval = False
    is_mutation = True
    max_amount_limit = 50000.0
    required_permissions = ["seller", "admin", "all"]

    input_schema = {
        "type": "object",
        "properties": {
            "amount": {"type": "number", "description": "Payment amount in INR"},
            "currency": {"type": "string", "default": "INR"},
            "customer_email": {"type": "string", "description": "Recipient email address"},
            "description": {"type": "string"},
            "idempotency_key": {"type": "string"},
        },
        "required": ["amount", "customer_email"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "short_url": {"type": "string"},
            "amount": {"type": "number"},
            "currency": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["id", "short_url", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_payment_provider()
        return provider.create_payment_link(
            amount=input_data["amount"],
            currency=input_data.get("currency", "INR"),
            customer_email=input_data["customer_email"],
            description=input_data.get("description", ""),
        )


class GetPaymentStatusTool(BaseTool):
    id = "tool_get_payment_status"
    name = "getPaymentStatus"
    description = "Checks real-time transaction status from payment gateway."
    category = ToolCategory.PAYMENTS
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "payment_id": {"type": "string", "description": "Payment ID"},
        },
        "required": ["payment_id"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "payment_id": {"type": "string"},
            "status": {"type": "string"},
            "captured": {"type": "boolean"},
        },
        "required": ["payment_id", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_payment_provider()
        return provider.get_payment_status(input_data["payment_id"])
