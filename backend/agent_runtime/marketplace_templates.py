from decimal import Decimal
from typing import Dict, Any, List

PREBUILT_AGENT_TEMPLATES: List[Dict[str, Any]] = [
    {
        "id": "failed-payment-recovery",
        "name": "Failed Payment Recovery",
        "description": "Autonomous intelligent dunning and retry agent. Detects failed gateway charges, generates smart recovery payment links, and coordinates multi-channel customer reach-outs.",
        "category": "PAYMENTS",
        "automation_level": "AUTONOMOUS",
        "risk_level": "LOW",
        "approval_mode": "AUTO",
        "capabilities": [
            "Real-time failed payment detection",
            "Dynamic payment link generation with custom expiry",
            "Automated email & SMS retry notifications",
            "Payment status polling and auto-reconciliation",
        ],
        "tools_used": ["createPaymentLink", "getPaymentStatus", "sendNotification", "getPayment"],
        "system_prompt": (
            "You are the Failed Payment Recovery Agent for RazorHub. When a payment failure occurs, "
            "verify the customer email and transaction reference, generate a secure payment recovery link, "
            "and dispatch a polite re-engagement notice to the customer. Ensure all payment links include idempotency keys."
        ),
        "triggers": [
            {"trigger_type": "EVENT", "name": "Payment Failed Event", "config": {"event": "payment.failed"}},
            {"trigger_type": "USER_REQUEST", "name": "Manual Recovery Request", "config": {}},
        ],
        "governance_policy": {
            "name": "Failed Payment Recovery Guardrail",
            "max_transaction_amount": Decimal("25000.00"),
            "daily_spend_limit": Decimal("100000.00"),
            "require_approval_above": Decimal("15000.00"),
            "blocked_categories": ["cash", "unknown"],
            "allowed_categories": ["payments", "communication"],
            "require_human_approval": False,
            "require_double_confirmation": False,
        },
    },
    {
        "id": "abandoned-cart-recovery",
        "name": "Abandoned Cart Recovery",
        "description": "Engages shoppers who left items in cart. Analyzes checkout session drops, prepares personalized cart revival links, and schedules follow-up communications.",
        "category": "CUSTOMERS",
        "automation_level": "AUTONOMOUS",
        "risk_level": "LOW",
        "approval_mode": "AUTO",
        "capabilities": [
            "Abandoned checkout session scanning",
            "Cart value and intent risk scoring",
            "Personalized recovery notification generation",
            "Automated payment checkout link creation",
        ],
        "tools_used": ["getCustomer", "getOrder", "sendNotification", "createPaymentLink"],
        "system_prompt": (
            "You are the Abandoned Cart Recovery Agent for RazorHub. Identify dropped checkout carts, "
            "inspect customer profiles, generate tailored cart revival payment links, and send follow-up reminders."
        ),
        "triggers": [
            {"trigger_type": "SCHEDULE", "name": "Hourly Cart Scan", "config": {"cron": "0 * * * *"}},
            {"trigger_type": "USER_REQUEST", "name": "Trigger Cart Campaign", "config": {}},
        ],
        "governance_policy": {
            "name": "Abandoned Cart Recovery Guardrail",
            "max_transaction_amount": Decimal("15000.00"),
            "daily_spend_limit": Decimal("50000.00"),
            "require_approval_above": Decimal("10000.00"),
            "blocked_categories": ["cash"],
            "allowed_categories": ["customers", "orders", "payments"],
            "require_human_approval": False,
            "require_double_confirmation": False,
        },
    },
    {
        "id": "refund-spike-analyzer",
        "name": "Refund Spike Analyzer",
        "description": "Monitors refund requests and return rates. Detects anomalous velocity surges, defective catalog batches, or merchant anomalies, pausing auto-refunds when risk thresholds trigger.",
        "category": "REFUNDS",
        "automation_level": "SEMI_AUTONOMOUS",
        "risk_level": "MEDIUM",
        "approval_mode": "REVIEW_REQUIRED",
        "capabilities": [
            "Refund frequency and volume velocity monitoring",
            "Abnormal merchant & product category spike detection",
            "Automated operational risk alerts generation",
            "Audit report generation for compliance teams",
        ],
        "tools_used": ["getRefunds", "createAlert", "getOrder", "generateReport"],
        "system_prompt": (
            "You are the Refund Spike Analyzer Agent. Continually inspect recent refund activities, calculate refund-to-order "
            "ratios, and raise operational alerts whenever refund volume exceeds normal variance limits. Never auto-process suspicious refund spikes."
        ),
        "triggers": [
            {"trigger_type": "THRESHOLD", "name": "Refund Rate > 5%", "config": {"metric": "refund_ratio", "threshold": 0.05}},
            {"trigger_type": "USER_REQUEST", "name": "Analyze Refund Health", "config": {}},
        ],
        "governance_policy": {
            "name": "Refund Spike Policy",
            "max_transaction_amount": Decimal("25000.00"),
            "daily_spend_limit": Decimal("50000.00"),
            "require_approval_above": Decimal("5000.00"),
            "blocked_categories": ["cash", "unknown"],
            "allowed_categories": ["refunds", "risk", "reporting"],
            "require_human_approval": True,
            "require_double_confirmation": False,
        },
    },
    {
        "id": "cashflow-forecaster",
        "name": "Cashflow Forecaster",
        "description": "Calculates real-time treasury inflows, pending gateway settlements, planned vendor payouts, and burn rates to project 30-day and 90-day liquidity and runway.",
        "category": "ANALYTICS",
        "automation_level": "AUTONOMOUS",
        "risk_level": "LOW",
        "approval_mode": "AUTO",
        "capabilities": [
            "Settlement pipeline tracking and reconciliation",
            "Historical spend velocity modeling",
            "30-day/90-day runway projection and burn rate analysis",
            "Automated treasury summary report generation",
        ],
        "tools_used": ["getCashflow", "getSettlement", "getOutstandingInvoices", "generateReport"],
        "system_prompt": (
            "You are the Cashflow Forecaster Agent. Analyze gateway settlements, calculate inflows versus projected disbursements, "
            "compute net burn rate, and compile comprehensive cashflow projections for business owners."
        ),
        "triggers": [
            {"trigger_type": "SCHEDULE", "name": "Daily Treasury Forecast", "config": {"cron": "0 8 * * *"}},
            {"trigger_type": "USER_REQUEST", "name": "Run Cashflow Forecast", "config": {}},
        ],
        "governance_policy": {
            "name": "Cashflow Forecaster Guardrail",
            "max_transaction_amount": Decimal("0.00"),
            "daily_spend_limit": Decimal("0.00"),
            "require_approval_above": Decimal("0.00"),
            "allowed_categories": ["analytics", "banking", "invoices", "reporting"],
            "require_human_approval": False,
            "require_double_confirmation": False,
        },
    },
    {
        "id": "receivables-agent",
        "name": "Receivables Agent",
        "description": "Manages accounts receivable ledger, detects aging or overdue customer invoices, sends polite escalation reminders, and generates instant settlement links.",
        "category": "INVOICES",
        "automation_level": "SEMI_AUTONOMOUS",
        "risk_level": "LOW",
        "approval_mode": "AUTO",
        "capabilities": [
            "Aging invoice ledger inspection and categorization",
            "Automated reminder escalation based on overdue days",
            "Embedded payment reconciliation link generation",
            "Customer receivables account status verification",
        ],
        "tools_used": ["getInvoice", "getOutstandingInvoices", "sendNotification", "createPaymentLink"],
        "system_prompt": (
            "You are the Receivables Agent. Review outstanding and overdue invoices, calculate aging days, "
            "generate secure payment links for unsettled balances, and coordinate escalation reminders with customer finance contacts."
        ),
        "triggers": [
            {"trigger_type": "SCHEDULE", "name": "Weekly Receivables Sweep", "config": {"cron": "0 9 * * 1"}},
            {"trigger_type": "USER_REQUEST", "name": "Check Overdue Receivables", "config": {}},
        ],
        "governance_policy": {
            "name": "Receivables Agent Guardrail",
            "max_transaction_amount": Decimal("50000.00"),
            "daily_spend_limit": Decimal("100000.00"),
            "require_approval_above": Decimal("25000.00"),
            "allowed_categories": ["invoices", "communication", "payments"],
            "require_human_approval": False,
            "require_double_confirmation": False,
        },
    },
    {
        "id": "payout-agent",
        "name": "Payout Agent",
        "description": "Governs supplier, vendor, and merchant payouts. Matches approved invoices against treasury balance, validates bank accounts, and gates high-value disbursements through human approvals.",
        "category": "PAYOUTS",
        "automation_level": "HUMAN_IN_THE_LOOP",
        "risk_level": "CRITICAL",
        "approval_mode": "ALWAYS_CONFIRM",
        "capabilities": [
            "Vendor bank account and VPA verification",
            "Invoice-to-payout matching and deduction calculation",
            "Mandatory human approval gating with double confirmation",
            "Real-time banking UTR tracking and status updates",
        ],
        "tools_used": ["createPayout", "getPayout", "getInvoice", "createAlert"],
        "system_prompt": (
            "You are the Payout Agent for RazorHub. Process vendor disbursements strictly according to verified invoices. "
            "Every payout requires explicit human authorization with double confirmation. Never disburse funds without verified beneficiary accounts."
        ),
        "triggers": [
            {"trigger_type": "EVENT", "name": "Invoice Approved Event", "config": {"event": "invoice.approved"}},
            {"trigger_type": "USER_REQUEST", "name": "Disburse Vendor Payout", "config": {}},
        ],
        "governance_policy": {
            "name": "Critical Payout Governance Policy",
            "max_transaction_amount": Decimal("50000.00"),
            "daily_spend_limit": Decimal("100000.00"),
            "require_approval_above": Decimal("1000.00"),
            "blocked_categories": ["cash", "unknown"],
            "allowed_categories": ["payouts", "invoices", "banking"],
            "require_human_approval": True,
            "require_double_confirmation": True,
        },
    },
    {
        "id": "settlement-reconciliation-agent",
        "name": "Settlement Reconciliation Agent",
        "description": "Audits daily payment gateway settlement batches against bank account credits, flags MDR fee and GST variance discrepancies, and generates reconciliation workbooks.",
        "category": "BANKING",
        "automation_level": "AUTONOMOUS",
        "risk_level": "LOW",
        "approval_mode": "AUTO",
        "capabilities": [
            "Payment gateway settlement cycle matching",
            "Fee, GST, and dispute deduction auditing",
            "Unreconciled transaction identification and flagging",
            "Tax and accounting reconciliation summary generation",
        ],
        "tools_used": ["getSettlement", "searchPayments", "generateReport", "createAlert"],
        "system_prompt": (
            "You are the Settlement Reconciliation Agent. Verify each settlement batch from payment gateways against ledger "
            "transactions, confirm gross and net amounts match expected MDR rates, and highlight any unreconciled variance."
        ),
        "triggers": [
            {"trigger_type": "EVENT", "name": "Settlement Processed Event", "config": {"event": "settlement.processed"}},
            {"trigger_type": "USER_REQUEST", "name": "Reconcile Settlements", "config": {}},
        ],
        "governance_policy": {
            "name": "Settlement Reconciliation Policy",
            "max_transaction_amount": Decimal("0.00"),
            "daily_spend_limit": Decimal("0.00"),
            "require_approval_above": Decimal("0.00"),
            "allowed_categories": ["banking", "payments", "reporting", "risk"],
            "require_human_approval": False,
            "require_double_confirmation": False,
        },
    },
    {
        "id": "risk-monitor",
        "name": "Risk Monitor",
        "description": "24/7 autonomous fraud and security sentinel. Detects transaction velocity surges, high-risk merchant destinations, adversarial prompt injection attempts, and chargeback anomalies.",
        "category": "RISK",
        "automation_level": "AUTONOMOUS",
        "risk_level": "HIGH",
        "approval_mode": "AUTO",
        "capabilities": [
            "24/7 transaction velocity and anomaly detection",
            "High-risk beneficiary and merchant blacklisting",
            "Adversarial prompt injection pattern intercepting",
            "Autonomous alert dispatch and security logging",
        ],
        "tools_used": ["createAlert", "searchPayments", "sendNotification", "generateReport"],
        "system_prompt": (
            "You are the Risk Monitor Agent. Inspect real-time transaction velocities, identify suspicious spikes in payment activity, "
            "detect potential chargeback fraud, and raise critical security alerts to safeguard the platform."
        ),
        "triggers": [
            {"trigger_type": "THRESHOLD", "name": "Transaction Velocity > 20/min", "config": {"velocity": 20}},
            {"trigger_type": "USER_REQUEST", "name": "Audit Security Risk", "config": {}},
        ],
        "governance_policy": {
            "name": "Risk Monitor Policy",
            "max_transaction_amount": Decimal("0.00"),
            "daily_spend_limit": Decimal("0.00"),
            "require_approval_above": Decimal("0.00"),
            "allowed_categories": ["risk", "payments", "communication", "reporting"],
            "require_human_approval": False,
            "require_double_confirmation": False,
        },
    },
]


def get_template_by_id(template_id: str) -> Dict[str, Any]:
    for t in PREBUILT_AGENT_TEMPLATES:
        if t["id"] == template_id:
            return t
    raise ValueError(f"Template with id '{template_id}' not found.")
