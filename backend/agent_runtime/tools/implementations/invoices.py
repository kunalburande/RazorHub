from typing import Dict, Any
from ..base import BaseTool, ToolExecutionContext
from ..categories import ToolCategory
from ...models import RiskLevel


class GetInvoiceTool(BaseTool):
    id = "tool_get_invoice"
    name = "getInvoice"
    description = "Fetches tax invoice details, GST/subtotal breakdown, and settlement status."
    category = ToolCategory.INVOICES
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string", "description": "Invoice number (e.g. INV-2026-004)"},
        },
        "required": ["invoice_id"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string"},
            "subtotal": {"type": "number"},
            "tax": {"type": "number"},
            "total": {"type": "number"},
            "status": {"type": "string"},
        },
        "required": ["invoice_id", "total", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        inv_id = input_data["invoice_id"]
        return {
            "invoice_id": inv_id,
            "customer_name": "Acme Retailers Pvt Ltd",
            "gstin": "29AABCU9603R1ZM",
            "subtotal": 12000.0,
            "tax": 2160.0,
            "total": 14160.0,
            "currency": "INR",
            "status": "paid",
            "due_date": "2026-09-15",
        }


class GetOutstandingInvoicesTool(BaseTool):
    id = "tool_get_outstanding_invoices"
    name = "getOutstandingInvoices"
    description = "Queries unpaid or pending invoices with aging days."
    category = ToolCategory.INVOICES
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "days_overdue": {"type": "integer", "description": "Filter by minimum days overdue"},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "invoices": {"type": "array"},
            "total_outstanding": {"type": "number"},
            "count": {"type": "integer"},
        },
        "required": ["invoices", "total_outstanding", "count"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        invoices = [
            {
                "invoice_id": "INV-2026-012",
                "customer": "TechCorp Solutions",
                "amount": 45000.0,
                "days_overdue": 8,
                "status": "overdue",
            },
            {
                "invoice_id": "INV-2026-019",
                "customer": "Global Logistics",
                "amount": 18500.0,
                "days_overdue": 2,
                "status": "pending",
            },
        ]
        return {
            "invoices": invoices,
            "total_outstanding": sum(i["amount"] for i in invoices),
            "count": len(invoices),
        }
