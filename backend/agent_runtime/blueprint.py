import json
import logging
import re
from dataclasses import dataclass, field, asdict
from decimal import Decimal
from typing import Dict, Any, List, Optional

from .models import (
    Agent,
    AgentStatus,
    AgentTool,
    AgentTrigger,
    AgentPolicy,
    AgentGovernancePolicy,
    AgentVersion,
    AgentAuditLog,
    AuditEventType,
    AuditSeverity,
)

logger = logging.getLogger(__name__)

# ── 1. VALID REGISTERED MCP TOOLS & DOMAINS ──────────────────────────────────
ALLOWED_MCP_TOOLS = {
    "getPayment",
    "searchPayments",
    "getOrder",
    "searchOrders",
    "createPaymentIntent",
    "createPaymentLink",
    "getPaymentStatus",
    "createRefund",
    "getRefunds",
    "getCustomer",
    "getInvoice",
    "getOutstandingInvoices",
    "createPayout",
    "getPayout",
    "getSettlement",
    "getCashflow",
    "sendNotification",
    "generateReport",
    "createAlert",
}

ALLOWED_DATA_SOURCES = {
    "payments",
    "refunds",
    "orders",
    "customers",
    "invoices",
    "settlements",
    "banking",
    "payouts",
    "analytics",
    "risk",
}


# ── 2. AGENT BLUEPRINT SPECIFICATION ─────────────────────────────────────────
@dataclass
class AgentBlueprint:
    name: str
    description: str
    goal: str
    trigger: Dict[str, Any]
    dataSources: List[str]
    tools: List[str]
    logic: List[str]
    conditions: List[str]
    actions: List[str]
    notifications: List[str]
    riskLevel: str  # "low", "medium", "high", "critical"
    approvalMode: str  # "auto", "review_required", "always_confirm", "blocked"
    guardrails: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── 3. DETERMINISTIC BLUEPRINT GENERATOR (FALLBACK ENGINE) ───────────────────
class DeterministicBlueprintGenerator:
    """
    Deterministic template fallback when external AI APIs are offline,
    unconfigured, or return parsing errors. Generates structured blueprints without arbitrary code.
    """

    @classmethod
    def generate(cls, prompt: str) -> AgentBlueprint:
        text = prompt.lower()

        # 1. Refund Spikes / Anomalies
        if any(k in text for k in ["refund", "spike", "return rate", "chargeback"]):
            return AgentBlueprint(
                name="Refund Spike Analyzer",
                description="Autonomous monitoring agent that continually inspects refund velocity, detects unusual volume surges, and alerts operations teams.",
                goal="Detect anomalous refund rates against historical baselines and issue operational risk alerts.",
                trigger={
                    "type": "scheduled",
                    "frequency": "daily",
                    "config": {"cron": "0 9 * * *"},
                },
                dataSources=["refunds", "orders", "payments"],
                tools=["getRefunds", "getOrder", "createAlert", "generateReport"],
                logic=[
                    "calculate daily refund rate",
                    "compare with 30-day baseline average",
                    "identify statistical volume anomalies",
                    "identify affected products and merchant batches",
                ],
                conditions=[
                    "refund_rate > baseline * 1.5",
                    "affected_sku_count >= 2",
                ],
                actions=[
                    "create alert",
                    "generate report",
                    "notify operations team",
                ],
                notifications=[
                    "email: finance-ops@razorhub.com",
                    "slack: #payment-alerts",
                ],
                riskLevel="medium",
                approvalMode="auto",
                guardrails={
                    "maxTransactionAmount": 25000.00,
                    "dailySpendLimit": 50000.00,
                    "requireApprovalAbove": 10000.00,
                    "blockedCategories": ["cash", "unknown"],
                    "allowedMerchants": [],
                    "requireDoubleConfirmation": False,
                },
            )

        # 2. Failed Payment Recovery / Dunning
        if any(k in text for k in ["failed payment", "dunning", "payment failure", "retry payment", "decline"]):
            return AgentBlueprint(
                name="Failed Payment Recovery Agent",
                description="Recovers declined customer transactions by dynamically generating smart retry payment links and issuing multi-channel notifications.",
                goal="Maximize payment conversion and recover lost revenues from transient payment gateway failures.",
                trigger={
                    "type": "event",
                    "event": "payment.failed",
                    "config": {"event_name": "payment.failed"},
                },
                dataSources=["payments", "customers", "orders"],
                tools=["createPaymentLink", "getPaymentStatus", "sendNotification", "getPayment"],
                logic=[
                    "parse failed transaction metadata and customer email",
                    "verify failure reason (insufficient funds, timeout, network error)",
                    "generate idempotent dynamic payment retry link",
                    "send recovery email and SMS to customer",
                ],
                conditions=[
                    "failure_code in ['GATEWAY_TIMEOUT', 'INSUFFICIENT_FUNDS']",
                    "retry_count < 3",
                ],
                actions=[
                    "create payment link",
                    "send notification",
                    "update payment status",
                ],
                notifications=[
                    "email: customer@example.com",
                    "webhook: dunning.retry.initiated",
                ],
                riskLevel="low",
                approvalMode="auto",
                guardrails={
                    "maxTransactionAmount": 15000.00,
                    "dailySpendLimit": 50000.00,
                    "requireApprovalAbove": 10000.00,
                    "blockedCategories": ["cash"],
                    "allowedMerchants": [],
                    "requireDoubleConfirmation": False,
                },
            )

        # 3. Abandoned Cart Recovery
        if any(k in text for k in ["abandoned cart", "cart recovery", "dropped cart", "cart reminder", "cart", "abandoned"]):

            return AgentBlueprint(
                name="Abandoned Cart Recovery Agent",
                description="Scans for inactive shopping carts, checks customer intent, and sends personalized recovery offers and payment checkout links.",
                goal="Re-engage shoppers who left items in carts and convert pending orders.",
                trigger={
                    "type": "scheduled",
                    "frequency": "hourly",
                    "config": {"cron": "0 * * * *"},
                },
                dataSources=["orders", "customers"],
                tools=["getCustomer", "getOrder", "sendNotification", "createPaymentLink"],
                logic=[
                    "scan carts abandoned for > 60 minutes",
                    "compute cart item margins and recovery discount",
                    "generate tailored checkout URL",
                    "dispatch personalized notification",
                ],
                conditions=[
                    "cart_inactivity_minutes >= 60",
                    "cart_value >= 500",
                ],
                actions=[
                    "create payment link",
                    "send notification",
                ],
                notifications=[
                    "email: cart-recovery@razorhub.com",
                ],
                riskLevel="low",
                approvalMode="auto",
                guardrails={
                    "maxTransactionAmount": 10000.00,
                    "dailySpendLimit": 30000.00,
                    "requireApprovalAbove": 5000.00,
                    "blockedCategories": ["cash"],
                    "allowedMerchants": [],
                    "requireDoubleConfirmation": False,
                },
            )

        # 4. Cashflow & Runway Forecaster
        if any(k in text for k in ["cashflow", "forecast", "runway", "treasury", "burn rate"]):
            return AgentBlueprint(
                name="Cashflow Forecaster Agent",
                description="Analyzes gateway settlement cycles, pending payouts, and historical burn rate to project 30-day and 90-day liquidity and runway.",
                goal="Provide real-time visibility into platform liquidity and treasury health.",
                trigger={
                    "type": "scheduled",
                    "frequency": "daily",
                    "config": {"cron": "0 8 * * *"},
                },
                dataSources=["settlements", "banking", "invoices", "analytics"],
                tools=["getCashflow", "getSettlement", "getOutstandingInvoices", "generateReport"],
                logic=[
                    "aggregate cleared bank deposits and pending gateway settlements",
                    "deduct scheduled supplier payouts and operational costs",
                    "simulate 30-day rolling burn velocity",
                    "compile executive cashflow dashboard report",
                ],
                conditions=[
                    "always_run == True",
                ],
                actions=[
                    "generate report",
                    "create alert if projected runway < 30 days",
                ],
                notifications=[
                    "email: treasury@razorhub.com",
                ],
                riskLevel="low",
                approvalMode="auto",
                guardrails={
                    "maxTransactionAmount": 0.00,
                    "dailySpendLimit": 0.00,
                    "requireApprovalAbove": 0.00,
                    "blockedCategories": [],
                    "allowedMerchants": [],
                    "requireDoubleConfirmation": False,
                },
            )

        # 5. Receivables & Aging Invoices
        if any(k in text for k in ["receivable", "invoice", "overdue", "unpaid", "aging"]):
            return AgentBlueprint(
                name="Receivables Agent",
                description="Tracks overdue invoices, groups debtors by aging brackets, generates instant payment links, and manages escalation schedules.",
                goal="Accelerate collection of accounts receivable and resolve delinquent invoices.",
                trigger={
                    "type": "scheduled",
                    "frequency": "weekly",
                    "config": {"cron": "0 9 * * 1"},
                },
                dataSources=["invoices", "customers", "payments"],
                tools=["getInvoice", "getOutstandingInvoices", "sendNotification", "createPaymentLink"],
                logic=[
                    "scan ledger for unpaid invoices past due date",
                    "categorize into 1-15d, 16-30d, 30d+ aging buckets",
                    "generate secure payment link for balance",
                    "dispatch polite dunning reminder to debtor",
                ],
                conditions=[
                    "invoice_status == 'OVERDUE'",
                    "days_overdue >= 7",
                ],
                actions=[
                    "create payment link",
                    "send notification",
                    "generate report",
                ],
                notifications=[
                    "email: finance@razorhub.com",
                ],
                riskLevel="low",
                approvalMode="auto",
                guardrails={
                    "maxTransactionAmount": 50000.00,
                    "dailySpendLimit": 100000.00,
                    "requireApprovalAbove": 25000.00,
                    "blockedCategories": ["cash"],
                    "allowedMerchants": [],
                    "requireDoubleConfirmation": False,
                },
            )

        # 6. Payout & Vendor Disbursements
        if any(k in text for k in ["payout", "disburse", "vendor payment", "supplier payment"]):
            return AgentBlueprint(
                name="Payout Governance Agent",
                description="Governs supplier and vendor disbursements. Cross-references invoice authorizations with bank balances and gates execution through human approval.",
                goal="Safeguard outgoing capital with strict double-confirmation checks.",
                trigger={
                    "type": "event",
                    "event": "invoice.approved",
                    "config": {"event_name": "invoice.approved"},
                },
                dataSources=["payouts", "invoices", "banking"],
                tools=["createPayout", "getPayout", "getInvoice", "createAlert"],
                logic=[
                    "match vendor invoice against purchase order approval",
                    "verify beneficiary bank IFSC and account details",
                    "evaluate transaction amount against spend ceiling",
                    "gate disbursement through human double confirmation",
                ],
                conditions=[
                    "invoice_approved == True",
                    "beneficiary_verified == True",
                ],
                actions=[
                    "create payout",
                    "create alert",
                ],
                notifications=[
                    "email: approver@razorhub.com",
                    "slack: #disbursements",
                ],
                riskLevel="critical",
                approvalMode="always_confirm",
                guardrails={
                    "maxTransactionAmount": 50000.00,
                    "dailySpendLimit": 100000.00,
                    "requireApprovalAbove": 1000.00,
                    "blockedCategories": ["cash", "unknown"],
                    "allowedMerchants": [],
                    "requireDoubleConfirmation": True,
                },
            )

        # 7. Settlement Reconciliation
        if any(k in text for k in ["settlement", "reconcile", "reconciliation", "bank ledger", "mdr"]):
            return AgentBlueprint(
                name="Settlement Reconciliation Agent",
                description="Matches payment gateway settlement batches against bank account credits, auditing MDR fee and GST deductions automatically.",
                goal="Ensure 100% accounting accuracy between payment gateway reports and bank credits.",
                trigger={
                    "type": "event",
                    "event": "settlement.processed",
                    "config": {"event_name": "settlement.processed"},
                },
                dataSources=["settlements", "payments", "banking"],
                tools=["getSettlement", "searchPayments", "generateReport", "createAlert"],
                logic=[
                    "retrieve daily gateway settlement batch payload",
                    "match transaction items against internal ledger orders",
                    "audit gateway MDR fee and GST deductions",
                    "flag variance discrepancies for accounting review",
                ],
                conditions=[
                    "variance_amount > 10.00",
                ],
                actions=[
                    "generate report",
                    "create alert if variance detected",
                ],
                notifications=[
                    "email: reconciliation@razorhub.com",
                ],
                riskLevel="low",
                approvalMode="auto",
                guardrails={
                    "maxTransactionAmount": 0.00,
                    "dailySpendLimit": 0.00,
                    "requireApprovalAbove": 0.00,
                    "blockedCategories": [],
                    "allowedMerchants": [],
                    "requireDoubleConfirmation": False,
                },
            )

        # 8. Risk & Fraud Sentinel
        if any(k in text for k in ["risk", "fraud", "velocity", "sentinel", "monitor", "suspicious"]):
            return AgentBlueprint(
                name="Risk & Security Sentinel",
                description="24/7 autonomous fraud sentinel detecting sudden velocity surges, high-risk merchant destinations, and adversarial patterns.",
                goal="Protect the platform against payment fraud, unauthorized access, and anomalous charge velocity.",
                trigger={
                    "type": "threshold",
                    "threshold": {"velocity": 20, "window_minutes": 1},
                    "config": {"velocity": 20},
                },
                dataSources=["payments", "risk", "analytics"],
                tools=["createAlert", "searchPayments", "sendNotification", "generateReport"],
                logic=[
                    "inspect real-time transaction velocity across all payment rails",
                    "detect abnormal bursts in cards/UPI authorizations",
                    "match user IP and fingerprint against known fraud databases",
                    "trigger emergency risk blocks and notify security operations",
                ],
                conditions=[
                    "velocity_per_min > 20",
                    "chargeback_score > 0.80",
                ],
                actions=[
                    "create alert",
                    "send notification",
                    "generate report",
                ],
                notifications=[
                    "email: sec-ops@razorhub.com",
                    "pager: emergency-oncall",
                ],
                riskLevel="high",
                approvalMode="auto",
                guardrails={
                    "maxTransactionAmount": 0.00,
                    "dailySpendLimit": 0.00,
                    "requireApprovalAbove": 0.00,
                    "blockedCategories": [],
                    "allowedMerchants": [],
                    "requireDoubleConfirmation": False,
                },
            )

        # Default / Custom Agent Builder Synthesizer
        # Extract title words
        clean_words = [w.capitalize() for w in re.findall(r"\b[A-Za-z]+\b", prompt) if len(w) > 3][:3]
        agent_name = f"{' '.join(clean_words)} Agent" if clean_words else "Custom Commerce Agent"

        return AgentBlueprint(
            name=agent_name,
            description=f"Autonomous agent designed to: {prompt[:120]}...",
            goal=f"Fulfill request: {prompt}",
            trigger={
                "type": "scheduled" if "daily" in text or "every" in text else "user_request",
                "frequency": "daily" if "daily" in text else "on_demand",
                "config": {},
            },
            dataSources=["payments", "orders"],
            tools=["searchPayments", "getOrder", "createAlert", "generateReport"],
            logic=[
                "receive and validate request input",
                "query platform data models within authorized scope",
                "evaluate governance policy and transaction firewall",
                "execute approved actions and notify stakeholder",
            ],
            conditions=["is_valid == True"],
            actions=["generate report", "create alert"],
            notifications=["email: admin@razorhub.com"],
            riskLevel="low",
            approvalMode="auto",
            guardrails={
                "maxTransactionAmount": 5000.00,
                "dailySpendLimit": 10000.00,
                "requireApprovalAbove": 2000.00,
                "blockedCategories": ["cash", "unknown"],
                "allowedMerchants": [],
                "requireDoubleConfirmation": False,
            },
        )


# ── 4. HYBRID LLM & FALLBACK BLUEPRINT GENERATOR ─────────────────────────────
class AgentBlueprintService:
    """
    Transforms natural language requests into typed AgentBlueprint schemas.
    Tries Google Gemini / LLM first, falling back to DeterministicBlueprintGenerator seamlessly.
    """

    SYSTEM_PROMPT = f"""
You are an expert AI Autonomous Agent Architect for RazorHub.
Your mission is to transform natural language user requests into a valid JSON AgentBlueprint.

CRITICAL RULES:
1. Return ONLY a valid JSON object matching the AgentBlueprint schema below. No markdown codeblocks, no explanations.
2. Tools MUST be selected exclusively from this list of registered MCP tools:
   {list(ALLOWED_MCP_TOOLS)}
3. DataSources MUST be selected from:
   {list(ALLOWED_DATA_SOURCES)}
4. NEVER generate executable code (Python, JS, SQL). Only output structured configuration.
5. Risk levels must be one of: "low", "medium", "high", "critical".
6. Approval modes must be one of: "auto", "review_required", "always_confirm", "blocked".

SCHEMA:
{{
  "name": "string",
  "description": "string",
  "goal": "string",
  "trigger": {{
    "type": "scheduled" | "event" | "threshold" | "user_request",
    "frequency": "daily" | "hourly" | "weekly" | "realtime" (optional),
    "event": "string" (optional),
    "threshold": {{}} (optional)
  }},
  "dataSources": ["payments", "refunds", ...],
  "tools": ["getRefunds", "createAlert", ...],
  "logic": ["step 1", "step 2", ...],
  "conditions": ["rule 1", ...],
  "actions": ["create alert", ...],
  "notifications": ["email: ops@example.com"],
  "riskLevel": "low" | "medium" | "high" | "critical",
  "approvalMode": "auto" | "review_required" | "always_confirm" | "blocked",
  "guardrails": {{
    "maxTransactionAmount": 5000.00,
    "dailySpendLimit": 10000.00,
    "requireApprovalAbove": 2000.00,
    "blockedCategories": ["cash", "unknown"],
    "allowedMerchants": [],
    "requireDoubleConfirmation": false
  }}
}}
"""

    @classmethod
    def generate(cls, user_message: str, history: Optional[List[Dict[str, str]]] = None) -> Dict[str, Any]:
        """
        Generates an AgentBlueprint from user prompt.
        Attempts LLM generation; falls back to Deterministic generator if LLM is offline or invalid.
        """
        # Attempt LLM generation
        try:
            from intelligence.agents import BaseAgent

            class BlueprintAgent(BaseAgent):
                name = "BlueprintArchitect"

            agent_caller = BlueprintAgent()

            messages = [{"role": "system", "content": cls.SYSTEM_PROMPT}]
            if history:
                messages.extend(history)
            messages.append({"role": "user", "content": user_message})

            llm_res = agent_caller.call_gemini_json(messages, context={}, temperature=0.2)

            if isinstance(llm_res, dict) and "name" in llm_res and "tools" in llm_res:
                sanitized = cls._sanitize_and_validate(llm_res, user_message)
                return {
                    "blueprint": sanitized.to_dict(),
                    "ai_message": (
                        f"I have designed the **{sanitized.name}** based on your prompt. "
                        f"It connects {len(sanitized.tools)} MCP tools with {sanitized.approvalMode.upper()} approval governance. "
                        f"You can review and customize the blueprint on the right before activating."
                    ),
                    "source": "LLM",
                }
        except Exception as e:
            logger.info(f"LLM blueprint generation unavailable or failed: {e}. Falling back to deterministic engine.")

        # Fallback to deterministic blueprint generator
        blueprint = DeterministicBlueprintGenerator.generate(user_message)
        return {
            "blueprint": blueprint.to_dict(),
            "ai_message": (
                f"I have generated the **{blueprint.name}** blueprint for your request. "
                f"It includes {len(blueprint.tools)} MCP tools ({', '.join(blueprint.tools)}) and {blueprint.approvalMode.upper()} approval governance. "
                f"Review the configuration on the right and adjust spending limits or triggers as needed."
            ),
            "source": "DETERMINISTIC_FALLBACK",
        }

    @classmethod
    def _sanitize_and_validate(cls, raw: Dict[str, Any], prompt: str) -> AgentBlueprint:
        """
        Sanitizes and enforces strict schema compliance on LLM output.
        """
        name = str(raw.get("name", "Custom Commerce Agent"))[:100]
        desc = str(raw.get("description", f"Agent designed for {prompt}"))[:300]
        goal = str(raw.get("goal", prompt))[:300]

        trigger = raw.get("trigger", {})
        if not isinstance(trigger, dict):
            trigger = {"type": "user_request"}

        # Validate tools: only allow registered MCP tools
        raw_tools = raw.get("tools", [])
        if not isinstance(raw_tools, list):
            raw_tools = []
        valid_tools = [t for t in raw_tools if t in ALLOWED_MCP_TOOLS]
        if not valid_tools:
            valid_tools = ["getOrder", "createAlert", "generateReport"]

        # Validate data sources
        raw_sources = raw.get("dataSources", [])
        if not isinstance(raw_sources, list):
            raw_sources = []
        valid_sources = [s for s in raw_sources if s in ALLOWED_DATA_SOURCES]
        if not valid_sources:
            valid_sources = ["orders", "payments"]

        risk_level = str(raw.get("riskLevel", "low")).lower()
        if risk_level not in ["low", "medium", "high", "critical"]:
            risk_level = "low"

        approval_mode = str(raw.get("approvalMode", "auto")).lower()
        if approval_mode not in ["auto", "review_required", "always_confirm", "blocked"]:
            approval_mode = "auto"

        # Guardrails
        guardrails_raw = raw.get("guardrails", {})
        if not isinstance(guardrails_raw, dict):
            guardrails_raw = {}

        max_amount = float(guardrails_raw.get("maxTransactionAmount", 5000.00))
        daily_limit = float(guardrails_raw.get("dailySpendLimit", 10000.00))
        approval_above = float(guardrails_raw.get("requireApprovalAbove", 2000.00))
        blocked_cats = guardrails_raw.get("blockedCategories", ["cash", "unknown"])
        if not isinstance(blocked_cats, list):
            blocked_cats = ["cash", "unknown"]
        allowed_merchants = guardrails_raw.get("allowedMerchants", [])
        if not isinstance(allowed_merchants, list):
            allowed_merchants = []
        double_confirm = bool(guardrails_raw.get("requireDoubleConfirmation", risk_level == "critical"))

        return AgentBlueprint(
            name=name,
            description=desc,
            goal=goal,
            trigger=trigger,
            dataSources=valid_sources,
            tools=valid_tools,
            logic=raw.get("logic", ["execute approved tasks"]),
            conditions=raw.get("conditions", []),
            actions=raw.get("actions", ["generate report"]),
            notifications=raw.get("notifications", ["email: admin@razorhub.com"]),
            riskLevel=risk_level,
            approvalMode=approval_mode,
            guardrails={
                "maxTransactionAmount": max_amount,
                "dailySpendLimit": daily_limit,
                "requireApprovalAbove": approval_above,
                "blockedCategories": blocked_cats,
                "allowedMerchants": allowed_merchants,
                "requireDoubleConfirmation": double_confirm,
            },
        )

    @classmethod
    def provision_blueprint(
        cls,
        blueprint_data: Dict[str, Any],
        status: str = "ACTIVE",
        user=None,
    ) -> Agent:
        """
        Translates a validated AgentBlueprint into persistent Django models:
        Agent, AgentGovernancePolicy, AgentTrigger, AgentTool links, and initial AgentVersion.
        """
        name = blueprint_data.get("name", "Custom Blueprint Agent").strip()
        desc = blueprint_data.get("description", "").strip()
        risk_level = blueprint_data.get("riskLevel", "LOW").upper()
        approval_mode = blueprint_data.get("approvalMode", "AUTO").upper()

        system_prompt = (
            f"You are the {name}. Goal: {blueprint_data.get('goal', '')}\n"
            f"Operational Logic:\n" + "\n".join(f"- {step}" for step in blueprint_data.get("logic", [])) + "\n"
            f"Conditions:\n" + "\n".join(f"- {cond}" for cond in blueprint_data.get("conditions", [])) + "\n"
            f"Adhere strictly to deterministic spending limits and governance firewalls."
        )

        agent_status = AgentStatus.ACTIVE if status.upper() == "ACTIVE" else AgentStatus.DRAFT

        # Ensure unique agent name
        base_name = name
        counter = 1
        while Agent.objects.filter(name=name).exists():
            name = f"{base_name} ({counter})"
            counter += 1

        # 1. Create Agent
        agent = Agent.objects.create(
            name=name,

            description=desc,
            system_prompt=system_prompt,
            status=agent_status,
            approval_mode=approval_mode,
            risk_level=risk_level,
            metadata={
                "blueprint": blueprint_data,
                "goal": blueprint_data.get("goal"),
                "data_sources": blueprint_data.get("dataSources", []),
                "actions": blueprint_data.get("actions", []),
                "notifications": blueprint_data.get("notifications", []),
            },
        )

        # 2. Attach Tools
        tools_list = blueprint_data.get("tools", [])
        for tool_name in tools_list:
            if tool_name in ALLOWED_MCP_TOOLS:
                tool_obj, _ = AgentTool.objects.get_or_create(
                    name=tool_name,
                    defaults={
                        "category": "blueprint",
                        "description": f"MCP Tool {tool_name} attached via Agent Blueprint",
                    },
                )
                agent.tools.add(tool_obj)

        # 3. Create Trigger
        trig_data = blueprint_data.get("trigger", {})
        trig_type = trig_data.get("type", "USER_REQUEST").upper()
        if trig_type not in ["USER_REQUEST", "SCHEDULE", "EVENT", "THRESHOLD"]:
            trig_type = "USER_REQUEST"

        AgentTrigger.objects.create(
            agent=agent,
            name=f"{name} Trigger ({trig_type})",
            trigger_type=trig_type,
            configuration=trig_data.get("config", {}),
        )


        # 4. Create Governance Policy
        guard = blueprint_data.get("guardrails", {})
        AgentGovernancePolicy.objects.create(
            agent=agent,
            name=f"{name} Guardrail Policy",
            max_transaction_amount=Decimal(str(guard.get("maxTransactionAmount", 5000.00))),
            daily_spend_limit=Decimal(str(guard.get("dailySpendLimit", 10000.00))),
            require_approval_above=Decimal(str(guard.get("requireApprovalAbove", 2000.00))),
            blocked_categories=guard.get("blockedCategories", ["cash", "unknown"]),
            allowed_merchants=guard.get("allowedMerchants", []),
            require_human_approval=(approval_mode in ["REVIEW_REQUIRED", "ALWAYS_CONFIRM"]),
            require_double_confirmation=bool(guard.get("requireDoubleConfirmation", risk_level == "CRITICAL")),
        )

        # 5. Snapshot Version
        AgentVersion.objects.create(
            agent=agent,
            system_prompt=agent.system_prompt,
            configuration={"tools": tools_list, "guardrails": guard},
            change_summary="Initial blueprint provision",
        )


        # 6. Immutable Audit Log
        AgentAuditLog.objects.create(
            agent=agent,
            event_type=AuditEventType.AGENT_CREATED,
            severity=AuditSeverity.INFO,
            actor_type="USER" if user else "SYSTEM",
            actor_id=str(user.id) if user else "system",
            details={
                "action": "PROVISIONED_FROM_CONVERSATIONAL_BLUEPRINT",
                "status": agent.status,
                "tools": tools_list,
                "risk_level": risk_level,
            },
        )

        return agent
