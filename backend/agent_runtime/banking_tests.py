from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    BusinessInvoice,
    InvoiceFollowUp,
    BookkeepingEntry,
    BusinessFinanceReport,
    Agent,
    AgentAuditLog,
)
from .banking_agents import (
    InsightsAgentService,
    ReceivablesAgentService,
    PayoutAgentService,
    BookkeepingAgentService,
    ReportingAgentService,
    seed_benchmark_banking_data,
)

User = get_user_model()


class AgenticBusinessBankingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="treasury_admin@razorhub.test",
            password="testpassword123",
            username="treasury_admin",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.agent = Agent.objects.create(
            name="Payout & Treasury Agent",
            description="Agent supporting autonomous vendor disbursements and banking",
            system_prompt="You handle banking and payouts.",
            status="ACTIVE",
            approval_mode="AUTO",
            risk_level="LOW",
        )

        seed_benchmark_banking_data()

    def test_insights_agent_calculations(self):
        """Verifies Insights Agent computes treasury balance, runway, burn rate, and forecast."""
        metrics = InsightsAgentService.calculate_treasury_metrics()

        self.assertGreater(metrics["cash_balance"], 0)
        self.assertEqual(metrics["cash_balance"], 2845000.00)
        self.assertEqual(metrics["todays_revenue"], 142500.00)
        self.assertEqual(metrics["weekly_revenue"], 890000.00)
        self.assertEqual(metrics["monthly_revenue"], 3520000.00)
        self.assertGreater(metrics["outstanding_receivables"], 0)
        self.assertGreater(metrics["upcoming_payouts"], 0)
        self.assertEqual(metrics["burn_rate"], 420000.00)
        self.assertEqual(metrics["cash_runway_months"], 6.8)
        self.assertEqual(metrics["payment_success_rate"], 98.4)
        self.assertTrue(len(metrics["cashflow_forecast"]) > 0)

    def test_receivables_agent_overdue_and_followup(self):
        """Verifies Receivables Agent identifies overdue debtors, logs communication, and stops when paid."""
        invoices = ReceivablesAgentService.get_invoices()
        self.assertTrue(len(invoices) >= 2)

        overdue_inv = next((i for i in invoices if i["status"] == "OVERDUE"), None)
        self.assertIsNotNone(overdue_inv)

        # Execute follow-up
        res = ReceivablesAgentService.execute_followup(overdue_inv["id"], channel="EMAIL")
        self.assertTrue(res["success"])
        self.assertEqual(res["follow_up_count"], 1)
        self.assertIn("instant payment link", res["message"])

        # Mark as paid
        paid_res = ReceivablesAgentService.mark_invoice_paid(overdue_inv["id"])
        self.assertTrue(paid_res["success"])
        self.assertEqual(paid_res["status"], "PAID")

        # Second follow-up should now be stopped
        res_stopped = ReceivablesAgentService.execute_followup(overdue_inv["id"], channel="EMAIL")
        self.assertTrue(res_stopped.get("stopped", False))

    def test_payout_agent_resolves_rahul_command(self):
        """Verifies Payout Agent handles 'Pay Rahul ₹18,500 for invoice INV-204'."""
        command = "Pay Rahul ₹18,500 for invoice INV-204"
        res = PayoutAgentService.resolve_payout_request(command, user=self.user)

        self.assertTrue(res["success"])
        self.assertTrue(res["invoice_found"])
        self.assertIn("approval_card", res)

        card = res["approval_card"]
        self.assertEqual(card["invoice_number"], "INV-204")
        self.assertEqual(card["amount"], 18500.00)
        self.assertIn("Rahul", card["recipient_name"])
        self.assertEqual(card["risk_level"], "LOW")
        self.assertEqual(card["status"], "REQUIRES_APPROVAL")

        # Execute Payout post-approval
        exec_res = PayoutAgentService.execute_payout(card["invoice_id"], user=self.user)
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["status"], "DISBURSED")
        self.assertIn("UTR-", exec_res["utr_reference"])

        # Verify invoice is now paid
        inv = BusinessInvoice.objects.get(invoice_number="INV-204")
        self.assertEqual(inv.status, BusinessInvoice.InvoiceStatus.PAID)

        # Verify bookkeeping entry created
        bookkeeping = BookkeepingEntry.objects.filter(transaction_reference="PAYOUT-INV-204").first()
        self.assertIsNotNone(bookkeeping)
        self.assertEqual(bookkeeping.accounting_category, BookkeepingEntry.AccountingCategory.PAYROLL_CONTRACTORS)

        # Verify Audit Log
        audit = AgentAuditLog.objects.filter(details__action="VENDOR_PAYOUT_EXECUTED").first()
        self.assertIsNotNone(audit)

    def test_bookkeeping_agent_categorization(self):
        """Verifies Bookkeeping Agent maps raw entries into chart of accounts."""
        entry_dev = BookkeepingAgentService.categorize_event("TX-01", Decimal("25000.00"), "Software engineer contractor invoice")
        self.assertEqual(entry_dev.accounting_category, BookkeepingEntry.AccountingCategory.PAYROLL_CONTRACTORS)

        entry_cloud = BookkeepingAgentService.categorize_event("TX-02", Decimal("6200.00"), "Render PostgreSQL cloud database subscription")
        self.assertEqual(entry_cloud.accounting_category, BookkeepingEntry.AccountingCategory.CLOUD_INFRASTRUCTURE)

        entry_refund = BookkeepingAgentService.categorize_event("TX-03", Decimal("1999.00"), "Customer return refund for wireless headphones")
        self.assertEqual(entry_refund.accounting_category, BookkeepingEntry.AccountingCategory.REFUND_EXPENSE)

    def test_reporting_agent_generates_reports(self):
        """Verifies Reporting Agent generates daily, weekly, monthly, and anomaly reports."""
        daily = ReportingAgentService.generate_report("DAILY")
        self.assertEqual(daily["report_type"], "DAILY")
        self.assertIn("Daily Finance Pulse", daily["title"])

        weekly = ReportingAgentService.generate_report("WEEKLY")
        self.assertEqual(weekly["report_type"], "WEEKLY")

        monthly = ReportingAgentService.generate_report("MONTHLY")
        self.assertEqual(monthly["report_type"], "MONTHLY")

        anomaly = ReportingAgentService.generate_report("ANOMALY")
        self.assertEqual(anomaly["report_type"], "ANOMALY")
        self.assertTrue(len(anomaly["anomalies"]) > 0)

    def test_banking_api_endpoints(self):
        """Tests REST endpoints for Business Banking module."""
        # 1. Insights
        res_insights = self.client.get("/api/agent-runtime/banking/insights/")
        self.assertEqual(res_insights.status_code, status.HTTP_200_OK)
        self.assertEqual(res_insights.json()["cash_balance"], 2845000.00)

        # 2. Receivables
        res_rec = self.client.get("/api/agent-runtime/banking/receivables/")
        self.assertEqual(res_rec.status_code, status.HTTP_200_OK)
        self.assertTrue(len(res_rec.json()) > 0)

        # 3. Payouts chat
        res_payout_chat = self.client.post(
            "/api/agent-runtime/banking/payouts/chat/",
            {"prompt": "Pay Rahul ₹18,500 for invoice INV-204"},
            format="json",
        )
        self.assertEqual(res_payout_chat.status_code, status.HTTP_200_OK)
        self.assertTrue(res_payout_chat.json()["success"])

        # 4. Bookkeeping
        res_book = self.client.get("/api/agent-runtime/banking/bookkeeping/")
        self.assertEqual(res_book.status_code, status.HTTP_200_OK)

        # 5. Reports
        res_rep = self.client.get("/api/agent-runtime/banking/reports/")
        self.assertEqual(res_rep.status_code, status.HTTP_200_OK)

        # 6. Reconciliation
        res_recon = self.client.get("/api/agent-runtime/banking/reconciliation/")
        self.assertEqual(res_recon.status_code, status.HTTP_200_OK)
        self.assertEqual(res_recon.json()["status"], "RECONCILED")
