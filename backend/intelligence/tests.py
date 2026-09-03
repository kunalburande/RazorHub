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



