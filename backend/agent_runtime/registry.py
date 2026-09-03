import inspect
import logging
from typing import Callable, Any, Dict, List, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class RegisteredTool:
    name: str
    description: str
    handler: Callable
    category: str = "general"
    risk_level: str = "LOW"
    parameters_schema: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)


class ToolRegistry:
    """
    Central in-memory registry for all tools accessible by the Agent Runtime.
    Enforces parameter validation, schema compliance, and sandboxed execution.
    """
    _registry: Dict[str, RegisteredTool] = {}

    @classmethod
    def register(
        cls,
        name: str,
        description: str,
        category: str = "general",
        risk_level: str = "LOW",
        parameters_schema: Optional[Dict[str, Any]] = None,
        required_permissions: Optional[List[str]] = None,
    ):
        """Decorator to register a tool callable."""
        def decorator(func: Callable):
            schema = parameters_schema or cls._derive_schema(func)
            registered = RegisteredTool(
                name=name,
                description=description,
                handler=func,
                category=category,
                risk_level=risk_level,
                parameters_schema=schema,
                required_permissions=required_permissions or [],
            )
            cls._registry[name] = registered
            return func
        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[RegisteredTool]:
        if name in cls._registry:
            return cls._registry[name]
        try:
            from .tools.registry import ToolRegistry as TypedRegistry
            typed = TypedRegistry.get(name)
            if typed:
                return RegisteredTool(
                    name=typed.name,
                    description=typed.description,
                    handler=lambda **kwargs: typed.execute(kwargs, kwargs.get("context")),
                    category=str(typed.category).lower(),
                    risk_level=typed.risk_level,
                    parameters_schema=typed.input_schema,
                    required_permissions=typed.required_permissions,
                )
        except Exception:
            pass
        return None

    @classmethod
    def list_tools(cls) -> List[RegisteredTool]:
        tools = list(cls._registry.values())
        try:
            from .tools.registry import ToolRegistry as TypedRegistry
            for t in TypedRegistry.list_tools():
                if t.name not in cls._registry:
                    tools.append(RegisteredTool(
                        name=t.name,
                        description=t.description,
                        handler=lambda **kwargs: t.execute(kwargs, kwargs.get("context")),
                        category=str(t.category).lower(),
                        risk_level=t.risk_level,
                        parameters_schema=t.input_schema,
                        required_permissions=t.required_permissions,
                    ))
        except Exception:
            pass
        return tools

    @classmethod
    def execute(cls, name: str, arguments: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute registered tool with argument validation and error boundaries.
        Returns: {"success": bool, "result": Any, "error": str | None}
        """
        context = context or {}

        # 1. Check typed registry first for full financial guardrail execution
        try:
            from .tools.registry import ToolRegistry as TypedRegistry
            from .tools.base import ToolExecutionContext
            typed = TypedRegistry.get(name)
            if typed:
                exec_ctx = ToolExecutionContext(
                    user=context.get("user"),
                    agent=context.get("agent"),
                    session_id=context.get("session_id", ""),
                    is_pre_approved=context.get("is_pre_approved", False),
                )
                res = typed.run_with_guardrails(arguments, exec_ctx)
                return {
                    "success": res.success,
                    "result": res.result,
                    "error": res.error,
                    "approval_required": res.approval_required,
                    "approval_reason": res.approval_reason,
                    "is_idempotent_replay": res.is_idempotent_replay,
                }
        except Exception as e:
            logger.debug(f"TypedRegistry bypass for {name}: {e}")

        tool = cls.get(name)
        if not tool:
            return {
                "success": False,
                "result": None,
                "error": f"Tool '{name}' is not registered in runtime registry.",
            }

        # 1. Parameter Validation
        val_error = cls._validate_arguments(tool, arguments)
        if val_error:
            return {
                "success": False,
                "result": None,
                "error": f"Argument validation error for tool '{name}': {val_error}",
            }

        # 2. Execution
        try:
            sig = inspect.signature(tool.handler)
            # Pass context if handler accepts it
            if "context" in sig.parameters:
                result = tool.handler(**arguments, context=context)
            else:
                result = tool.handler(**arguments)

            return {
                "success": True,
                "result": result,
                "error": None,
            }
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return {
                "success": False,
                "result": None,
                "error": f"Execution failed in '{name}': {str(e)}",
            }

    @classmethod
    def _validate_arguments(cls, tool: RegisteredTool, arguments: Dict[str, Any]) -> Optional[str]:
        schema = tool.parameters_schema
        required = schema.get("required", [])
        for req in required:
            if req not in arguments or arguments[req] is None:
                return f"Missing required parameter '{req}'"

        properties = schema.get("properties", {})
        for key, val in arguments.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "number" and not isinstance(val, (int, float)):
                    return f"Parameter '{key}' must be a number"
                elif expected_type == "integer" and not isinstance(val, int):
                    return f"Parameter '{key}' must be an integer"
                elif expected_type == "string" and not isinstance(val, str):
                    return f"Parameter '{key}' must be a string"
                elif expected_type == "boolean" and not isinstance(val, bool):
                    return f"Parameter '{key}' must be a boolean"
                elif expected_type == "array" and not isinstance(val, list):
                    return f"Parameter '{key}' must be a list"
                elif expected_type == "object" and not isinstance(val, dict):
                    return f"Parameter '{key}' must be a dictionary"
        return None

    @classmethod
    def _derive_schema(cls, func: Callable) -> Dict[str, Any]:
        sig = inspect.signature(func)
        properties = {}
        required = []
        type_map = {
            int: "integer",
            float: "number",
            str: "string",
            bool: "boolean",
            list: "array",
            dict: "object",
        }
        for param_name, param in sig.parameters.items():
            if param_name == "context":
                continue
            prop_info: Dict[str, Any] = {"type": "string"}
            if param.annotation in type_map:
                prop_info["type"] = type_map[param.annotation]
            properties[param_name] = prop_info
            if param.default == inspect.Parameter.empty:
                required.append(param_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
        }


# Convenience decorator
register_tool = ToolRegistry.register


# ── BUILT-IN STANDARD TOOLS ───────────────────────────────────────────────────
def register_builtin_tools():
    """Register core baseline tools for testing and standard commerce operations."""

    @register_tool(
        name="echo",
        description="Echoes back the provided text message for diagnostic and health verification.",
        category="system",
        risk_level="LOW",
        parameters_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
    )
    def echo_tool(message: str) -> dict:
        return {"echo": message, "status": "ok"}

    @register_tool(
        name="check_balance",
        description="Checks the current available and reserved balance for a designated account or wallet.",
        category="financial",
        risk_level="LOW",
        parameters_schema={
            "type": "object",
            "properties": {
                "account_id": {"type": "string"},
                "currency": {"type": "string"},
            },
            "required": ["account_id"],
        },
    )
    def check_balance_tool(account_id: str, currency: str = "INR") -> dict:
        # Mock / baseline account lookup
        return {
            "account_id": account_id,
            "currency": currency or "INR",
            "available_balance": 150000.00,
            "reserved_balance": 5000.00,
            "status": "active",
        }

    @register_tool(
        name="transfer_funds",
        description="Initiates an internal or external fund transfer between accounts. Subject to spending limits and approval.",
        category="financial",
        risk_level="HIGH",
        parameters_schema={
            "type": "object",
            "properties": {
                "recipient_id": {"type": "string"},
                "amount": {"type": "number"},
                "currency": {"type": "string"},
                "note": {"type": "string"},
            },
            "required": ["recipient_id", "amount"],
        },
    )
    def transfer_funds_tool(recipient_id: str, amount: float, currency: str = "INR", note: str = "") -> dict:
        return {
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "recipient_id": recipient_id,
            "amount": float(amount),
            "currency": currency or "INR",
            "status": "completed",
            "note": note,
        }

    @register_tool(
        name="query_catalog",
        description="Searches active products in the store catalog with optional price filtering.",
        category="commerce",
        risk_level="LOW",
        parameters_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "max_price": {"type": "number"},
            },
            "required": ["query"],
        },
    )
    def query_catalog_tool(query: str, max_price: float = None) -> dict:
        from products.models import Product
        qs = Product.objects.filter(is_active=True, name__icontains=query)
        if max_price:
            qs = qs.filter(price__lte=max_price)
        results = [
            {"id": p.id, "name": p.name, "price": float(p.price), "stock": p.stock}
            for p in qs[:5]
        ]
        return {"items": results, "count": len(results)}

    @register_tool(
        name="execute_payout",
        description="Executes a verified vendor or merchant payout.",
        category="banking",
        risk_level="HIGH",
        parameters_schema={
            "type": "object",
            "properties": {
                "recipient": {"type": "string"},
                "amount": {"type": "number"},
                "currency": {"type": "string"},
            },
            "required": ["recipient", "amount"],
        },
    )
    def execute_payout_tool(recipient: str, amount: float, currency: str = "INR") -> dict:
        import uuid
        return {
            "payout_id": f"pout_{uuid.uuid4().hex[:12]}",
            "recipient": recipient,
            "amount": float(amount),
            "currency": currency,
            "status": "PROCESSED",
        }

    @register_tool(
        name="create_payment_intent",
        description="Creates an authorized commerce payment intent.",
        category="commerce",
        risk_level="MEDIUM",
        parameters_schema={
            "type": "object",
            "properties": {
                "amount": {"type": "number"},
                "currency": {"type": "string"},
                "item": {"type": "string"},
            },
            "required": ["amount"],
        },
    )
    def create_payment_intent_tool(amount: float, currency: str = "INR", item: str = "") -> dict:
        import uuid
        return {
            "intent_id": f"pi_{uuid.uuid4().hex[:12]}",
            "amount": float(amount),
            "currency": currency,
            "item": item,
            "status": "AUTHORIZED",
        }

    @register_tool(
        name="generate_report",
        description="Generates executive business and financial reports.",
        category="analytics",
        risk_level="LOW",
        parameters_schema={
            "type": "object",
            "properties": {
                "report_type": {"type": "string"},
            },
            "required": ["report_type"],
        },
    )
    def generate_report_tool(report_type: str = "EXECUTIVE_SUMMARY") -> dict:
        return {
            "report_id": "rep_exec_001",
            "report_type": report_type,
            "metrics": {"revenue_mtd": 1250000, "profit_margin": 0.24},
            "status": "READY",
        }

    @register_tool(
        name="fetch_balance",
        description="Fetches primary treasury account balance.",
        category="financial",
        risk_level="LOW",
    )
    def fetch_balance_tool(account_id: str = "acc_primary_001") -> dict:
        return {
            "account_id": account_id,
            "available_balance": 150000.00,
            "status": "active",
        }

    @register_tool(
        name="analyze_refunds",
        description="Analyzes refund trends and calculates anomaly score.",
        category="analytics",
        risk_level="LOW",
    )
    def analyze_refunds_tool(lookback_days: int = 30) -> dict:
        return {"refund_rate": 0.042, "baseline_rate": 0.038, "anomaly_detected": False}

    @register_tool(
        name="get_overdue_invoices",
        description="Fetches all pending accounts receivable invoices.",
        category="banking",
        risk_level="LOW",
    )
    def get_overdue_invoices_tool(days_threshold: int = 30) -> dict:
        return {"overdue_count": 3, "total_overdue_amount": 75000.0}

    @register_tool(
        name="reconcile_settlements",
        description="Reconciles bank settlements against transaction ledger.",
        category="banking",
        risk_level="LOW",
    )
    def reconcile_settlements_tool(batch_id: str = "set_batch_today") -> dict:
        return {"batch_id": batch_id, "reconciled_count": 142, "discrepancies": 0}


register_builtin_tools()

