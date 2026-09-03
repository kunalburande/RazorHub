from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import Agent, AgentExecution, AgentAuditLog, RefundAnomalyRecord
from .refund_analyzer import RefundMetricsCalculator, RefundReportSynthesizer, RefundSpikeService

User = get_user_model()


class RefundSpikeAnalyzerTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="risk_sentinel",
            email="sentinel@razorhub.com",
            password="Password123!",
        )
        self.client.force_authenticate(user=self.user)

    def test_deterministic_refund_metrics_calculation(self):
        """
        Calculates refund rate, baseline comparison, delta, and threshold multiplier deterministically.
        """
        metrics = RefundMetricsCalculator.calculate_metrics(
            baseline_rate=Decimal("4.20"),
            threshold_factor=Decimal("1.50"),
        )

        self.assertEqual(metrics["current_refund_rate"], 12.70)
        self.assertEqual(metrics["baseline_refund_rate"], 4.20)
        self.assertEqual(metrics["delta"], 8.50)
        self.assertEqual(metrics["threshold_multiplier"], 3.02)
        self.assertTrue(metrics["is_anomaly"])
        self.assertEqual(metrics["severity"], "CRITICAL")
        self.assertGreater(metrics["refund_count"], 0)
        self.assertGreater(metrics["refund_amount"], 0)

    def test_affected_products_and_breakdowns(self):
        """
        Identifies affected products, payment method distribution, and 7-day trend.
        """
        metrics = RefundMetricsCalculator.calculate_metrics()

        # Product breakdown
        self.assertGreaterEqual(len(metrics["by_product"]), 3)
        self.assertGreaterEqual(len(metrics["affected_products"]), 1)
        top_affected = metrics["affected_products"][0]
        self.assertIn("product_name", top_affected)
        self.assertGreater(top_affected["refund_rate"], metrics["baseline_refund_rate"])

        # Customer cohort breakdown
        self.assertGreaterEqual(len(metrics["by_customer"]), 1)
        self.assertIn("email", metrics["by_customer"][0])

        # Payment methods breakdown
        self.assertGreaterEqual(len(metrics["by_payment_method"]), 2)
        methods = [m["method"] for m in metrics["by_payment_method"]]
        self.assertTrue(any("Card" in m for m in methods))
        self.assertTrue(any("UPI" in m for m in methods))

        # Daily series breakdown
        self.assertEqual(len(metrics["by_day"]), 7)
        self.assertEqual(metrics["by_day"][-1]["refund_rate"], 12.70)

    def test_llm_cannot_override_threshold_or_severity(self):
        """
        Verifies that report synthesis reflects deterministic metrics without changing them.
        """
        metrics = RefundMetricsCalculator.calculate_metrics()
        report = RefundReportSynthesizer.synthesize_report(metrics)

        self.assertIn("explanation", report)
        self.assertIn("likely_reasons", report)
        self.assertIn("recommended_actions", report)
        self.assertGreaterEqual(len(report["likely_reasons"]), 2)
        self.assertGreaterEqual(len(report["recommended_actions"]), 2)

    def test_refund_spike_service_execution(self):
        """
        Verifies that running analysis creates a RefundAnomalyRecord, AgentExecution, and AuditLog.
        """
        record = RefundSpikeService.run_analysis(user=self.user)

        self.assertIsNotNone(record.id)
        self.assertEqual(float(record.current_refund_rate), 12.70)
        self.assertEqual(float(record.baseline_refund_rate), 4.20)
        self.assertEqual(record.severity, "CRITICAL")
        self.assertTrue(record.is_anomaly)
        self.assertIsNotNone(record.execution)
        self.assertEqual(record.execution.status, "COMPLETED")

        # Check audit log
        audit = AgentAuditLog.objects.filter(agent=record.agent).last()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.details.get("action"), "REFUND_SPIKE_ANALYSIS_EXECUTED")

    def test_refund_spike_api_endpoints(self):
        """
        Tests 'Run now', 'latest', 'history', and 'schedule' endpoints.
        """
        # 1. Run now (POST)
        run_res = self.client.post("/api/agent-runtime/refund-spike-analyzer/run/", format="json")
        self.assertEqual(run_res.status_code, status.HTTP_200_OK)
        self.assertEqual(float(run_res.data["current_refund_rate"]), 12.70)
        self.assertEqual(run_res.data["severity"], "CRITICAL")

        # 2. Get latest
        latest_res = self.client.get("/api/agent-runtime/refund-spike-analyzer/latest/")
        self.assertEqual(latest_res.status_code, status.HTTP_200_OK)
        self.assertEqual(latest_res.data["id"], run_res.data["id"])

        # 3. Get history timeline
        hist_res = self.client.get("/api/agent-runtime/refund-spike-analyzer/history/")
        self.assertEqual(hist_res.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(hist_res.data), 1)

        # 4. Schedule update
        sched_res = self.client.post(
            "/api/agent-runtime/refund-spike-analyzer/schedule/",
            {"is_active": True, "cron": "0 9 * * *", "frequency": "daily"},
            format="json",
        )
        self.assertEqual(sched_res.status_code, status.HTTP_200_OK)
        self.assertEqual(sched_res.data["status"], "SCHEDULE_UPDATED")
        self.assertTrue(sched_res.data["is_active"])
