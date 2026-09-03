import time
from typing import Dict, Any
from ..base import BaseTool, ToolExecutionContext
from ..categories import ToolCategory
from ...models import RiskLevel
from ..providers.factory import get_banking_provider


class GetCashflowTool(BaseTool):
    id = "tool_get_cashflow"
    name = "getCashflow"
    description = "Calculates cash inflow/outflow metrics, projected burn rate, and runway months."
    category = ToolCategory.ANALYTICS
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "start_date": {"type": "string"},
            "end_date": {"type": "string"},
        },
    }
    output_schema = {
        "type": "object",
        "properties": {
            "opening_balance": {"type": "number"},
            "total_inflows": {"type": "number"},
            "total_outflows": {"type": "number"},
            "net_cashflow": {"type": "number"},
            "closing_balance": {"type": "number"},
            "runway_months": {"type": "number"},
        },
        "required": ["opening_balance", "closing_balance", "net_cashflow"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_banking_provider()
        return provider.get_cashflow(
            start_date=input_data.get("start_date"),
            end_date=input_data.get("end_date"),
        )


class GenerateReportTool(BaseTool):
    id = "tool_generate_report"
    name = "generateReport"
    description = "Compiles financial summary or tax reconciliation report for a designated period."
    category = ToolCategory.REPORTING
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = False

    input_schema = {
        "type": "object",
        "properties": {
            "report_type": {"type": "string", "description": "Type of report (reconciliation, tax, transactions)"},
            "period": {"type": "string", "description": "monthly, quarterly, annual"},
        },
        "required": ["report_type"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "report_id": {"type": "string"},
            "report_type": {"type": "string"},
            "generated_at": {"type": "string"},
            "summary": {"type": "object"},
        },
        "required": ["report_id", "report_type", "summary"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        rtype = input_data["report_type"]
        return {
            "report_id": f"rep_{int(time.time())}",
            "report_type": rtype,
            "period": input_data.get("period", "monthly"),
            "generated_at": "2026-09-03T12:00:00Z",
            "summary": {
                "total_volume": 425000.0,
                "transaction_count": 142,
                "successful_count": 139,
                "refunded_count": 3,
                "tax_collected_gst": 38250.0,
            },
        }
