from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    Agent,
    AgentGovernancePolicy,
    GovernanceDecision,
    GovernanceDecisionRecord,
    FinancialRiskRecord,
    FinancialRiskLevel,
)
from .risk import FinancialRiskEngine
from .governance import TransactionGovernanceFirewall

User = get_user_model()


class FinancialRiskEngineTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="risk_analyst@razorhub.test",
            password="testpassword123",
            username="risk_analyst",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.agent = Agent.objects.create(
            name="Treasury & Payment Agent",
            description="Agent handling disbursements and payments",
            system_prompt="Execute payment orders securely",
            status="ACTIVE",
        )
        self.policy = AgentGovernancePolicy.objects.create(
            agent=self.agent,
            name="Standard Treasury Governance",
            max_transaction_amount=Decimal("50000.00"),
            daily_spend_limit=Decimal("100000.00"),
            weekly_spend_limit=Decimal("500000.00"),
            monthly_spend_limit=Decimal("2000000.00"),
            require_approval_above=Decimal("25000.00"),
            allowed_categories=["PAYMENTS", "UTILITIES", "SERVICES"],
            blocked_categories=["CASH", "GAMBLING"],
        )

    def test_exact_user_prompt_scenario(self):
        """
        Verifies exact prompt example:
        riskScore: 82
        riskLevel: HIGH
        reasons:
        - amount 4.2x customer average
        - 7 failed attempts in 10 minutes
        - new device
        - new merchant
        - unusual category
        """
        inputs = {
            "transaction_amount": 21000.0,
            "customer_avg_amount": 5000.0,  # 21000 / 5000 = 4.2x
            "failed_attempts": 7,
            "device": {"is_new_device": True},
            "merchant_history": {"is_new": True},
            "category": "crypto",
        }

        result = FinancialRiskEngine.evaluate(inputs)

        self.assertEqual(result["riskScore"], 82)
        self.assertEqual(result["riskLevel"], "HIGH")
        self.assertFalse(result["critical_rule_triggered"])

        expected_reasons = [
            "amount 4.2x customer average",
            "7 failed attempts in 10 minutes",
            "new device",
            "new merchant",
            "unusual category",
        ]
        for expected in expected_reasons:
            self.assertIn(expected, result["reasons"])

    def test_low_risk_regular_transaction(self):
        """Clean transaction produces LOW risk score under 30 with no critical triggers."""
        inputs = {
            "transaction_amount": 1200.0,
            "customer_avg_amount": 1500.0,
            "customer_age_days": 180,
            "failed_attempts": 0,
            "device": {"is_new_device": False, "is_vpn_proxy": False},
            "merchant_history": {"is_new": False, "total_transactions": 45, "dispute_rate": 0.0},
            "category": "groceries",
            "location": {"current_country": "IN", "home_country": "IN", "is_impossible_travel": False},
        }

        result = FinancialRiskEngine.evaluate(inputs)
        self.assertLess(result["riskScore"], 30)
        self.assertEqual(result["riskLevel"], "LOW")
        self.assertFalse(result["critical_rule_triggered"])
        self.assertEqual(len(result["reasons"]), 0)

    def test_critical_rule_impossible_travel(self):
        """Impossible travel hard-clamps score to >= 85 and forces CRITICAL level."""
        inputs = {
            "transaction_amount": 500.0,
            "location": {
                "is_impossible_travel": True,
                "distance_km": 4800,
                "current_country": "RU",
                "home_country": "IN",
            },
        }

        result = FinancialRiskEngine.evaluate(inputs)
        self.assertTrue(result["critical_rule_triggered"])
        self.assertGreaterEqual(result["riskScore"], 85)
        self.assertEqual(result["riskLevel"], "CRITICAL")
        self.assertTrue(any("impossible travel" in r for r in result["reasons"]))

    def test_critical_rule_excessive_failed_attempts(self):
        """Brute-force attempts >= 10 triggers CRITICAL risk level."""
        inputs = {
            "transaction_amount": 2500.0,
            "failed_attempts": 11,
        }

        result = FinancialRiskEngine.evaluate(inputs)
        self.assertTrue(result["critical_rule_triggered"])
        self.assertGreaterEqual(result["riskScore"], 85)
        self.assertEqual(result["riskLevel"], "CRITICAL")

    def test_critical_rule_excessive_chargebacks(self):
        """Customer with >= 5 chargebacks is flagged as CRITICAL risk."""
        inputs = {
            "transaction_amount": 3500.0,
            "chargeback_history": {"chargeback_count": 6, "chargeback_rate": 0.15},
        }

        result = FinancialRiskEngine.evaluate(inputs)
        self.assertTrue(result["critical_rule_triggered"])
        self.assertGreaterEqual(result["riskScore"], 85)
        self.assertEqual(result["riskLevel"], "CRITICAL")

    def test_llm_cannot_override_critical_rule(self):
        """Verifies requirement: 'The LLM must never override CRITICAL deterministic rules.'"""
        inputs = {
            "transaction_amount": 500.0,
            "location": {"is_impossible_travel": True, "distance_km": 4800},
        }

        result = FinancialRiskEngine.evaluate(inputs, include_llm_explanation=True)
        # Even with LLM narrative generation requested, score and level remain strictly deterministic
        self.assertTrue(result["critical_rule_triggered"])
        self.assertGreaterEqual(result["riskScore"], 85)
        self.assertEqual(result["riskLevel"], "CRITICAL")
        self.assertIn("[CRITICAL SECURITY INTERVENTION]", result["explanation"])

    def test_transaction_governance_firewall_denies_critical_risk(self):
        """Transaction Governance Firewall denies mutations with CRITICAL risk level."""
        res = TransactionGovernanceFirewall.evaluate(
            agent=self.agent,
            tool_name="createPaymentIntent",
            arguments={
                "amount": 4500.0,
                "location": {"is_impossible_travel": True, "distance_km": 5200},
                "category": "PAYMENTS",
            },
            raw_prompt="Send payment",
            user=self.user,
        )

        self.assertEqual(res.decision, GovernanceDecision.DENY)
        self.assertFalse(res.allowed)
        self.assertIn("CRITICAL", res.reason)

        # Check recorded in GovernanceDecisionRecord and FinancialRiskRecord
        record = GovernanceDecisionRecord.objects.filter(agent=self.agent, decision=GovernanceDecision.DENY).latest("created_at")
        self.assertIn("CRITICAL", record.reason)

        risk_rec = FinancialRiskRecord.objects.filter(user=self.user, risk_level="CRITICAL").latest("created_at")
        self.assertTrue(risk_rec.critical_rule_triggered)

    def test_transaction_governance_firewall_high_risk_requires_confirmation(self):
        """High risk score requires human supervisor approval and double confirmation."""
        res = TransactionGovernanceFirewall.evaluate(
            agent=self.agent,
            tool_name="createPaymentIntent",
            arguments={
                "amount": 21000.0,
                "customer_avg_amount": 5000.0,
                "failed_attempts": 7,
                "device": {"is_new_device": True},
                "merchant_history": {"is_new": True},
                "category": "PAYMENTS",
            },
            raw_prompt="Pay vendor",
            user=self.user,
        )

        self.assertEqual(res.decision, GovernanceDecision.ALLOW_WITH_CONFIRMATION)
        self.assertTrue(res.requires_human_approval)
        self.assertTrue(res.requires_double_confirmation)

    def test_rest_api_risk_evaluate_and_history(self):
        """Verifies REST endpoints for risk evaluation and audit history."""
        # 1. POST evaluate
        res = self.client.post(
            "/api/agent-runtime/risk/evaluate/",
            {
                "inputs": {
                    "transaction_amount": 21000.0,
                    "customer_avg_amount": 5000.0,
                    "failed_attempts": 7,
                    "device": {"is_new_device": True},
                    "merchant_history": {"is_new": True},
                    "category": "crypto",
                },
                "include_llm_explanation": False,
                "save_record": True,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["riskScore"], 82)
        self.assertEqual(data["riskLevel"], "HIGH")
        self.assertIn("record_id", data)

        # 2. GET history
        hist_res = self.client.get("/api/agent-runtime/risk/history/")
        self.assertEqual(hist_res.status_code, status.HTTP_200_OK)
        records = hist_res.json()
        self.assertTrue(len(records) > 0)
        self.assertEqual(records[0]["risk_score"], 82)
