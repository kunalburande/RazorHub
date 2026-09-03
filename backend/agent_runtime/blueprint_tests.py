from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .blueprint import (
    AgentBlueprintService,
    DeterministicBlueprintGenerator,
    AgentBlueprint,
    ALLOWED_MCP_TOOLS,
)
from .models import Agent, AgentGovernancePolicy, AgentTrigger, AgentTool, AgentStatus

User = get_user_model()


class BlueprintArchitectureTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="architect_tester",
            email="tester@razorhub.com",
            password="Password123!",
        )
        self.client.force_authenticate(user=self.user)

    def test_refund_spike_blueprint_generation(self):
        """
        User request: 'Build me an agent that detects unusual refund spikes and alerts me.'
        Must generate a structured AgentBlueprint matching expected schema.
        """
        prompt = "Build me an agent that detects unusual refund spikes and alerts me."
        res = AgentBlueprintService.generate(prompt)

        self.assertIn("blueprint", res)
        self.assertIn("ai_message", res)
        self.assertIn("source", res)

        bp = res["blueprint"]
        self.assertIn("name", bp)
        self.assertIn("trigger", bp)
        self.assertIn("dataSources", bp)
        self.assertIn("tools", bp)
        self.assertIn("logic", bp)
        self.assertIn("conditions", bp)
        self.assertIn("actions", bp)
        self.assertIn("riskLevel", bp)
        self.assertIn("approvalMode", bp)
        self.assertIn("guardrails", bp)

        # Ensure tools are within ALLOWED_MCP_TOOLS
        for tool in bp["tools"]:
            self.assertIn(tool, ALLOWED_MCP_TOOLS)

        # Validate refund content
        self.assertTrue("refund" in bp["name"].lower() or "spike" in bp["name"].lower())
        self.assertIn("refunds", bp["dataSources"])
        self.assertTrue(any("alert" in a.lower() for a in bp["actions"]))

    def test_deterministic_fallback_when_llm_fails(self):
        """
        Deterministic template fallback produces compliant blueprints for payments, cart, cashflow, etc.
        """
        bp_payment = DeterministicBlueprintGenerator.generate("Create an automated failed payment dunning agent")
        self.assertIn("createPaymentLink", bp_payment.tools)
        self.assertIn("payments", bp_payment.dataSources)

        bp_cart = DeterministicBlueprintGenerator.generate("Recover abandoned shopping carts with discounts")
        self.assertIn("createPaymentLink", bp_cart.tools)
        self.assertIn("orders", bp_cart.dataSources)

        bp_payout = DeterministicBlueprintGenerator.generate("Manage vendor payouts with human double confirmation")
        self.assertEqual(bp_payout.approvalMode, "always_confirm")
        self.assertTrue(bp_payout.guardrails["requireDoubleConfirmation"])

    def test_no_arbitrary_code_allowed(self):
        """
        Input attempting to inject code or malicious tool names is strictly sanitized.
        """
        raw_malicious = {
            "name": "Exploit Agent",
            "tools": ["rm -rf /", "DROP TABLE users;", "getRefunds", "__import__('os').system('whoami')"],
            "dataSources": ["payments", "internal_passwords"],
            "riskLevel": "INVALID_LEVEL",
            "approvalMode": "BYPASS_ALL",
            "guardrails": {"maxTransactionAmount": 999999999},
        }
        sanitized = AgentBlueprintService._sanitize_and_validate(raw_malicious, "Exploit attempt")

        # Only valid registered MCP tools remain
        self.assertEqual(sanitized.tools, ["getRefunds"])
        self.assertEqual(sanitized.dataSources, ["payments"])
        self.assertIn(sanitized.riskLevel, ["low", "medium", "high", "critical"])
        self.assertIn(sanitized.approvalMode, ["auto", "review_required", "always_confirm", "blocked"])

    def test_blueprint_provisioning_to_database(self):
        """
        Provisioning creates real Agent, AgentGovernancePolicy, AgentTrigger, and AgentVersion rows.
        """
        bp = DeterministicBlueprintGenerator.generate("Build me an agent that detects unusual refund spikes and alerts me.")
        agent = AgentBlueprintService.provision_blueprint(
            blueprint_data=bp.to_dict(),
            status="ACTIVE",
            user=self.user,
        )

        self.assertIsNotNone(agent.id)
        self.assertEqual(agent.status, AgentStatus.ACTIVE)
        self.assertTrue(hasattr(agent, "governance_policy"))
        self.assertEqual(agent.governance_policy.max_transaction_amount, 25000.00)
        self.assertGreaterEqual(agent.tools.count(), 1)
        self.assertGreaterEqual(agent.triggers.count(), 1)
        self.assertGreaterEqual(agent.versions.count(), 1)

    def test_blueprint_api_endpoints(self):
        """
        Tests POST /api/agent-runtime/blueprint/generate/ and POST /api/agent-runtime/blueprint/activate/.
        """
        # 1. Generate
        gen_res = self.client.post(
            "/api/agent-runtime/blueprint/generate/",
            {"message": "Build me an agent that detects unusual refund spikes and alerts me."},
            format="json",
        )
        self.assertEqual(gen_res.status_code, status.HTTP_200_OK)
        bp_data = gen_res.data["blueprint"]

        # 2. Activate without confirmation -> 428 Precondition Required
        act_res_fail = self.client.post(
            "/api/agent-runtime/blueprint/activate/",
            {"blueprint": bp_data, "activate": True, "confirmation": False},
            format="json",
        )
        self.assertEqual(act_res_fail.status_code, status.HTTP_428_PRECONDITION_REQUIRED)

        # 3. Activate with confirmation -> 201 Created
        act_res_ok = self.client.post(
            "/api/agent-runtime/blueprint/activate/",
            {"blueprint": bp_data, "activate": True, "confirmation": True},
            format="json",
        )
        self.assertEqual(act_res_ok.status_code, status.HTTP_201_CREATED)
        self.assertEqual(act_res_ok.data["status"], "ACTIVE")

        # 4. Save as Draft -> 201 Created with status DRAFT
        draft_res = self.client.post(
            "/api/agent-runtime/blueprint/activate/",
            {"blueprint": bp_data, "activate": False, "confirmation": False},
            format="json",
        )
        self.assertEqual(draft_res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(draft_res.data["status"], "DRAFT")
