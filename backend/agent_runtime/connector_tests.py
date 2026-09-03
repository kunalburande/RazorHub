from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework.exceptions import PermissionDenied

from .models import Connector, ConnectorCapability, ConnectorExecution, Agent
from .connectors.registry import ConnectorRegistry

User = get_user_model()


class ConnectorArchitectureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="connector_admin@razorhub.test",
            password="testpassword123",
            username="connector_admin",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.agent = Agent.objects.create(
            name="Treasury Operations Agent",
            description="Agent for handling payouts and invoicing",
            system_prompt="Manage corporate treasury",
            status="ACTIVE",
        )

        ConnectorRegistry.seed_default_connectors()

    def test_seed_default_connectors(self):
        """Verifies all 10 connectors and their capabilities are seeded correctly."""
        connectors = Connector.objects.all()
        self.assertGreaterEqual(connectors.count(), 10)

        slugs = list(connectors.values_list("slug", flat=True))
        expected_slugs = [
            "mock-commerce",
            "mock-payment",
            "mock-banking",
            "mock-accounting",
            "mock-email",
            "mock-whatsapp",
            "razorpay-test",
            "google-sheets",
            "gmail",
            "telegram",
        ]
        for s in expected_slugs:
            self.assertIn(s, slugs)

        # Check capabilities
        banking_conn = Connector.objects.get(slug="mock-banking")
        caps = list(banking_conn.capabilities.values_list("capability", flat=True))
        self.assertIn("READ", caps)
        self.assertIn("CREATE", caps)
        self.assertIn("UPDATE", caps)

    def test_agent_unauthorized_connector_access_blocked(self):
        """
        Verifies rule: 'Do not allow an agent to access every connector by default.
        Agent configuration must specify which connectors an agent is allowed to use.'
        """
        # self.agent has no connectors attached
        self.assertEqual(self.agent.connectors.count(), 0)

        with self.assertRaises(PermissionDenied):
            ConnectorRegistry.execute(
                connector_slug="mock-banking",
                capability="READ",
                action="get_balance",
                params={},
                agent_id=str(self.agent.id),
            )

        # Verify execution record logged the policy block
        latest_exec = ConnectorExecution.objects.latest("created_at")
        self.assertEqual(latest_exec.status, "BLOCKED_BY_POLICY")
        self.assertIn("Access Prohibited", latest_exec.error_message)

    def test_agent_authorized_connector_access_succeeds(self):
        """Verifies configured agent successfully invokes authorized connector."""
        banking_conn = Connector.objects.get(slug="mock-banking")
        self.agent.connectors.add(banking_conn)

        res = ConnectorRegistry.execute(
            connector_slug="mock-banking",
            capability="READ",
            action="get_balance",
            params={},
            agent_id=str(self.agent.id),
        )

        self.assertEqual(res["feed_status"], "ONLINE")
        self.assertEqual(res["available_balance"], 2845000.00)

        # Verify execution record logged success
        latest_exec = ConnectorExecution.objects.latest("created_at")
        self.assertEqual(latest_exec.status, "SUCCESS")
        self.assertEqual(latest_exec.action_name, "get_balance")
        self.assertEqual(latest_exec.agent, self.agent)

    def test_capability_validation(self):
        """Verifies invoking an unsupported capability raises ValueError."""
        email_conn = Connector.objects.get(slug="mock-email")
        self.agent.connectors.add(email_conn)

        # MockEmailConnector only supports SEND, not DELETE
        with self.assertRaises(ValueError):
            ConnectorRegistry.execute(
                connector_slug="mock-email",
                capability="DELETE",
                action="delete_email",
                params={},
                agent_id=str(self.agent.id),
            )

    def test_mock_commerce_connector(self):
        """Tests MockCommerceConnector operations: READ products & CREATE cart."""
        comm_conn = Connector.objects.get(slug="mock-commerce")
        self.agent.connectors.add(comm_conn)

        # 1. READ products
        products_res = ConnectorRegistry.execute(
            connector_slug="mock-commerce",
            capability="READ",
            action="get_products",
            params={},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(products_res["count"], 3)

        # 2. CREATE cart
        cart_res = ConnectorRegistry.execute(
            connector_slug="mock-commerce",
            capability="CREATE",
            action="create_cart",
            params={"items": ["PROD-1"], "total": 1499.0},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(cart_res["status"], "ACTIVE")
        self.assertIn("CART-", cart_res["cart_id"])

    def test_mock_payment_connector(self):
        """Tests MockPaymentConnector operations: CREATE intent & WRITE refund."""
        pay_conn = Connector.objects.get(slug="mock-payment")
        self.agent.connectors.add(pay_conn)

        # 1. CREATE payment intent
        intent_res = ConnectorRegistry.execute(
            connector_slug="mock-payment",
            capability="CREATE",
            action="create_payment_intent",
            params={"amount": 4999.0},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(intent_res["status"], "REQUIRES_CONFIRMATION")
        self.assertEqual(intent_res["amount"], 4999.0)

        # 2. WRITE refund
        refund_res = ConnectorRegistry.execute(
            connector_slug="mock-payment",
            capability="WRITE",
            action="create_refund",
            params={"amount": 1000.0},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(refund_res["status"], "REFUNDED")

    def test_mock_accounting_connector(self):
        """Tests MockAccountingConnector operations: READ accounts & CREATE journal entry."""
        acc_conn = Connector.objects.get(slug="mock-accounting")
        self.agent.connectors.add(acc_conn)

        je_res = ConnectorRegistry.execute(
            connector_slug="mock-accounting",
            capability="CREATE",
            action="create_journal_entry",
            params={"category": "PAYROLL_CONTRACTORS", "amount": 18500.0},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(je_res["status"], "POSTED")

    def test_communication_connectors(self):
        """Tests MockEmailConnector & MockWhatsAppConnector SEND capability."""
        email_conn = Connector.objects.get(slug="mock-email")
        wa_conn = Connector.objects.get(slug="mock-whatsapp")
        self.agent.connectors.add(email_conn, wa_conn)

        # Email SEND
        email_res = ConnectorRegistry.execute(
            connector_slug="mock-email",
            capability="SEND",
            action="send_email",
            params={"recipient": "vendor@test.com"},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(email_res["status"], "DELIVERED")

        # WhatsApp SEND
        wa_res = ConnectorRegistry.execute(
            connector_slug="mock-whatsapp",
            capability="SEND",
            action="send_whatsapp_message",
            params={"phone": "+919988776655"},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(wa_res["status"], "SENT_AND_DELIVERED")

    def test_external_connectors(self):
        """Tests RazorpayTestModeConnector, GoogleSheetsConnector, Gmail, and Telegram."""
        rzp_conn = Connector.objects.get(slug="razorpay-test")
        sheets_conn = Connector.objects.get(slug="google-sheets")
        gmail_conn = Connector.objects.get(slug="gmail")
        tg_conn = Connector.objects.get(slug="telegram")
        self.agent.connectors.add(rzp_conn, sheets_conn, gmail_conn, tg_conn)

        rzp_res = ConnectorRegistry.execute(
            connector_slug="razorpay-test",
            capability="CREATE",
            action="create_order",
            params={"amount": 50000},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(rzp_res["mode"], "TEST_SANDBOX")

        sheets_res = ConnectorRegistry.execute(
            connector_slug="google-sheets",
            capability="WRITE",
            action="append_row",
            params={"spreadsheet_id": "treasury_2026"},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(sheets_res["status"], "SYNCHRONIZED")

        gmail_res = ConnectorRegistry.execute(
            connector_slug="gmail",
            capability="SEND",
            action="send_draft",
            params={"to": "client@corp.test"},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(gmail_res["status"], "SENT_VIA_GMAIL_API")

        tg_res = ConnectorRegistry.execute(
            connector_slug="telegram",
            capability="SEND",
            action="send_channel_alert",
            params={"chat_id": "@finance_alerts"},
            agent_id=str(self.agent.id),
        )
        self.assertEqual(tg_res["status"], "DISPATCHED_TO_CHANNEL")

    def test_rest_api_connectors_and_agent_configuration(self):
        """Verifies REST endpoints for listing connectors, testing capability, and updating agent connectors."""
        # 1. List Connectors
        res = self.client.get("/api/agent-runtime/connectors/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        connectors_data = res.json()["results"] if "results" in res.json() else res.json()
        self.assertGreaterEqual(len(connectors_data), 10)

        # 2. Test execute endpoint
        banking_conn = Connector.objects.get(slug="mock-banking")
        test_res = self.client.post(
            f"/api/agent-runtime/connectors/{banking_conn.id}/test_execute/",
            {"capability": "READ", "action": "get_balance", "params": {}},
            format="json",
        )
        self.assertEqual(test_res.status_code, status.HTTP_200_OK)
        self.assertTrue(test_res.json()["success"])

        # 3. Configure Agent Connectors
        comm_conn = Connector.objects.get(slug="mock-commerce")
        conf_res = self.client.post(
            f"/api/agent-runtime/agents/{self.agent.id}/update_connectors/",
            {"connector_ids": [str(comm_conn.id), str(banking_conn.id)]},
            format="json",
        )
        self.assertEqual(conf_res.status_code, status.HTTP_200_OK)
        self.assertEqual(conf_res.json()["connected_count"], 2)
        self.assertEqual(self.agent.connectors.count(), 2)
