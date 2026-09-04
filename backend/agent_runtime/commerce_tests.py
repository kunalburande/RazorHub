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
            is_configured=True,
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

    def test_seller_copilot_low_stock_intent(self):
        """Verifies 'Which products have low stock?' routes to SELLER_INVENTORY with store name and does not checkout."""
        seller_user = User.objects.create_user(
            email="seller.nexus@razorhub.test",
            password="sellerpassword123",
            username="seller_nexus",
            role="seller",
        )
        from sellers.models import Store, SellerProfile
        seller_profile = SellerProfile.objects.create(user=seller_user)
        store = Store.objects.create(
            seller=seller_profile,
            name="Nexus Tech Hub",
            slug="nexus-tech-hub",
            support_email="seller.nexus@razorhub.test",
        )
        seller_client = APIClient()
        seller_client.force_authenticate(user=seller_user)

        res = seller_client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "Which products have low stock?"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["intent"], "SELLER_INVENTORY")
        self.assertIn("Inventory", data["message"])
        self.assertIn("Nexus Tech Hub", data["message"])
        self.assertNotIn("Ananya", data["message"])
        self.assertNotIn("approval_card", data)

    def test_seller_without_store_notice(self):
        """Verifies seller without linked store receives clean setup notice without Ananya fallback."""
        seller_unlinked = User.objects.create_user(
            email="seller.unlinked@razorhub.test",
            password="sellerpassword123",
            username="seller_unlinked",
            role="seller",
        )
        seller_client = APIClient()
        seller_client.force_authenticate(user=seller_unlinked)

        res = seller_client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "Analyze today's store revenue"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["intent"], "SELLER_ANALYTICS")
        self.assertIn("No Merchant Store Linked", data["message"])
        self.assertNotIn("Ananya", data["message"])

    def test_seller_copilot_campaign_revenue_intent(self):
        """Verifies 'Increase revenue from customers who purchased laptops' routes to SELLER_CAMPAIGN."""
        seller_user = User.objects.create_user(
            email="seller.growth@razorhub.test",
            password="sellerpassword123",
            username="seller_growth",
            role="seller",
        )
        from sellers.models import Store, SellerProfile
        seller_profile = SellerProfile.objects.create(user=seller_user)
        Store.objects.create(
            seller=seller_profile,
            name="Growth Electronics",
            slug="growth-electronics",
            support_email="seller.growth@razorhub.test",
        )
        seller_client = APIClient()
        seller_client.force_authenticate(user=seller_user)

        res = seller_client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "Increase revenue from customers who purchased laptops"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["intent"], "SELLER_CAMPAIGN")
        self.assertIn("Autonomous Campaign Orchestrator", data["message"])
        self.assertNotIn("approval_card", data)

    def test_seller_copilot_sales_analytics_intent(self):
        """Verifies 'Analyze today's store revenue' routes to SELLER_ANALYTICS with real store name."""
        seller_user = User.objects.create_user(
            email="seller.sales@razorhub.test",
            password="sellerpassword123",
            username="seller_sales",
            role="seller",
        )
        from sellers.models import Store, SellerProfile
        seller_profile = SellerProfile.objects.create(user=seller_user)
        Store.objects.create(
            seller=seller_profile,
            name="Apex Retail Hub",
            slug="apex-retail-hub",
            support_email="seller.sales@razorhub.test",
        )
        seller_client = APIClient()
        seller_client.force_authenticate(user=seller_user)

        res = seller_client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "Analyze today's store revenue"},
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["intent"], "SELLER_ANALYTICS")
        self.assertIn("Apex Retail Hub", data["message"])
        self.assertNotIn("Ananya", data["message"])

    def test_admin_role_command_engine(self):
        """Verifies admin receives platform-wide metrics with zero Ananya fallback."""
        admin_user = User.objects.create_user(
            email="admin@razorhub.test",
            password="adminpassword123",
            username="admin_tester",
            role="admin",
            is_staff=True,
        )
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin_user)

        # 1. Platform GMV & Orders
        res_gmv = admin_client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "how today's platform GMV and orders"},
            format="json",
        )
        self.assertEqual(res_gmv.status_code, status.HTTP_200_OK)
        data_gmv = res_gmv.json()
        self.assertEqual(data_gmv["intent"], "ADMIN_ANALYTICS")
        self.assertIn("Platform-Wide Performance Summary", data_gmv["message"])
        self.assertNotIn("Ananya", data_gmv["message"])

        # 2. Dunning simulation
        res_dunning = admin_client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "Simulate failed payment dunning recovery"},
            format="json",
        )
        self.assertEqual(res_dunning.status_code, status.HTTP_200_OK)
        data_dunning = res_dunning.json()
        self.assertEqual(data_dunning["intent"], "ADMIN_DUNNING")
        self.assertIn("Autonomous Platform Payment Dunning & Recovery Engine", data_dunning["message"])
        self.assertNotIn("Ananya", data_dunning["message"])

        # 3. RTO risk
        res_rto = admin_client.post(
            "/api/agent-runtime/commerce/chat/",
            {"message": "Analyze platform RTO risk"},
            format="json",
        )
        self.assertEqual(res_rto.status_code, status.HTTP_200_OK)
        data_rto = res_rto.json()
        self.assertEqual(data_rto["intent"], "ADMIN_RTO_RISK")
        self.assertIn("Platform Pre-Dispatch Return-To-Origin (RTO) Firewall", data_rto["message"])
        self.assertNotIn("Ananya", data_rto["message"])

    def test_empty_cart_checkout_guard_no_ssd(self):
        """Verifies empty bag checkout never fabricates products or SSDs."""
        res = self.client.post(
            "/api/agent-runtime/commerce/chat/",
            {
                "message": "Proceed with checkout for my bag items",
                "cart": {"items": [], "total_amount": 0},
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["intent"], "CHECKOUT")
        self.assertIn("Your shopping bag is currently empty (0 items)", data["message"])
        self.assertNotIn("approval_card", data)
        self.assertNotIn("Silicon Power", data["message"])
        self.assertNotIn("256gb", data["message"].lower())
        self.assertNotIn("ssd", data["message"].lower())

    def test_unconfigured_policy_blocks_payment(self):
        """Verifies unconfigured consent policy mandates user rule definition before payment."""
        unconf_user = User.objects.create_user(
            email="unconf@razorhub.test",
            password="testpassword123",
            username="unconf_user",
        )
        policy = AgentUserConsentPolicy.objects.create(
            user=unconf_user,
            is_configured=False,
            approval_threshold=Decimal("2000.00"),
            per_transaction_limit=Decimal("150000.00"),
        )
        client = APIClient()
        client.force_authenticate(user=unconf_user)

        # 1. Checkout validation returns RULES_NOT_CONFIGURED
        item = {"id": "sony-wh-ch520", "name": "Sony WH-CH520", "price": 3990.00, "quantity": 1}
        cart = DeterministicCommerceTools.calculateCart([item])
        intent = DeterministicCommerceTools.createPaymentIntent(cart_data=cart, user=unconf_user)
        val = DeterministicCommerceTools.validateTransaction(intent, policy=policy)
        self.assertEqual(val["decision"], "RULES_NOT_CONFIGURED")
        self.assertFalse(val["approval_card"]["rules_configured"])

        # 2. Approve endpoint returns 400 with RULES_NOT_CONFIGURED
        res_approve = client.post(
            "/api/agent-runtime/commerce/approve/",
            {"intent_id": str(intent.id)},
            format="json",
        )
        self.assertEqual(res_approve.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_approve.json().get("code"), "RULES_NOT_CONFIGURED")

        # 3. executePayment raises ValueError
        with self.assertRaises(ValueError) as cm:
            DeterministicCommerceTools.executePayment(str(intent.id), user=unconf_user)
        self.assertIn("Payment authorization rules have not been configured", str(cm.exception))

    def test_search_laptops_relevance_excludes_consoles(self):
        """Verifies searching for laptops returns laptops and never gaming consoles."""
        from products.models import Product, Category
        cat_laptops, _ = Category.objects.get_or_create(name="Laptops", slug="laptops")
        cat_gaming, _ = Category.objects.get_or_create(name="Gaming", slug="gaming")

        Product.objects.create(
            name="MacBook Air M3 Test Model",
            slug="macbook-air-m3-test-model",
            category=cat_laptops,
            price=Decimal("99990.00"),
            stock=10,
            is_active=True,
        )
        Product.objects.create(
            name="Sony PlayStation 5 Test Model",
            slug="ps5-test-model",
            category=cat_gaming,
            price=Decimal("49990.00"),
            stock=5,
            is_active=True,
        )

        results = DeterministicCommerceTools.searchProducts(query="laptops")
        result_names = [p["name"] for p in results]
        self.assertIn("MacBook Air M3 Test Model", result_names)
        self.assertNotIn("Sony PlayStation 5 Test Model", result_names)

    def test_affirmative_yes_response_context_checkout(self):
        """Verifies replying 'yes' to an assistant proposal checks out the proposed item and does not return cosmetics or random jackets."""
        from products.models import Product, Category
        cat_gaming, _ = Category.objects.get_or_create(name="Gaming", slug="gaming")
        Product.objects.create(
            name="Xbox Series S Test Unit",
            slug="xbox-series-s-test-unit",
            category=cat_gaming,
            price=Decimal("31990.00"),
            stock=10,
            is_active=True,
        )

        self.policy.per_transaction_limit = Decimal("50000.00")
        self.policy.daily_limit = Decimal("100000.00")
        self.policy.save()

        history = [
            {
                "role": "agent",
                "content": "My top recommendation is the **Xbox Series S Test Unit** (₹31,990.00) with a rating of 4.8★.\n\nWould you like me to prepare checkout for the **Xbox Series S Test Unit**?",
            }
        ]

        res = self.client.post(
            "/api/agent-runtime/commerce/chat/",
            {
                "message": "yes",
                "history": history,
            },
            format="json",
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertEqual(data["intent"], "CHECKOUT")
        self.assertIn("approval_card", data)
        self.assertEqual(data["approval_card"]["product"], "Xbox Series S Test Unit")
        self.assertNotIn("jacket", data["message"].lower())
        self.assertNotIn("eyeshadow", data["message"].lower())

    def test_agent_checkout_clears_database_cart(self):
        """Verifies that executing checkout payment removes purchased items from user's database Cart."""
        from products.models import Product, Category
        from orders.models import Cart as DbCart, CartItem as DbCartItem

        cat, _ = Category.objects.get_or_create(name="Electronics", slug="electronics")
        prod1 = Product.objects.create(
            name="Wireless Mouse Pro",
            slug="wireless-mouse-pro",
            category=cat,
            price=Decimal("1500.00"),
            stock=15,
            is_active=True,
        )
        prod2 = Product.objects.create(
            name="Mechanical Keyboard RGB",
            slug="mechanical-keyboard-rgb",
            category=cat,
            price=Decimal("3500.00"),
            stock=10,
            is_active=True,
        )

        # Set up user's database cart with both products
        db_cart, _ = DbCart.objects.get_or_create(user=self.user)
        DbCartItem.objects.create(cart=db_cart, product=prod1, quantity=1)
        DbCartItem.objects.create(cart=db_cart, product=prod2, quantity=1)
        self.assertEqual(db_cart.items.count(), 2)

        # Stage checkout intent for prod1
        cart_payload = {
            "items": [{
                "id": str(prod1.id),
                "name": prod1.name,
                "slug": prod1.slug,
                "price": float(prod1.price),
                "quantity": 1,
            }],
            "total_amount": 1500.00,
        }
        intent = DeterministicCommerceTools.createPaymentIntent(cart_payload, user=self.user)

        # Execute payment
        res = DeterministicCommerceTools.executePayment(str(intent.id), user=self.user)
        self.assertTrue(res["success"])
        self.assertIn(prod1.id, res["cleared_product_ids"])

        # Check that prod1 was removed from db_cart, and prod2 remains
        remaining_items = DbCartItem.objects.filter(cart=db_cart)
        self.assertEqual(remaining_items.count(), 1)
        self.assertEqual(remaining_items.first().product_id, prod2.id)

        # Now checkout prod2
        cart_payload2 = {
            "items": [{
                "id": str(prod2.id),
                "name": prod2.name,
                "slug": prod2.slug,
                "price": float(prod2.price),
                "quantity": 1,
            }],
            "total_amount": 3500.00,
        }
        intent2 = DeterministicCommerceTools.createPaymentIntent(cart_payload2, user=self.user)
        res2 = DeterministicCommerceTools.executePayment(str(intent2.id), user=self.user)
        self.assertTrue(res2["success"])

        # DB cart should now be completely empty
        self.assertEqual(DbCartItem.objects.filter(cart=db_cart).count(), 0)
