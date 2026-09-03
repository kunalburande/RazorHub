import os
from django.test import TestCase
from django.contrib.auth import get_user_model

from .tools.categories import ToolCategory
from .tools.base import BaseTool, ToolExecutionContext, ToolResult
from .tools.registry import ToolRegistry
from .tools.providers.factory import (
    get_payment_provider,
    get_banking_provider,
    get_communication_provider,
    reset_providers,
)
from .tools.providers.mock_payment_provider import MockPaymentProvider
from .tools.providers.razorpay_provider import RazorpayTestProvider
from .tools.implementations import (
    GetPaymentTool,
    SearchPaymentsTool,
    CreatePaymentIntentTool,
    CreatePaymentLinkTool,
    GetPaymentStatusTool,
    GetOrderTool,
    SearchOrdersTool,
    CreateRefundTool,
    GetRefundsTool,
    GetCustomerTool,
    GetInvoiceTool,
    GetOutstandingInvoicesTool,
    CreatePayoutTool,
    GetPayoutTool,
    GetSettlementTool,
    GetCashflowTool,
    GenerateReportTool,
    SendNotificationTool,
    CreateAlertTool,
    ALL_INITIAL_TOOLS,
)
from .models import Agent, AgentStatus, AgentAuditLog, AuditEventType, RiskLevel

User = get_user_model()


class ToolRegistryAndGuardrailTests(TestCase):

    def setUp(self):
        reset_providers()
        self.admin_user = User.objects.create_user(
            username="admin_treasury",
            email="admin@razorhub.local",
            password="password123",
            role="admin",
        )
        self.seller_user = User.objects.create_user(
            username="seller_merchant",
            email="merchant@razorhub.local",
            password="password123",
            role="seller",
        )
        self.customer_user = User.objects.create_user(
            username="regular_customer",
            email="customer@razorhub.local",
            password="password123",
            role="customer",
        )

        self.agent = Agent.objects.create(
            name="Treasury Operations Agent",
            system_prompt="Manage treasury, payments, and payouts.",
            status=AgentStatus.ACTIVE,
        )

    def tearDown(self):
        reset_providers()

    # ── 1. TYPED TOOL INTERFACE & MCP SPEC ─────────────────────────────────────
    def test_typed_tool_interface(self):
        tool = CreatePaymentLinkTool()

        # Required fields & aliases
        self.assertEqual(tool.id, "tool_create_payment_link")
        self.assertEqual(tool.name, "createPaymentLink")
        self.assertIsNotNone(tool.description)
        self.assertEqual(tool.category, ToolCategory.PAYMENTS)
        self.assertEqual(tool.riskLevel, RiskLevel.MEDIUM)
        self.assertFalse(tool.requiresApproval)
        self.assertIsInstance(tool.inputSchema, dict)
        self.assertIsInstance(tool.outputSchema, dict)

        # MCP Schema Export
        mcp_def = tool.to_mcp_tool()
        self.assertEqual(mcp_def["name"], "createPaymentLink")
        self.assertIn("inputSchema", mcp_def)
        self.assertIn("outputSchema", mcp_def)
        self.assertEqual(mcp_def["category"], "PAYMENTS")

        # Global MCP tool list
        mcp_tools = ToolRegistry.list_mcp_tools()
        self.assertEqual(len(mcp_tools), 19)
        names = [t["name"] for t in mcp_tools]
        self.assertIn("createPaymentIntent", names)
        self.assertIn("createPayout", names)
        self.assertIn("getCashflow", names)

    # ── 2. INPUT & OUTPUT VALIDATION ──────────────────────────────────────────
    def test_input_validation(self):
        tool = CreatePaymentIntentTool()

        # Valid input
        valid_input = {"amount": 2500.0, "currency": "INR"}
        res = tool.validateInput(valid_input)
        self.assertEqual(res["amount"], 2500.0)

        # Missing required parameter ('amount')
        with self.assertRaises(ValueError) as ctx:
            tool.validateInput({"currency": "INR"})
        self.assertIn("Missing required parameter 'amount'", str(ctx.exception))

        # Invalid type for numeric parameter
        with self.assertRaises(ValueError) as ctx:
            tool.validateInput({"amount": "five_hundred"})
        self.assertIn("must be numeric", str(ctx.exception))

    # ── 3. 12 CATEGORIES COVERAGE ─────────────────────────────────────────────
    def test_tool_categories_filtering(self):
        all_categories = [
            ToolCategory.PAYMENTS,
            ToolCategory.ORDERS,
            ToolCategory.CUSTOMERS,
            ToolCategory.REFUNDS,
            ToolCategory.INVOICES,
            ToolCategory.SUBSCRIPTIONS,
            ToolCategory.BANKING,
            ToolCategory.PAYOUTS,
            ToolCategory.REPORTING,
            ToolCategory.COMMUNICATION,
            ToolCategory.ANALYTICS,
            ToolCategory.RISK,
        ]
        self.assertEqual(len(all_categories), 12)

        # Filter by PAYMENTS
        payment_tools = ToolRegistry.list_tools(category=ToolCategory.PAYMENTS)
        self.assertTrue(len(payment_tools) >= 5)
        for t in payment_tools:
            self.assertEqual(t.category, ToolCategory.PAYMENTS)

        # Filter by PAYOUTS
        payout_tools = ToolRegistry.list_tools(category=ToolCategory.PAYOUTS)
        self.assertTrue(len(payout_tools) >= 2)
        for t in payout_tools:
            self.assertEqual(t.category, ToolCategory.PAYOUTS)

    # ── 4. FINANCIAL MUTATION: PERMISSION CHECK ───────────────────────────────
    def test_financial_mutation_permission_check(self):
        tool = CreatePayoutTool()

        # Customer role attempting to disburse payout -> Prohibited
        ctx_unauth = ToolExecutionContext(user=self.customer_user, agent=self.agent)
        res_unauth = tool.run_with_guardrails(
            {"recipient_account": "ACC_VEND_99", "amount": 1000.0},
            ctx_unauth,
        )
        self.assertFalse(res_unauth.success)
        self.assertIn("not authorized", res_unauth.error)

        # Admin user -> Authorized
        ctx_auth = ToolExecutionContext(user=self.admin_user, agent=self.agent, is_pre_approved=True)
        res_auth = tool.run_with_guardrails(
            {"recipient_account": "ACC_VEND_99", "amount": 1000.0},
            ctx_auth,
        )
        self.assertTrue(res_auth.success)
        self.assertEqual(res_auth.result["status"], "queued")

    # ── 5. FINANCIAL MUTATION: AMOUNT LIMIT CHECK ──────────────────────────────
    def test_financial_mutation_amount_limit(self):
        tool = CreatePaymentIntentTool()  # Ceiling is ₹1,00,000

        ctx = ToolExecutionContext(user=self.seller_user, agent=self.agent)

        # Attempt ₹1,50,000 intent -> Blocked by ceiling
        res_overflow = tool.run_with_guardrails(
            {"amount": 150000.0, "currency": "INR"},
            ctx,
        )
        self.assertFalse(res_overflow.success)
        self.assertIn("exceeds tool hard ceiling", res_overflow.error)

        # Custom agent limit of ₹10,000
        ctx_restricted = ToolExecutionContext(
            user=self.seller_user,
            agent=self.agent,
            custom_limits={"max_amount": 10000.0},
        )
        res_agent_cap = tool.run_with_guardrails(
            {"amount": 15000.0, "currency": "INR"},
            ctx_restricted,
        )
        self.assertFalse(res_agent_cap.success)
        self.assertIn("exceeds agent limit", res_agent_cap.error)

    # ── 6. FINANCIAL MUTATION: IDEMPOTENCY KEY DEDUPLICATION ──────────────────
    def test_financial_mutation_idempotency(self):
        tool = CreatePaymentLinkTool()
        key = "idemp_test_uuid_9999"

        ctx = ToolExecutionContext(user=self.seller_user, agent=self.agent)
        payload = {
            "amount": 2500.0,
            "currency": "INR",
            "customer_email": "client@example.com",
            "description": "Invoice Settlement",
            "idempotency_key": key,
        }

        # 1st Execution
        res1 = tool.run_with_guardrails(payload, ctx)
        self.assertTrue(res1.success)
        self.assertFalse(res1.is_idempotent_replay)
        link_id_1 = res1.result["id"]

        # 2nd Execution with same idempotency_key
        res2 = tool.run_with_guardrails(payload, ctx)
        self.assertTrue(res2.success)
        self.assertTrue(res2.is_idempotent_replay)
        link_id_2 = res2.result["id"]

        # Exact same link returned without double creation
        self.assertEqual(link_id_1, link_id_2)

    # ── 7. FINANCIAL MUTATION: APPROVAL REQUIREMENT ────────────────────────────
    def test_financial_mutation_approval_requirement(self):
        tool = CreateRefundTool()  # requires_approval = True

        ctx = ToolExecutionContext(user=self.admin_user, agent=self.agent, is_pre_approved=False)
        payload = {"payment_id": "pay_mock_1001", "amount": 2999.0}

        # First run requires approval
        res = tool.run_with_guardrails(payload, ctx)
        self.assertFalse(res.success)
        self.assertTrue(res.approval_required)
        self.assertIn("require approval", res.approval_reason)

        # Pre-approved execution succeeds
        ctx_approved = ToolExecutionContext(user=self.admin_user, agent=self.agent, is_pre_approved=True)
        res_approved = tool.run_with_guardrails(payload, ctx_approved)
        self.assertTrue(res_approved.success)
        self.assertEqual(res_approved.result["status"], "processed")

    # ── 8. FINANCIAL MUTATION: AUDIT LOGGING ──────────────────────────────────
    def test_financial_mutation_audit_logging(self):
        tool = CreateAlertTool()
        ctx = ToolExecutionContext(user=self.admin_user, agent=self.agent)

        initial_count = AgentAuditLog.objects.filter(agent=self.agent).count()

        res = tool.run_with_guardrails(
            {
                "title": "High Velocity Transaction Spike",
                "description": "Exceeded 50 transactions in 1 minute",
                "severity": "CRITICAL",
            },
            ctx,
        )
        self.assertTrue(res.success)

        final_count = AgentAuditLog.objects.filter(agent=self.agent).count()
        self.assertEqual(final_count, initial_count + 1)

        log = AgentAuditLog.objects.filter(agent=self.agent).latest("timestamp")
        self.assertEqual(log.event_type, AuditEventType.TOOL_EXECUTED)
        self.assertEqual(log.details["tool"], "createAlert")

    # ── 9. DEPENDENCY INJECTION & OFFLINE RESILIENCE ───────────────────────────
    def test_dependency_injection_provider_switching(self):
        # 1. Default / Mock Provider
        os.environ["PAYMENT_PROVIDER"] = "mock"
        reset_providers()
        provider = get_payment_provider()
        self.assertIsInstance(provider, MockPaymentProvider)

        # 2. Switch to Razorpay Test Provider
        os.environ["PAYMENT_PROVIDER"] = "razorpay_test"
        reset_providers()
        provider_rzp = get_payment_provider()
        self.assertIsInstance(provider_rzp, RazorpayTestProvider)

        # 3. Offline execution resilience across all 19 tools
        os.environ["PAYMENT_PROVIDER"] = "mock"
        reset_providers()

        ctx = ToolExecutionContext(user=self.admin_user, agent=self.agent, is_pre_approved=True)

        tool_execs = [
            ("getPayment", {"payment_id": "pay_mock_1001"}),
            ("searchPayments", {"status": "captured"}),
            ("getOrder", {"order_id": 1}),
            ("searchOrders", {"status": "pending"}),
            ("createPaymentIntent", {"amount": 500.0, "currency": "INR"}),
            ("createPaymentLink", {"amount": 500.0, "customer_email": "a@b.com"}),
            ("getPaymentStatus", {"payment_id": "pay_mock_1001"}),
            ("createRefund", {"payment_id": "pay_mock_1001", "amount": 100.0}),
            ("getRefunds", {}),
            ("getCustomer", {"email": "buyer@example.com"}),
            ("getInvoice", {"invoice_id": "INV-1"}),
            ("getOutstandingInvoices", {}),
            ("createPayout", {"recipient_account": "ACC_1", "amount": 250.0}),
            ("getPayout", {"payout_id": "pout_1"}),
            ("getSettlement", {}),
            ("getCashflow", {}),
            ("sendNotification", {"recipient": "user@ex.com", "message": "Notice"}),
            ("generateReport", {"report_type": "reconciliation"}),
            ("createAlert", {"title": "Test Alert", "description": "Desc"}),
        ]

        for name, args in tool_execs:
            result = ToolRegistry.execute(name, args, ctx)
            self.assertTrue(
                result.success,
                f"Tool '{name}' failed with error: {result.error}",
            )
            self.assertIsNotNone(result.result)
