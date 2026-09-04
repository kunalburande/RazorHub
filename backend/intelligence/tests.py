from decimal import Decimal
from django.test import TestCase
from products.models import Product, Category, Brand
from intelligence.services.profit_optimizer import ProfitOptimizerService


class ProfitOptimizerTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Footwear", slug="footwear")
        self.brand = Brand.objects.create(name="StrideLab", slug="stridelab")

        # Base Product: ₹2,000 shoes (cost ₹1,200)
        self.base_shoes = Product.objects.create(
            name="StrideLab Classic Running Shoes",
            slug="stridelab-classic-running-shoes",
            category=self.category,
            brand=self.brand,
            price=Decimal("2000.00"),
            cost_price=Decimal("1200.00"),
            stock=40,
            description="Comfortable daily running shoes.",
        )

        # Candidate 1: Socks (₹300, Cost ₹120 -> Margin ₹180)
        self.socks = Product.objects.create(
            name="Breathable Cotton Athletic Socks",
            slug="breathable-cotton-athletic-socks",
            category=self.category,
            brand=self.brand,
            price=Decimal("300.00"),
            cost_price=Decimal("120.00"),
            stock=100,
            rating=Decimal("4.2"),
            description="Cushioned ankle running socks.",
        )

        # Candidate 2: Premium Insoles (₹800, Cost ₹300 -> Margin ₹500)
        self.insoles = Product.objects.create(
            name="Orthotic Gel Memory Foam Insoles",
            slug="orthotic-gel-memory-foam-insoles",
            category=self.category,
            brand=self.brand,
            price=Decimal("800.00"),
            cost_price=Decimal("300.00"),
            stock=45,
            rating=Decimal("4.4"),
            description="High arch support insoles.",
        )

        # Candidate 3: Premium Shoe Upgrade (₹3,000, incremental margin ₹350)
        self.shoe_upgrade = Product.objects.create(
            name="StrideLab Pro Carbon Marathon Shoes",
            slug="stridelab-pro-carbon-marathon-shoes",
            category=self.category,
            brand=self.brand,
            price=Decimal("3000.00"),
            cost_price=Decimal("1850.00"),  # Incremental margin: (3000-2000) - (1850-1200) = 1000 - 650 = 350
            stock=25,
            rating=Decimal("4.7"),
            description="Carbon-plated elite race shoes.",
        )

        # Candidate 4: Shoe-care kit (₹500, Cost ₹200 -> Margin ₹300)
        self.shoe_care_kit = Product.objects.create(
            name="Complete Sneaker Cleaning & Care Kit",
            slug="complete-sneaker-cleaning-care-kit",
            category=self.category,
            brand=self.brand,
            price=Decimal("500.00"),
            cost_price=Decimal("200.00"),
            stock=80,
            rating=Decimal("4.6"),
            description="Bristle brush, foaming cleanser, and water repellent shield.",
        )

    def test_shoe_care_kit_beats_higher_priced_options(self):
        """
        Validates the user prompt's exact business rule:
        - Socks: EIM = .35 × ₹180 = ₹63
        - Insoles: EIM = .18 × ₹500 = ₹90
        - Upgrade: EIM = .12 × ₹350 = ₹42
        - Shoe-Care Kit: EIM = .32 × ₹300 = ₹96
        The agent must prioritize Shoe-Care Kit over higher priced Insoles (₹800) and Upgrade (₹3,000)!
        """
        score_socks = ProfitOptimizerService.calculate_opportunity_score(
            candidate=self.socks,
            base_product=self.base_shoes,
            relationship_type="accessory_for"
        )
        score_insoles = ProfitOptimizerService.calculate_opportunity_score(
            candidate=self.insoles,
            base_product=self.base_shoes,
            relationship_type="accessory_for"
        )
        score_upgrade = ProfitOptimizerService.calculate_opportunity_score(
            candidate=self.shoe_upgrade,
            base_product=self.base_shoes,
            relationship_type="upgrade_to",
            is_upgrade=True
        )
        score_care_kit = ProfitOptimizerService.calculate_opportunity_score(
            candidate=self.shoe_care_kit,
            base_product=self.base_shoes,
            relationship_type="accessory_for"
        )

        # Check contribution margins
        self.assertEqual(score_socks["contribution_margin"], 180.0)
        self.assertEqual(score_insoles["contribution_margin"], 500.0)
        self.assertEqual(score_upgrade["contribution_margin"], 350.0)
        self.assertEqual(score_care_kit["contribution_margin"], 300.0)

        # Verify expected incremental margin (EIM) comparison
        # Shoe-care kit EIM must exceed socks, insoles, and upgrade!
        self.assertGreater(score_care_kit["expected_incremental_margin"], score_socks["expected_incremental_margin"])
        self.assertGreater(score_care_kit["expected_incremental_margin"], score_upgrade["expected_incremental_margin"])
        self.assertGreater(score_care_kit["opportunity_score"], score_insoles["opportunity_score"])
        self.assertGreater(score_care_kit["opportunity_score"], score_upgrade["opportunity_score"])

    def test_opportunity_score_formula_penalties(self):
        """Tests that discount costs, customer fatigue, and cannibalization risk deduct properly."""
        base_score = ProfitOptimizerService.calculate_opportunity_score(
            candidate=self.shoe_care_kit,
            base_product=self.base_shoes,
            discount_offered=Decimal("0.00"),
            dismissed_count=0
        )

        penalized_score = ProfitOptimizerService.calculate_opportunity_score(
            candidate=self.shoe_care_kit,
            base_product=self.base_shoes,
            discount_offered=Decimal("50.00"),
            dismissed_count=2
        )

        self.assertLess(penalized_score["opportunity_score"], base_score["opportunity_score"])
        self.assertGreater(penalized_score["discount_cost"], 0.0)
        self.assertGreater(penalized_score["customer_fatigue_risk"], 0.0)

    def test_causal_uplift_persuadable_vs_sure_thing(self):
        """
        Validates the user prompt's exact Uplift scenario:
        - Customer 1 (Persuadable): P0 = 0.30, P1 = 0.52 -> Uplift = 0.22
        - Customer 2 (Sure Thing):   P0 = 0.70, P1 = 0.73 -> Uplift = 0.03
        A traditional recommender favors Customer 2 (0.73 > 0.52).
        Our Uplift Agent spends the recommendation opportunity on Customer 1 (0.22 vs 0.03)!
        """
        from intelligence.services.uplift_service import UpliftModelService, UpliftQuadrant

        # Evaluate Customer 1
        eval_c1 = UpliftModelService.evaluate_uplift(
            user=None,
            candidate=self.shoe_care_kit,
            base_product=self.base_shoes,
            baseline_override=Decimal("0.3000"),
            treatment_override=Decimal("0.5200")
        )
        self.assertAlmostEqual(eval_c1["uplift"], 0.22, places=2)
        self.assertEqual(eval_c1["quadrant"], UpliftQuadrant.PERSUADABLE)

        # Evaluate Customer 2
        eval_c2 = UpliftModelService.evaluate_uplift(
            user=None,
            candidate=self.shoe_care_kit,
            base_product=self.base_shoes,
            baseline_override=Decimal("0.7000"),
            treatment_override=Decimal("0.7300")
        )
        self.assertAlmostEqual(eval_c2["uplift"], 0.03, places=2)
        self.assertEqual(eval_c2["quadrant"], UpliftQuadrant.SURE_THING)

        # Calculate Opportunity Score for both customers with ₹300 margin
        score_c1 = ProfitOptimizerService.calculate_opportunity_score(
            candidate=self.shoe_care_kit,
            base_product=self.base_shoes,
            baseline_override=Decimal("0.3000"),
            treatment_override=Decimal("0.5200")
        )

        score_c2 = ProfitOptimizerService.calculate_opportunity_score(
            candidate=self.shoe_care_kit,
            base_product=self.base_shoes,
            baseline_override=Decimal("0.7000"),
            treatment_override=Decimal("0.7300")
        )

        # Verify Causal Incremental Margin:
        # C1 (0.22 * 300 = Rs. 66) vs C2 (0.03 * 300 = Rs. 9)
        self.assertAlmostEqual(score_c1["causal_incremental_margin"], 66.0, delta=1.0)
        self.assertAlmostEqual(score_c2["causal_incremental_margin"], 9.0, delta=1.0)

        # Assert Customer 1 is prioritized over Customer 2!
        self.assertGreater(score_c1["opportunity_score"], score_c2["opportunity_score"])
        self.assertGreater(score_c1["opportunity_score"] / score_c2["opportunity_score"], 5.0)

    def test_uplift_quadrant_classifications(self):
        """Validates classification across all 4 quadrants: Persuadables, Sure Things, Lost Causes, Sleeping Dogs."""
        from intelligence.services.uplift_service import UpliftModelService, UpliftQuadrant

        # 1. Persuadable
        q_persuadable = UpliftModelService.classify_customer_quadrant(
            p_baseline=Decimal("0.25"), p_treatment=Decimal("0.50"), uplift=Decimal("0.25")
        )
        self.assertEqual(q_persuadable["quadrant"], UpliftQuadrant.PERSUADABLE)
        self.assertEqual(q_persuadable["action"], "PRIORITIZE_OFFER")

        # 2. Sure Thing
        q_sure_thing = UpliftModelService.classify_customer_quadrant(
            p_baseline=Decimal("0.75"), p_treatment=Decimal("0.78"), uplift=Decimal("0.03")
        )
        self.assertEqual(q_sure_thing["quadrant"], UpliftQuadrant.SURE_THING)
        self.assertEqual(q_sure_thing["action"], "SUPPRESS_DISCOUNT")

        # 3. Lost Cause
        q_lost_cause = UpliftModelService.classify_customer_quadrant(
            p_baseline=Decimal("0.04"), p_treatment=Decimal("0.06"), uplift=Decimal("0.02")
        )
        self.assertEqual(q_lost_cause["quadrant"], UpliftQuadrant.LOST_CAUSE)
        self.assertEqual(q_lost_cause["action"], "CONSERVE_BUDGET")

        # 4. Sleeping Dog
        q_sleeping_dog = UpliftModelService.classify_customer_quadrant(
            p_baseline=Decimal("0.40"), p_treatment=Decimal("0.35"), uplift=Decimal("-0.05")
        )
        self.assertEqual(q_sleeping_dog["quadrant"], UpliftQuadrant.SLEEPING_DOG)
        self.assertEqual(q_sleeping_dog["action"], "HARD_SUPPRESS")

    def test_bundle_compiler_photography_phone_example(self):
        """
        Validates the user prompt's exact Bundle Compiler scenario:
        - Customer: "I need a phone for photography under ₹35,000"
        - Primary: Phone A = ₹31,999
        - Accessories: Case (₹699), Screen Protector (₹399), Power Bank (₹1,299), Lens Kit (₹1,299)
        - Budget limit: ₹35,000
        - Creator Bundle = Phone + Case + Screen Protector = ₹33,097 (Headroom = ₹1,903 below budget)
        - Complete Bundle = ₹35,696 (Exceeds budget by ₹696)
        - Asserts agent automatically compiles and explains Creator Bundle!
        """
        from intelligence.services.bundle_compiler import BundleCompilerService

        phone_cat = Category.objects.create(name="Smartphones", slug="smartphones")

        phone_a = Product.objects.create(
            name="Lumix Pro Camera Smartphone",
            slug="lumix-pro-camera-smartphone",
            category=phone_cat,
            price=Decimal("31999.00"),
            stock=20,
        )

        case = Product.objects.create(
            name="Shockproof Armor Protective Case",
            slug="shockproof-armor-protective-case",
            category=phone_cat,
            price=Decimal("699.00"),
            stock=50,
        )

        screen_protector = Product.objects.create(
            name="Tempered Glass Screen Protector",
            slug="tempered-glass-screen-protector",
            category=phone_cat,
            price=Decimal("399.00"),
            stock=50,
        )

        power_bank = Product.objects.create(
            name="Magnetic Wireless Power Bank 10000mAh",
            slug="magnetic-wireless-power-bank-10000mah",
            category=phone_cat,
            price=Decimal("1299.00"),
            stock=30,
        )

        lens_attachment = Product.objects.create(
            name="Macro & Wide Angle Pro Lens Attachment",
            slug="macro-wide-angle-pro-lens-attachment",
            category=phone_cat,
            price=Decimal("1299.00"),
            stock=25,
        )

        # Parse query
        parsed = BundleCompilerService.parse_intent_and_budget("I need a phone for photography under ₹35,000")
        self.assertEqual(parsed["budget_limit"], Decimal("35000"))
        self.assertEqual(parsed["use_case"], "photography")

        # Compile bundle with candidate accessories
        bundle_result = BundleCompilerService.compile_bundle(
            primary=phone_a,
            budget_limit=parsed["budget_limit"],
            candidate_accessories=[case, screen_protector, power_bank, lens_attachment],
            bundle_discount_pct=Decimal("0.0")  # Exact raw pricing benchmark
        )

        tiers = bundle_result["tiers"]
        creator = tiers["creator"]
        complete = tiers["complete"]

        # Creator Bundle: Phone (31,999) + Case (699) + Screen Protector (399) = 33,097
        self.assertEqual(creator["bundle_price"], 33097.0)
        self.assertEqual(creator["savings_headroom"], 1903.0)
        self.assertTrue(creator["is_within_budget"])

        # Complete Bundle: Exceeds 35,000
        self.assertGreater(complete["bundle_price"], 35000.0)
        self.assertFalse(complete["is_within_budget"])

        # Assert recommended tier is Creator Bundle
        self.assertEqual(bundle_result["recommended_tier"], "creator")

        # Assert explanation cites headroom and protection
        explanation = bundle_result["explanation"]
        self.assertIn("1,903", explanation)
        self.assertIn("below your budget", explanation)
        self.assertIn("protection", explanation.lower())

    def test_agent_readable_product_manifest(self):
        """Validates that AgentManifestService outputs facts-only, schema-valid JSON for AI buyers."""
        from intelligence.services.agent_manifest import AgentManifestService

        manifest = AgentManifestService.build_product_manifest(self.base_shoes)

        # Assert mandatory AI buyer facts
        self.assertEqual(manifest["name"], "StrideLab Classic Running Shoes")
        self.assertEqual(manifest["price"]["amount"], 2000.0)
        self.assertEqual(manifest["price"]["currency"], "INR")
        self.assertEqual(manifest["availability"]["status"], "in_stock")
        self.assertEqual(manifest["availability"]["quantity"], 40)
        self.assertIn("max_quantity_per_order", manifest["constraints"])
        self.assertIn("estimated_days", manifest["shipping"])
        self.assertIn("window_days", manifest["returns"])
        self.assertIsInstance(manifest["attributes"], dict)
        self.assertIsInstance(manifest["compatibility"], list)

    def test_agent_buyer_compatibility_score_and_diagnostic(self):
        """
        Validates the AI Commerce Readiness Score calculation across 8 pillars
        and tests the explainable diagnostic summary output.
        """
        from intelligence.services.agent_compatibility import AgentBuyerCompatibilityService

        readiness = AgentBuyerCompatibilityService.evaluate_store_readiness(
            products_qs=Product.objects.filter(id__in=[
                self.base_shoes.id,
                self.socks.id,
                self.insoles.id,
                self.shoe_care_kit.id
            ])
        )

        # Assert total score range (0-100)
        self.assertGreaterEqual(readiness["total_score"], 60)
        self.assertLessEqual(readiness["total_score"], 100)

        # Assert all 8 pillars are evaluated
        pillars = readiness["pillars"]
        expected_pillars = [
            "catalog_completeness",
            "structured_product_data",
            "live_inventory_availability",
            "price_consistency",
            "shipping_information",
            "compatibility_metadata",
            "machine_checkout",
            "transaction_policy",
        ]
        for p in expected_pillars:
            self.assertIn(p, pillars)
            self.assertIn("score", pillars[p])
            self.assertIn("max", pillars[p])

        # Assert explainable diagnostic text
        diag = readiness["diagnostic_summary"]
        self.assertIn("discoverable by AI buyers", diag)
        self.assertIsInstance(readiness["action_items"], list)
        self.assertGreater(len(readiness["action_items"]), 0)

    def test_merchant_policy_blocked_human_confirmation_example(self):
        """
        Validates the user prompt's exact Merchant Policy scenario:
        - Merchant Policy: max_autonomous_order_value = ₹5,000
        - LLM Proposes: Offer Phone + Case (Total: ₹32,698)
        - Decision: BLOCKED → human confirmation required
        - LLM CANNOT override this deterministic check.
        """
        from intelligence.services.merchant_policy import MerchantPolicyEngine

        policy = {
            "max_discount": Decimal("10.00"),
            "max_autonomous_order_value": Decimal("5000.00"),
            "max_items_per_order": 5,
            "min_margin_percent": Decimal("18.00"),
            "auto_approval_under": Decimal("1500.00"),
            "human_approval_from": Decimal("1500.00"),
            "human_approval_to": Decimal("5000.00"),
            "human_required_above": Decimal("5000.00"),
        }

        proposal = {
            "items": ["Phone", "Case"],
            "total_price": Decimal("32698.00"),
            "discount_pct": Decimal("5.00"),
            "margin_pct": Decimal("25.00"),
            "categories": ["mobiles", "accessories"],
        }

        result = MerchantPolicyEngine.evaluate_proposal(proposal, policy)

        self.assertFalse(result["allowed"])
        self.assertEqual(result["decision"], "BLOCKED → human confirmation required")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["rule_violated"], "max_autonomous_order_value")
        self.assertEqual(result["limit_value"], 5000.0)
        self.assertEqual(result["proposed_value"], 32698.0)
        self.assertIn("32,698", result["explanation"])
        self.assertIn("5,000", result["explanation"])

    def test_merchant_policy_approval_gating_tiers(self):
        """Validates auto-approval under ₹1500, gated review between ₹1500-₹5000, and discount violations."""
        from intelligence.services.merchant_policy import MerchantPolicyEngine

        policy = {
            "max_discount": Decimal("10.00"),
            "max_autonomous_order_value": Decimal("5000.00"),
            "max_items_per_order": 5,
            "min_margin_percent": Decimal("18.00"),
            "auto_approval_under": Decimal("1500.00"),
            "human_approval_from": Decimal("1500.00"),
            "human_approval_to": Decimal("5000.00"),
            "human_required_above": Decimal("5000.00"),
        }

        # 1. Auto-approved (under ₹1,500)
        auto_prop = {"items": ["Socks"], "total_price": Decimal("999.00"), "discount_pct": Decimal("5.00"), "margin_pct": Decimal("20.00")}
        res_auto = MerchantPolicyEngine.evaluate_proposal(auto_prop, policy)
        self.assertTrue(res_auto["allowed"])
        self.assertEqual(res_auto["status"], "APPROVED")

        # 2. Gated review (between ₹1,500 and ₹5,000)
        gated_prop = {"items": ["Shoes"], "total_price": Decimal("3500.00"), "discount_pct": Decimal("5.00"), "margin_pct": Decimal("22.00")}
        res_gated = MerchantPolicyEngine.evaluate_proposal(gated_prop, policy)
        self.assertFalse(res_gated["allowed"])
        self.assertEqual(res_gated["status"], "GATED")
        self.assertEqual(res_gated["decision"], "GATED → merchant authorization pending")

        # 3. Discount ceiling violation (e.g. 15% discount when max is 10%)
        discount_prop = {"items": ["Socks"], "total_price": Decimal("800.00"), "discount_pct": Decimal("15.00"), "margin_pct": Decimal("20.00")}
        res_disc = MerchantPolicyEngine.evaluate_proposal(discount_prop, policy)
        self.assertFalse(res_disc["allowed"])
        self.assertEqual(res_disc["decision"], "BLOCKED → discount limit exceeded")

    def test_why_this_offer_proof_benchmark(self):
        """
        Validates user benchmark:
        WHY THIS OFFER?
        Customer intent: "Photography phone under ₹35K"
        Recommendation: Phone X + protective case
        Reason:
          • Fits budget
          • High compatibility confidence
          • Case has 72% attach rate with Phone X
          • Case has 24 units available
          • Expected incremental margin: ₹310
          • No additional discount required
        Confidence: 92%
        """
        from intelligence.services.explainability_service import FinancialExplainabilityService

        base_phone = Product.objects.create(
            name="Phone X",
            slug="phone-x-benchmark",
            price=Decimal("31999.00"),
            cost_price=Decimal("26000.00"),
            stock=15,
            category=self.category,
        )
        case_item = Product.objects.create(
            name="protective case",
            slug="case-benchmark-protective",
            price=Decimal("699.00"),
            cost_price=Decimal("350.00"),
            stock=24,
            category=self.category,
        )

        proof = FinancialExplainabilityService.generate_why_offer_proof(
            candidate=case_item,
            base_product=base_phone,
            customer_intent="Photography phone under ₹35K",
            budget=Decimal("35000.00"),
            expected_margin=310.0
        )

        self.assertEqual(proof["title"], "WHY THIS OFFER?")
        self.assertEqual(proof["customer_intent"], "Photography phone under ₹35K")
        self.assertEqual(proof["recommendation"], "Phone X + protective case")
        self.assertEqual(proof["confidence"], "92%")

        reasons_str = " ".join(proof["reasons"])
        self.assertIn("Fits budget", reasons_str)
        self.assertIn("High compatibility confidence", reasons_str)
        self.assertIn("72% attach rate with Phone X", reasons_str)
        self.assertIn("24 units available", reasons_str)
        self.assertIn("Expected incremental margin: ₹310", reasons_str)
        self.assertIn("No additional discount required", reasons_str)

    def test_why_is_transaction_allowed_proof_benchmark(self):
        """
        Validates user benchmark:
        WHY IS THIS TRANSACTION ALLOWED?
        Requested by: AI Shopping Agent
        User budget: ₹35,000
        Cart: ₹33,097
        Merchant autonomous limit: ₹35,000
        Product status: In stock
        Price verified: 1.4 seconds ago
        Policy check: PASSED
        """
        from intelligence.services.explainability_service import FinancialExplainabilityService

        proof = FinancialExplainabilityService.generate_why_transaction_allowed_proof(
            cart_total=Decimal("33097.00"),
            user_budget=Decimal("35000.00"),
            requested_by="AI Shopping Agent",
            merchant_limit=Decimal("35000.00"),
            verification_time_seconds=1.4
        )

        self.assertEqual(proof["title"], "WHY IS THIS TRANSACTION ALLOWED?")
        self.assertEqual(proof["requested_by"], "AI Shopping Agent")
        self.assertEqual(proof["user_budget"], 35000.0)
        self.assertEqual(proof["cart"], 33097.0)
        self.assertEqual(proof["merchant_autonomous_limit"], 35000.0)
        self.assertEqual(proof["product_status"], "In stock")
        self.assertEqual(proof["policy_check"], "PASSED")
        self.assertTrue(proof["allowed"])

    def test_benefit_ladder_negotiation_benchmark(self):
        """
        Validates user benchmark:
        Customer: "Can you get this below ₹5,000?"
        Agent evaluates:
          Product price: ₹5,299
          Minimum margin: 20%
          Current margin: 24%
          Allowed discount: ₹200
          Free shipping value: ₹100
        Response:
          "I can't reduce the item below ₹5,099 under this merchant's pricing rules, but I can apply free shipping."
        """
        from intelligence.services.negotiation_engine import BenefitLadderNegotiator

        product = Product.objects.create(
            name="Premium Wireless Headphones",
            slug="headphones-negotiation-benchmark",
            price=Decimal("5299.00"),
            cost_price=Decimal("4027.24"),
            stock=12,
            category=self.category,
        )

        res = BenefitLadderNegotiator.evaluate_negotiation(
            product=product,
            requested_target_price=Decimal("5000.00"),
            min_margin_percent=Decimal("20.00"),
            free_shipping_value=Decimal("100.00"),
        )

        self.assertEqual(res["product_price"], 5299.0)
        self.assertEqual(res["requested_target_price"], 5000.0)
        self.assertEqual(res["minimum_margin_percent"], 20.0)
        self.assertEqual(res["current_margin_percent"], 24.0)
        self.assertEqual(res["allowed_discount"], 200.0)
        self.assertEqual(res["min_allowed_price"], 5099.0)
        self.assertEqual(res["free_shipping_value"], 100.0)
        self.assertTrue(res["free_shipping_applied"])

        expected_msg = "I can't reduce the item below ₹5,099 under this merchant's pricing rules, but I can apply free shipping."
        self.assertEqual(res["response_message"], expected_msg)

        # Assert ladder tiers structure
        tiers = {step["tier"]: step for step in res["ladder_steps"]}
        self.assertEqual(tiers[1]["name"], "No discount")
        self.assertEqual(tiers[3]["name"], "Free shipping")
        self.assertEqual(tiers[3]["status"], "APPLIED")
        self.assertEqual(tiers[5]["name"], "Coupon up to merchant limit")
        self.assertEqual(tiers[5]["max_discount"], 200.0)
        self.assertEqual(tiers[6]["name"], "Human approval")

    def test_inventory_lifecycle_safe_interruption_benchmark(self):
        """
        Validates user benchmark:
        AI buyer selected: Headphones A — ₹7,499
        Between selection and purchase: Stock = 0
        Decision: Transaction interrupted safely. Payment NOT called.
        Alternative: Headphones B — ₹7,299 (Same ANC class, 42-hour battery, 2-day delivery)
        "Would you like me to replace it?"
        """
        from intelligence.services.inventory_lifecycle import InventoryLifecycleService

        # Out-of-stock product
        headphones_a = Product.objects.create(
            name="Headphones A",
            slug="headphones-a-benchmark",
            price=Decimal("7499.00"),
            stock=0,
            category=self.category,
        )

        # In-stock substitute
        headphones_b = Product.objects.create(
            name="Headphones B",
            slug="headphones-b-benchmark",
            price=Decimal("7299.00"),
            stock=15,
            category=self.category,
        )

        res = InventoryLifecycleService.validate_pipeline(headphones_a)

        self.assertEqual(res["status"], "TRANSACTION_INTERRUPTED_SAFELY")
        self.assertFalse(res["payment_called"])
        self.assertEqual(res["reason"], "Selected product became unavailable.")
        self.assertEqual(res["interrupted_stage"], "final_inventory_validation")

        alt = res["alternative"]
        self.assertEqual(alt["name"], "Headphones B")
        self.assertEqual(alt["price"], 7299.0)
        self.assertIn("Same ANC class", alt["attributes"])
        self.assertIn("42-hour battery", alt["attributes"])
        self.assertIn("2-day delivery", alt["attributes"])

        self.assertIn("Transaction interrupted safely", res["message"])
        self.assertIn("Selected product became unavailable", res["message"])
        self.assertIn("Headphones B — ₹7,299", res["message"])
        self.assertIn("Would you like me to replace it?", res["message"])

    def test_autonomous_campaign_orchestrator_benchmark(self):
        """
        Validates user benchmark:
        Merchant says: "Increase revenue from customers who purchased laptops."
        Agent creates:
          Segment: Laptop buyers
          Goal: Increase 30-day contribution margin
          Eligible products: Mouse, Keyboard, Laptop bag, Extended warranty
          Constraints:
            • discount ≤ 8%
            • inventory ≥ 10
            • no offer within 24h of complaint
            • no more than 2 recommendations/week
          Cadence:
            Day 0: Laptop purchase
            Day 2: Keyboard recommendation
            Day 7: Laptop bag
            Day 20: Warranty
            Day 28: Accessory bundle
        """
        from intelligence.services.campaign_orchestrator import AutonomousCampaignOrchestrator

        # Seed in-stock products
        Product.objects.create(name="Ergonomic Mouse", slug="mouse-test", price=Decimal("999.00"), stock=30, category=self.category)
        Product.objects.create(name="Mechanical Keyboard", slug="keyboard-test", price=Decimal("2499.00"), stock=25, category=self.category)
        Product.objects.create(name="Waterproof Laptop Bag", slug="laptop-bag-test", price=Decimal("1899.00"), stock=20, category=self.category)

        prompt = "Increase revenue from customers who purchased laptops."
        res = AutonomousCampaignOrchestrator.compile_goal_driven_campaign(merchant_prompt=prompt)

        self.assertEqual(res["segment"], "Laptop buyers")
        self.assertEqual(res["goal"], "Increase 30-day contribution margin")

        product_names = [p["name"] for p in res["eligible_products"]]
        self.assertEqual(product_names, ["Mouse", "Keyboard", "Laptop bag", "Extended warranty"])

        for p in res["eligible_products"]:
            self.assertGreaterEqual(p["stock"], 10)
            self.assertTrue(p["inventory_healthy"])

        constraints = res["constraints"]
        self.assertEqual(constraints["max_discount_percent"], 8.0)
        self.assertEqual(constraints["min_inventory"], 10)
        self.assertEqual(constraints["complaint_cooldown_hours"], 24)
        self.assertEqual(constraints["max_recommendations_per_week"], 2)

        cadence = res["cadence"]
        self.assertEqual([c["day"] for c in cadence], [0, 2, 7, 20, 28])
        self.assertEqual(cadence[0]["event"], "Laptop purchase")
        self.assertEqual(cadence[1]["action"], "Keyboard recommendation")
        self.assertEqual(cadence[2]["action"], "Laptop bag")
        self.assertEqual(cadence[3]["action"], "Warranty")
        self.assertEqual(cadence[4]["action"], "Accessory bundle")

    def test_outcome_learning_economic_evaluation_benchmark(self):
        """
        Validates user benchmark:
        Offer A: CTR = 41%, Acceptance = 13%, Margin = ₹250  -> Expected Value = ₹32.50
        Offer B: CTR = 28%, Acceptance = 19%, Margin = ₹520  -> Expected Value = ₹98.80
        Offer B is economically better (+204% expected margin).
        Do not optimize simply for click-through rate.
        """
        from intelligence.services.outcome_learning import OutcomeLearningService

        offer_a = {"name": "Offer A", "ctr": 0.41, "acceptance_rate": 0.13, "margin": 250.0}
        offer_b = {"name": "Offer B", "ctr": 0.28, "acceptance_rate": 0.19, "margin": 520.0}

        res = OutcomeLearningService.evaluate_offer_economics(offer_a, offer_b)

        self.assertEqual(res["winner"], "Offer B")
        self.assertEqual(res["offer_a"]["expected_margin"], 32.50)
        self.assertEqual(res["offer_b"]["expected_margin"], 98.80)
        self.assertEqual(res["economic_advantage"], 66.30)
        self.assertEqual(res["percentage_lift"], 204.0)
        self.assertIn("Offer B is economically better", res["rationale"])
        self.assertEqual(res["optimization_metric"], "EXPECTED_REALIZED_MARGIN")
        self.assertEqual(res["rejected_metric"], "CLICK_THROUGH_RATE_ONLY")

    def test_outcome_learning_nine_business_metrics(self):
        """
        Validates tracking of all 9 business outcome metrics:
        Incremental Revenue, Incremental Margin, AOV, Attach Rate,
        Conversion Rate, Repeat Purchase Rate, Discount Cost, Return Rate, Customer Complaint Rate.
        """
        from intelligence.services.outcome_learning import OutcomeLearningService

        res = OutcomeLearningService.get_business_outcome_metrics()
        metrics = res["metrics"]

        required_keys = [
            "incremental_revenue",
            "incremental_margin",
            "aov",
            "attach_rate",
            "conversion_rate",
            "repeat_purchase_rate",
            "discount_cost",
            "return_rate",
            "customer_complaint_rate"
        ]

        for k in required_keys:
            self.assertIn(k, metrics)
            self.assertIn("value", metrics[k])
            self.assertIn("description", metrics[k])

        self.assertEqual(len(res["funnel_stages"]), 8)
        self.assertIn("ORDER", res["funnel_stages"])
        self.assertIn("MARGIN", res["funnel_stages"])

    def test_customer_fatigue_score_benchmark_rejected_3_offers(self):
        """
        Validates user benchmark:
        Customer rejected 3 offers today.
        Fatigue score = 3 * (+1 shown) + 3 * (+2 rejected) = 9
        Threshold = 6
        Decision: Suppress recommendation
        Agent message: "No additional commercial recommendation will be shown."
        """
        from intelligence.services.customer_fatigue import CustomerFatigueService

        events = {
            "customer_id": "cust_benchmark_fatigue",
            "offers_shown": 3,
            "offers_rejected": 3
        }

        res = CustomerFatigueService.evaluate_suppression(events, threshold=6)

        self.assertEqual(res["fatigue_score"], 9)
        self.assertEqual(res["threshold"], 6)
        self.assertTrue(res["is_suppressed"])
        self.assertEqual(res["response_message"], "No additional commercial recommendation will be shown.")
        self.assertIn("Customer fatigue score (9) exceeds threshold (6)", res["suppression_reason"])

    def test_customer_fatigue_weights_breakdown(self):
        """
        Validates the 6 fatigue weights:
        +1 offer shown
        +2 offer rejected
        +3 offer explicitly declined
        +5 complaint
        +4 recent purchase
        +2 multiple interactions today
        """
        from intelligence.services.customer_fatigue import CustomerFatigueService

        events = {
            "offers_shown": 1,
            "offers_rejected": 1,
            "offers_explicitly_declined": 1,
            "complaints": 1,
            "recent_purchases": 1,
            "multiple_interactions_today": True
        }

        calc = CustomerFatigueService.calculate_fatigue_score(events)
        # 1*1 + 1*2 + 1*3 + 1*5 + 1*4 + 1*2 = 17
        self.assertEqual(calc["fatigue_score"], 17)
        self.assertEqual(calc["breakdown"]["offers_shown"]["points"], 1)
        self.assertEqual(calc["breakdown"]["offers_rejected"]["points"], 2)
        self.assertEqual(calc["breakdown"]["offers_explicitly_declined"]["points"], 3)
        self.assertEqual(calc["breakdown"]["complaints"]["points"], 5)
        self.assertEqual(calc["breakdown"]["recent_purchases"]["points"], 4)
        self.assertEqual(calc["breakdown"]["multiple_interactions_today"]["points"], 2)

    def test_competence_first_personalization_benchmark(self):
        """
        Validates user benchmark:
        Instead of artificial friendliness:
          "Hi bestie! I found something you'll LOVE!!!"
        The agent demonstrates perceived intelligence & competence:
          "Based on your budget and the products you're comparing, this bundle gives you the best value without exceeding ₹5,000."
        """
        from intelligence.services.competence_personalizer import CompetencePersonalizer

        res = CompetencePersonalizer.generate_competent_framing(
            budget=Decimal("5000.00"),
            compared_products=["Sony WH-CH520", "JBL Tune 510BT"],
            ceiling_amount=Decimal("5000.00")
        )

        expected_text = "Based on your budget and the products you're comparing, this bundle gives you the best value without exceeding ₹5,000."
        self.assertEqual(res["message"], expected_text)
        self.assertEqual(res["framing_type"], "COMPETENCE_FIRST")
        self.assertIn("User budget constraints", res["grounding_factors"])
        self.assertIn("Active comparison set", res["grounding_factors"])

    def test_anti_anthropomorphism_audit_rule(self):
        """
        Validates that sycophantic / fake human intimacy is flagged as non-compliant,
        while analytical, competence-first reasoning passes with high intelligence score.
        """
        from intelligence.services.competence_personalizer import CompetencePersonalizer

        # Bad anti-pattern
        bad_text = "Hi bestie! I found something you'll LOVE!!!"
        audit_bad = CompetencePersonalizer.audit_conversational_tone(bad_text)
        self.assertFalse(audit_bad["is_compliant"])
        self.assertTrue(audit_bad["violates_anti_anthropomorphism_rule"])
        self.assertIn("bestie", audit_bad["detected_violations"])
        self.assertIn("love!!!", audit_bad["detected_violations"])

        # Good competent pattern
        good_text = "Based on your budget and the products you're comparing, this bundle gives you the best value without exceeding ₹5,000."
        audit_good = CompetencePersonalizer.audit_conversational_tone(good_text)
        self.assertTrue(audit_good["is_compliant"])
        self.assertFalse(audit_good["violates_anti_anthropomorphism_rule"])
        self.assertEqual(len(audit_good["detected_violations"]), 0)
        self.assertEqual(audit_good["competence_score"], 100)

    def test_why_not_this_rejection_explainability_benchmark(self):
        """
        Validates user benchmark:
        Suppose the customer asks: "Why didn't you recommend the ₹8,999 headphones?"
        The agent answers:
          I excluded them because:
          • Your maximum budget was ₹8,000
          • Battery improvement is only 6%
          • Their contribution margin is lower
          • Another model has higher compatibility with your stated use case
          • Inventory is lower

        Explaining both: selection AND rejection.
        """
        from intelligence.services.explainability_service import FinancialExplainabilityService

        proof = FinancialExplainabilityService.generate_why_not_this_proof(
            rejected_product_name="₹8,999 headphones",
            rejected_price=Decimal("8999.00"),
            user_budget=Decimal("8000.00"),
            battery_improvement_pct=6.0,
            margin_comparison="Their contribution margin is lower",
            compatibility_comparison="Another model has higher compatibility with your stated use case",
            inventory_status="Inventory is lower"
        )

        self.assertEqual(proof["title"], "WHY NOT THIS? (REJECTION EXPLAINABILITY)")
        self.assertEqual(proof["query"], "Why didn't you recommend the ₹8,999 headphones?")
        self.assertEqual(proof["user_budget"], 8000.0)
        self.assertEqual(proof["rejected_item"]["price"], 8999.0)
        self.assertEqual(proof["diagnostics"]["budget_overrun"], 999.0)
        self.assertEqual(proof["diagnostics"]["battery_delta_percent"], 6.0)

        expected_reasons = [
            "Your maximum budget was ₹8,000",
            "Battery improvement is only 6%",
            "Their contribution margin is lower",
            "Another model has higher compatibility with your stated use case",
            "Inventory is lower"
        ]
        self.assertEqual(proof["reasons"], expected_reasons)

        for r in expected_reasons:
            self.assertIn(r, proof["formatted_message"])

        self.assertTrue(proof["formatted_message"].startswith("I excluded them because:"))

    def test_conversational_checkout_intent_shortlist_benchmark(self):
        """
        Validates user benchmark:
        "order lunch under ₹400, here in 30 minutes"
        Pattern:
          Intent → Shortlist against constraints → In-turn explainability → Awaiting confirmation
        """
        from intelligence.services.conversational_checkout import ConversationalCheckoutService

        query = "Order lunch under ₹400, here in 30 minutes"
        res = ConversationalCheckoutService.process_conversational_intent(query)

        self.assertEqual(res["status"], "AWAITING_USER_CONFIRMATION")
        self.assertTrue(res["liability_shield"]["requires_confirmation"])
        self.assertFalse(res["liability_shield"]["payment_initiated"])

        # Product constraints
        self.assertLessEqual(res["product"]["price"], 400.0)
        self.assertLessEqual(res["product"]["delivery_eta_mins"], 30)

        # In-turn explainability check
        self.assertIn("Matched because it's under budget", res["explainability"])
        self.assertIn("before your 30 minutes deadline", res["explainability"])
        self.assertIn(res["explainability"], res["formatted_message"])
        self.assertIn("[CONFIRM_AND_PAY:", res["formatted_message"])

    def test_cart_confirmation_liability_non_negotiable(self):
        """
        Validates Razorpay's liability model:
        The merchant absorbs disputes over what was ordered,
        so the confirmation step is strictly non-negotiable.
        Unconfirmed attempts must fail; confirmed attempts succeed via MCP.
        """
        from intelligence.services.conversational_checkout import ConversationalCheckoutService

        # 1. Unconfirmed attempt: MUST be blocked
        blocked = ConversationalCheckoutService.execute_payment_via_mcp(
            order_id="ord_test_unconfirmed",
            amount=380.0,
            confirmed_by_user=False,
            item_name="Executive Thali"
        )
        self.assertFalse(blocked["success"])
        self.assertEqual(blocked["status"], "BLOCKED_AWAITING_CONFIRMATION")
        self.assertIn("LIABILITY_CHECK_FAILED", blocked["error"])

        # 2. Confirmed attempt: MUST succeed via Razorpay MCP server
        paid = ConversationalCheckoutService.execute_payment_via_mcp(
            order_id="ord_test_confirmed",
            amount=380.0,
            confirmed_by_user=True,
            item_name="Executive Thali"
        )
        self.assertTrue(paid["success"])
        self.assertEqual(paid["status"], "PAID")
        self.assertEqual(paid["payment_method"], "upi_mandate")
        self.assertEqual(paid["mcp_response"]["liability_shield"], "CONFIRMED_BY_USER")

    def test_agent_readable_catalog_sixteen_attributes_and_json_ld(self):
        """
        Validates user benchmark:
        12 floor fields, 15+ total attributes wrapped in Schema.org JSON-LD Product/Offer markup.
        Standard Google Product Taxonomy code.
        """
        from intelligence.services.agent_manifest import AgentManifestService

        prod = Product.objects.filter(is_active=True).first()
        if not prod:
            prod = Product.objects.create(name="Studio Headphones", slug="studio-headphones", price=Decimal("7499.00"), stock=20)

        json_ld = AgentManifestService.generate_schema_org_json_ld(prod)

        # 1. Schema.org validation
        self.assertEqual(json_ld["@context"], "https://schema.org")
        self.assertEqual(json_ld["@type"], "Product")

        # 2. 12 floor fields check
        floor_fields = [
            "gtin13", "mpn", "sku", "name", "brand", "category",
            "categoryCode", "description", "url", "image", "itemCondition", "offers"
        ]
        for f in floor_fields:
            self.assertIn(f, json_ld)

        # 3. Offers structure
        offers = json_ld["offers"]
        self.assertEqual(offers["@type"], "Offer")
        self.assertIn(offers["availability"], ["https://schema.org/InStock", "https://schema.org/OutOfStock"])
        self.assertEqual(offers["priceCurrency"], "INR")
        self.assertIn("inventoryLevel", offers)

        # 4. Standard Taxonomy (Google Product Taxonomy, 4.5x surfacing multiplier)
        self.assertIn("standardTaxonomy", json_ld)
        self.assertEqual(json_ld["standardTaxonomy"]["system"], "Google Product Taxonomy")
        self.assertTrue(len(json_ld["standardTaxonomy"]["code"]) > 0)

        # 5. 15+ attributes floor
        attr_count = AgentManifestService.count_total_attributes(json_ld)
        self.assertGreaterEqual(attr_count, 15)

    def test_three_copies_reconciliation_agreement(self):
        """
        Validates user benchmark:
        Three copies that must agree:
          1. Structured data on the product page
          2. The merchant feed
          3. Read-only API / MCP tool
        All three reconcile on price, currency, and availability.
        Sub-minute inventory sync SLA verified.
        """
        from intelligence.services.catalog_reconciliation import CatalogReconciliationService

        prod = Product.objects.filter(is_active=True).first()
        if not prod:
            prod = Product.objects.create(name="ANC Wireless Headphones", slug="anc-headphones", price=Decimal("4999.00"), stock=15)

        recon = CatalogReconciliationService.reconcile_three_copies(prod)

        self.assertTrue(recon["is_reconciled"])
        self.assertEqual(recon["reconciliation_status"], "RECONCILIATION_VERIFIED")
        self.assertTrue(recon["agreement_matrix"]["price_agreement"])
        self.assertTrue(recon["agreement_matrix"]["currency_agreement"])
        self.assertTrue(recon["agreement_matrix"]["availability_agreement"])
        self.assertTrue(recon["agreement_matrix"]["inventory_level_agreement"])

        # Sub-minute freshness verification
        self.assertTrue(recon["freshness_audit"]["is_sub_minute_fresh"])
        self.assertLess(recon["freshness_audit"]["freshness_age_seconds"], 60.0)
        self.assertEqual(recon["freshness_audit"]["inventory_sync_sla"], "SUB_MINUTE_GUARANTEED")

    def test_dunning_payment_recovery_cadence_and_ledger(self):
        """
        Validates Razorpay payment-recovery / dunning agent:
        On payment.failed webhook:
          1. Retries with intelligent multi-channel cadence (In-app, SMS, Email).
          2. Logs attempts to the ledger.
          3. Escalates to human after exceeding max attempts (3).
          4. Computes recovered revenue before/after.
        """
        from intelligence.services.dunning_service import DunningRecoveryService

        # Attempt 1: In-App
        res1 = DunningRecoveryService.handle_failed_payment_webhook(
            payment_id="pay_fail_001",
            customer_email="buyer1@example.com",
            amount=Decimal("1200.00"),
            attempt_number=1
        )
        self.assertEqual(res1["channel"], "IN_APP")
        self.assertEqual(res1["status"], "RECOVERY_SCHEDULED")
        self.assertTrue(res1["ledger_logged"])

        # Attempt 4: Over max attempts -> Escalation to Human
        res4 = DunningRecoveryService.handle_failed_payment_webhook(
            payment_id="pay_fail_001",
            customer_email="buyer1@example.com",
            amount=Decimal("1200.00"),
            attempt_number=4
        )
        self.assertEqual(res4["status"], "ESCALATED_TO_HUMAN")
        self.assertTrue(res4["is_escalated_to_human"])

        # Simulate successful win-back
        win = DunningRecoveryService.simulate_successful_recovery(res1["task_id"], Decimal("1200.00"))
        self.assertEqual(win["status"], "RECOVERED")
        self.assertEqual(win["recovered_revenue"], 1200.00)

    def test_rto_risk_cod_scoring_and_prepaid_switch(self):
        """
        Validates Razorpay Return / RTO-risk operational agent:
        Scores COD orders transparently (explainable by construction).
        If risk >= 65%, switches order to prepaid-only to prevent courier loss.
        """
        from intelligence.services.rto_risk_service import RtoRiskService

        # High-risk order: remote pincode 800001, prior refusal history, apparel > 3000
        res = RtoRiskService.evaluate_cod_order(
            pincode="800001",
            customer_refusal_history=2,
            order_amount=Decimal("3500.00"),
            category="apparel"
        )
        self.assertGreaterEqual(res["rto_risk_score"], 65)
        self.assertTrue(res["is_high_risk"])
        self.assertEqual(res["action"], "SWITCH_TO_PREPAID_ONLY")
        self.assertTrue(res["explainable_by_construction"])
        self.assertGreater(len(res["explainability"]), 0)

    def test_payout_forecaster_hard_bounded_governance(self):
        """
        Validates Razorpay Cash-flow / payout forecasting agent:
        Projects 7-day settlement trajectories.
        Enforces hard bound: Never moves money or auto-approves > ₹50,000 without human confirmation.
        """
        from intelligence.services.payout_forecaster import PayoutForecastingService

        res = PayoutForecastingService.generate_payout_forecast(days=7, baseline_daily_gmv=Decimal("50000.00"))

        self.assertEqual(res["forecast_period_days"], 7)
        self.assertEqual(res["auto_disbursement_threshold"], 50000.0)
        self.assertTrue(res["hard_bounded_governance"]["compliant"])

        # Check that high-volume days trigger GATED_HUMAN_APPROVAL_REQUIRED
        gated_days = [d for d in res["timeline"] if d["disbursement_governance"]["status"] == "GATED_HUMAN_APPROVAL_REQUIRED"]
        self.assertGreater(len(gated_days), 0)

    def test_x402_machine_payable_merchant_surface_one_round_trip(self):
        """
        Validates x402 machine-payable merchant surface and autonomous AI Buyer Agent:
        1. Request without token -> HTTP 402 Payment Required.
        2. Request with signed token -> Settles in 1 round trip with zero human in the loop.
        """
        from intelligence.services.x402_merchant_surface import X402MerchantSurface, AIBuyerAgent

        # 1. Without signed token -> HTTP 402 Payment Required
        req402 = X402MerchantSurface.process_machine_purchase(
            quote_id="quote_test_001",
            amount=4999.00,
            nonce="nonce_test_001",
            signed_token=None
        )
        self.assertEqual(req402["http_status"], 402)
        self.assertEqual(req402["error"], "PAYMENT_REQUIRED")

        # 2. Autonomous buyer agent execution
        buy_cycle = AIBuyerAgent.execute_autonomous_buying_cycle("studio-headphones")
        self.assertEqual(buy_cycle["agent_action"], "AUTONOMOUS_PURCHASE_CYCLE")
        self.assertTrue(buy_cycle["zero_human_in_loop"])
        self.assertEqual(buy_cycle["settlement_result"]["http_status"], 200)
        self.assertEqual(buy_cycle["settlement_result"]["status"], "PURCHASE_COMPLETED_AUTONOMOUSLY")
        self.assertEqual(buy_cycle["settlement_result"]["round_trips"], 1)

    def test_voice_commerce_audible_gating_and_link_generation(self):
        """
        Validates Razorpay voice/call commerce agent:
        Generates payment link mid-conversation without hanging up.
        Enforces audible gating (verbal confirmation required).
        """
        from intelligence.services.voice_commerce import VoiceCommerceAgent

        # Turn 1: Mid-call payment link generation
        turn1 = VoiceCommerceAgent.process_voice_call_turn("I want to buy the studio headphones right now on this call")
        self.assertEqual(turn1["call_status"], "PAYMENT_LINK_GENERATED_MID_CALL")
        self.assertFalse(turn1["hangup_required"])
        self.assertTrue(turn1["payment_link"]["generated_during_call"])
        self.assertEqual(turn1["audible_gating"]["state"], "AWAITING_SPOKEN_CONFIRMATION")

        # Turn 2: Audible confirmation spoken
        turn2 = VoiceCommerceAgent.process_voice_call_turn("Yes I confirm and authorize payment", call_id=turn1["call_id"])
        self.assertEqual(turn2["call_status"], "PAYMENT_AUTHORIZED_AUDIBLY")
        self.assertTrue(turn2["audible_confirmation_verified"])















