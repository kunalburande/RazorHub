import uuid
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    Agent,
    AgentUserConsentPolicy,
    CommercePaymentIntent,
    AgentAuditLog,
)
from .commerce_assistant import (
    CommerceIntent,
    DeterministicCommerceTools,
    AgenticCommerceService,
    BENCHMARK_HEADPHONES,
)
from orders.models import Order, Payment

User = get_user_model()


class AgenticCommerceAssistantTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="shopper@razorhub.test",
            password="testpassword123",
            username="shopper",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.agent = Agent.objects.create(
            name="Commerce Shopping Agent",
            description="Agentic commerce and payment assistant",
            system_prompt="You assist users with shopping and payments.",
            status="ACTIVE",
            approval_mode="AUTO",
            risk_level="LOW",
        )

        self.policy = AgentUserConsentPolicy.objects.create(
            user=self.user,
            per_transaction_limit=Decimal("5000.00"),
            approval_threshold=Decimal("2000.00"),
            daily_limit=Decimal("10000.00"),
            monthly_limit=Decimal("50000.00"),
            allowed_categories=["electronics", "peripherals", "accessories"],
        )

    def test_structured_intent_parsing(self):
        """Verifies natural language queries map to structured commerce intents."""
        self.assertEqual(
            AgenticCommerceService.parse_intent("I need wireless headphones under ₹5,000"),
            CommerceIntent.SEARCH_PRODUCTS,
        )
        self.assertEqual(
            AgenticCommerceService.parse_intent("Compare Sony WH-CH520 vs JBL Tune 510BT"),
            CommerceIntent.COMPARE_PRODUCTS,
        )
        self.assertEqual(
            AgenticCommerceService.parse_intent("Add the Sony headphones to cart and checkout"),
            CommerceIntent.ADD_TO_CART,
        )
        self.assertEqual(
            AgenticCommerceService.parse_intent("Confirm payment for my order"),
            CommerceIntent.PAY,
        )
        self.assertEqual(
            AgenticCommerceService.parse_intent("Where is my order? track order"),
            CommerceIntent.ORDER_STATUS,
        )

    def test_deterministic_product_search_and_filtering(self):
        """Verifies deterministic searchProducts respects price ceiling and categories."""
        products = DeterministicCommerceTools.searchProducts(query="headphones", max_price=5000.0)
        self.assertTrue(len(products) > 0)
        for p in products:
            self.assertLessEqual(p["price"], 5000.0)
            self.assertIn("headphones", p["name"].lower())

    def test_cart_calculation_and_payment_intent(self):
        """Verifies deterministic calculation and creation of payment intent."""
        item = {
            "id": "sony-wh-ch520",
            "name": "Sony WH-CH520 Wireless Bluetooth Headphones",
            "price": 3990.00,
            "quantity": 1,
        }
        cart = DeterministicCommerceTools.calculateCart([item])
        self.assertEqual(cart["subtotal"], 3990.00)
        self.assertEqual(cart["delivery_fee"], 50.00)
        self.assertEqual(cart["total_amount"], 4040.00)

        intent = DeterministicCommerceTools.createPaymentIntent(
            cart_data=cart,
            user=self.user,
            merchant="SonicAudio Store",
        )
        self.assertEqual(intent.amount, Decimal("4040.00"))
        self.assertEqual(intent.status, CommercePaymentIntent.IntentStatus.PENDING)

    def test_consent_policy_validation_rules(self):
        """
        Verifies deterministic consent thresholds:
        - Auto approve: ₹0 - ₹1,999 (< approvalThreshold)
        - Require confirmation: ₹2,000 - ₹5,000
        - Block: > ₹5,000
        """
        # Case 1: Auto approve under ₹2,000 (e.g. boAt Rockerz @ ₹1,999 + ₹0 fee = ₹1,999)
        auto_intent = CommercePaymentIntent.objects.create(
            user=self.user,
            amount=Decimal("1999.00"),
            product_summary="boAt Rockerz 450 Pro",
        )
        val_auto = DeterministicCommerceTools.validateTransaction(auto_intent, self.policy)
        self.assertEqual(val_auto["decision"], "AUTO_APPROVE")

        # Case 2: Require confirmation between ₹2,000 and ₹5,000 (e.g. Sony @ ₹4,040)
        confirm_intent = CommercePaymentIntent.objects.create(
            user=self.user,
            amount=Decimal("4040.00"),
            product_summary="Sony WH-CH520 Wireless Bluetooth Headphones",
        )
        val_confirm = DeterministicCommerceTools.validateTransaction(confirm_intent, self.policy)
        self.assertEqual(val_confirm["decision"], "REQUIRE_CONFIRMATION")
        self.assertIn("approval_card", val_confirm)

        approval_card = val_confirm["approval_card"]
        self.assertEqual(approval_card["card_type"], "TRANSACTION_APPROVAL")
        self.assertEqual(approval_card["amount"], 4040.00)
        self.assertEqual(approval_card["product"], "Sony WH-CH520 Wireless Bluetooth Headphones")
        self.assertEqual(approval_card["risk"], "LOW")
        self.assertIn("policy", approval_card)

        # Case 3: Block exceeding ₹5,000 (e.g. Sennheiser @ ₹8,990)
        block_intent = CommercePaymentIntent.objects.create(
            user=self.user,
            amount=Decimal("8990.00"),
            product_summary="Sennheiser ACCENTUM",
        )
        val_block = DeterministicCommerceTools.validateTransaction(block_intent, self.policy)
        self.assertEqual(val_block["decision"], "BLOCK")

    def test_simulated_payment_execution_and_audit(self):
        """Verifies executePayment creates verified Order, Payment(paid), and Audit Log."""
        intent = CommercePaymentIntent.objects.create(
            user=self.user,
            amount=Decimal("4040.00"),
            product_summary="Sony WH-CH520 Wireless Bluetooth Headphones",
            status=CommercePaymentIntent.IntentStatus.REQUIRES_CONFIRMATION,
            cart_snapshot={"items": [{"name": "Sony WH-CH520", "price": 3990.00, "quantity": 1}]},
        )

        exec_res = DeterministicCommerceTools.executePayment(str(intent.id), user=self.user)
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["status"], "PAID")
        self.assertIn("sim_pay_", exec_res["payment_reference"])

        # Check DB Order & Payment
        order = Order.objects.get(id=exec_res["order_id"])
        self.assertEqual(order.user, self.user)
        self.assertEqual(order.total_price, Decimal("4040.00"))

        payment = Payment.objects.get(order=order)
        self.assertEqual(payment.status, Payment.STATUS_PAID)

        # Check updated intent & consent spent
        intent.refresh_from_db()
        self.assertEqual(intent.status, CommercePaymentIntent.IntentStatus.EXECUTED)
        self.policy.refresh_from_db()
        self.assertEqual(self.policy.daily_spent, Decimal("4040.00"))

        # Check Audit Log
        audit = AgentAuditLog.objects.filter(actor_id=str(self.user.id)).first()
        self.assertIsNotNone(audit)
        self.assertEqual(audit.details.get("action"), "AGENTIC_PAYMENT_EXECUTED")

    def test_commerce_api_chat_and_approval_flow(self):
        """Tests end-to-end API interaction for conversational search, cart, and approval."""
        # 1. Search Query
        res_search = self.client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "I need wireless headphones under ₹5,000"},
            format="json",
        )
        self.assertEqual(res_search.status_code, status.HTTP_200_OK)
        data_search = res_search.json()
        self.assertEqual(data_search["intent"], "SEARCH_PRODUCTS")
        self.assertTrue(len(data_search["products"]) > 0)

        # 2. Add to Cart & Checkout (which triggers approval card because ₹4,040 > ₹2,000 threshold)
        res_checkout = self.client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "Add Sony to cart and checkout"},
            format="json",
        )
        self.assertEqual(res_checkout.status_code, status.HTTP_200_OK)
        data_checkout = res_checkout.json()
        self.assertEqual(data_checkout["intent"], "CHECKOUT")
        self.assertIn("approval_card", data_checkout)
        approval_card = data_checkout["approval_card"]
        intent_id = approval_card["intent_id"]

        # 3. Approve Payment Intent
        res_approve = self.client.post(
            "/api/agent-runtime/commerce/approve/",
            {"intent_id": intent_id},
            format="json",
        )
        self.assertEqual(res_approve.status_code, status.HTTP_200_OK)
        data_approve = res_approve.json()
        self.assertTrue(data_approve["success"])
        self.assertEqual(data_approve["status"], "PAID")
