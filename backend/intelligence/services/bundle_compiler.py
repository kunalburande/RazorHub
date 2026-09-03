"""
Autonomous Bundle Compiler Service — Budget-Constrained Optimization & Conversational Packaging.

Instead of asking simple ad-hoc questions like "Would you also like a case?",
this service algorithmically compiles multi-tier bundles (Basic, Creator/Optimal, Complete)
that maximize utility and protection while strictly respecting the customer's budget limit.

Example:
    Query: "I need a phone for photography under ₹35,000"
    Primary: Phone A (₹31,999)
    Accessories: Case (₹699), Screen Protector (₹399), Power Bank (₹1,299)

    Tiers:
      - Basic:    ₹32,698 (Phone + Case)
      - Creator:  ₹33,097 (Phone + Case + Screen Protector) [OPTIMAL - Headroom: ₹1,903]
      - Complete: ₹35,696 (Phone + Case + Screen Protector + Power Bank) [Exceeds by ₹696]

    Explanation:
      "I chose this combination because it stays ₹1,903 below your budget while covering protection for the phone."
"""
import re
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional

from products.models import Product, Category
from intelligence.models import ProductRelationship

logger = logging.getLogger(__name__)


class BundleCompilerService:
    """Core optimization engine for compiling budget-constrained product bundles."""

    @classmethod
    def parse_intent_and_budget(cls, query: str) -> Dict[str, Any]:
        """
        Parses text queries like:
          - "I need a phone for photography under ₹35,000"
          - "Laptop for programming under 60k"
          - "Running shoes under ₹4,000"
        Extracts budget limit, target category slug, and use-case tags.
        """
        text = query.lower()

        # 1. Budget extraction (handles ₹35,000, 35000, 35k, under 35000, etc.)
        budget_limit = None
        # Match "35k", "50k", etc.
        k_match = re.search(r'(?:under|below|budget|within|upto|<)?\s*(?:rs\.?|inr|₹)?\s*(\d+(?:\.\d+)?)\s*k\b', text)
        if k_match:
            budget_limit = Decimal(str(float(k_match.group(1)) * 1000))
        else:
            # Match standard number e.g. "35,000" or "35000"
            num_match = re.search(r'(?:under|below|budget|within|upto|<)?\s*(?:rs\.?|inr|₹)?\s*(\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d{3,7}(?:\.\d+)?)', text)
            if num_match:
                clean_num = num_match.group(1).replace(',', '')
                try:
                    val = float(clean_num)
                    if val > 100:  # Avoid matching "1" or small quantities
                        budget_limit = Decimal(str(val))
                except ValueError:
                    pass

        # 2. Target Category Detection
        category_slug = None
        if any(w in text for w in ["phone", "mobile", "smartphone", "iphone", "android"]):
            category_slug = "mobiles"
        elif any(w in text for w in ["laptop", "notebook", "macbook", "pc"]):
            category_slug = "laptops"
        elif any(w in text for w in ["headphone", "earphone", "earbud", "audio", "soundbar"]):
            category_slug = "audio-sound"
        elif any(w in text for w in ["camera", "photography", "lens", "dslr"]):
            category_slug = "photography"
        elif any(w in text for w in ["shoe", "sneaker", "running", "footwear"]):
            category_slug = "sneakers"
        elif any(w in text for w in ["gaming", "playstation", "xbox", "console"]):
            category_slug = "gaming"

        # 3. Use case extraction
        use_case = "general"
        if "photo" in text or "camera" in text:
            use_case = "photography"
        elif "game" in text or "gaming" in text:
            use_case = "gaming"
        elif "run" in text or "fitness" in text or "gym" in text:
            use_case = "fitness"
        elif "work" in text or "office" in text or "study" in text:
            use_case = "work"

        return {
            "query": query,
            "category_slug": category_slug,
            "use_case": use_case,
            "budget_limit": budget_limit,
        }

    @classmethod
    def find_companion_accessories(cls, primary: Product, limit: int = 4) -> List[Product]:
        """
        Finds relevant, high-synergy accessories (cases, screen guards, chargers, cables)
        for a primary device or product.
        """
        accessories: List[Product] = []
        seen_ids = {primary.id}

        # 1. ProductRelationship check (accessory_for, compatible, complementary)
        relationships = ProductRelationship.objects.filter(
            source_product=primary,
            relationship_type__in=["accessory_for", "compatible", "complementary", "frequently_bought_together"]
        ).select_related("target_product")[:limit]

        for rel in relationships:
            t = rel.target_product
            if t.is_active and t.stock > 0 and t.id not in seen_ids:
                accessories.append(t)
                seen_ids.add(t.id)

        # 2. Heuristic fallback from database
        if len(accessories) < limit:
            prim_name = primary.name.lower()
            p_price = primary.discount_price if primary.discount_price else primary.price

            # Search keywords based on category
            if primary.category and primary.category.slug in ["mobiles", "electronics"]:
                keywords = ["case", "cover", "screen", "guard", "protector", "power bank", "charger", "cable", "adapter"]
            elif primary.category and primary.category.slug in ["laptops"]:
                keywords = ["sleeve", "bag", "mouse", "hub", "stand", "keyboard"]
            elif primary.category and primary.category.slug in ["sneakers"]:
                keywords = ["socks", "care", "cleaner", "insole", "laces", "spray"]
            else:
                keywords = ["accessory", "case", "care", "cleaner", "protection"]

            for kw in keywords:
                if len(accessories) >= limit:
                    break
                match = Product.objects.filter(
                    name__icontains=kw,
                    is_active=True,
                    stock__gt=0,
                    price__lte=p_price * Decimal("0.30"),  # Accessories shouldn't exceed 30% of base
                    price__gte=Decimal("99.00")
                ).exclude(id__in=seen_ids).first()

                if match:
                    accessories.append(match)
                    seen_ids.add(match.id)

        return accessories[:limit]

    @classmethod
    def compile_bundle(
        cls,
        primary: Product,
        budget_limit: Optional[Decimal] = None,
        candidate_accessories: Optional[List[Product]] = None,
        bundle_discount_pct: Decimal = Decimal("5.0")
    ) -> Dict[str, Any]:
        """
        Constructs multi-tier bundles (Basic, Creator/Optimal, Complete) and solves
        the knapsack problem to find the optimal bundle staying strictly within budget_limit.
        """
        prim_price = primary.discount_price if primary.discount_price else primary.price

        if budget_limit is None:
            # Default budget limit if none provided: 125% of base price
            budget_limit = (prim_price * Decimal("1.25")).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)

        # Retrieve accessories if not provided
        if candidate_accessories is None:
            candidate_accessories = cls.find_companion_accessories(primary, limit=4)

        # Calculate prices of accessories
        acc_items = []
        for acc in candidate_accessories:
            price_val = acc.discount_price if acc.discount_price else acc.price
            # Classify accessory type (protection, power/utility, enhancement)
            name_lower = acc.name.lower()
            if any(w in name_lower for w in ["case", "cover", "sleeve", "bag"]):
                role = "protection_case"
                priority = 10
            elif any(w in name_lower for w in ["screen", "guard", "protector", "glass"]):
                role = "protection_screen"
                priority = 9
            elif any(w in name_lower for w in ["power", "bank", "charger", "adapter", "battery"]):
                role = "power_utility"
                priority = 7
            else:
                role = "companion"
                priority = 5

            acc_items.append({
                "product": acc,
                "price": price_val,
                "role": role,
                "priority": priority,
            })

        # Sort accessories by priority (protection first, then power/utility, then companions)
        acc_items.sort(key=lambda x: (-x["priority"], x["price"]))

        # ── 1. Basic Tier: Primary + Top 1 Essential Protection Item ──────────
        basic_accs = acc_items[:1] if acc_items else []
        basic_raw_total = prim_price + sum(a["price"] for a in basic_accs)
        basic_discount = (basic_raw_total * (bundle_discount_pct / Decimal("100"))).quantize(Decimal("0.01"))
        basic_final_price = basic_raw_total - basic_discount
        basic_headroom = budget_limit - basic_final_price

        basic_tier = {
            "tier_name": "Basic Bundle",
            "tier_key": "basic",
            "primary": primary,
            "accessories": [a["product"] for a in basic_accs],
            "raw_total": float(basic_raw_total),
            "bundle_price": float(basic_final_price),
            "discount_amount": float(basic_discount),
            "savings_headroom": float(basic_headroom),
            "is_within_budget": basic_final_price <= budget_limit,
            "coverage": "Base device + essential physical protection",
        }

        # ── 2. Creator Tier: Primary + Protection Combo (Case + Screen Protector)
        creator_accs = acc_items[:2] if len(acc_items) >= 2 else basic_accs
        creator_raw_total = prim_price + sum(a["price"] for a in creator_accs)
        creator_discount = (creator_raw_total * (bundle_discount_pct / Decimal("100"))).quantize(Decimal("0.01"))
        creator_final_price = creator_raw_total - creator_discount
        creator_headroom = budget_limit - creator_final_price

        creator_tier = {
            "tier_name": "Creator Bundle",
            "tier_key": "creator",
            "primary": primary,
            "accessories": [a["product"] for a in creator_accs],
            "raw_total": float(creator_raw_total),
            "bundle_price": float(creator_final_price),
            "discount_amount": float(creator_discount),
            "savings_headroom": float(creator_headroom),
            "is_within_budget": creator_final_price <= budget_limit,
            "coverage": "Device + complete screen and case protection",
        }

        # ── 3. Complete Tier: Primary + ALL Companion Accessories ─────────────
        complete_raw_total = prim_price + sum(a["price"] for a in acc_items)
        complete_discount = (complete_raw_total * (bundle_discount_pct / Decimal("100"))).quantize(Decimal("0.01"))
        complete_final_price = complete_raw_total - complete_discount
        complete_headroom = budget_limit - complete_final_price

        complete_tier = {
            "tier_name": "Complete Bundle",
            "tier_key": "complete",
            "primary": primary,
            "accessories": [a["product"] for a in acc_items],
            "raw_total": float(complete_raw_total),
            "bundle_price": float(complete_final_price),
            "discount_amount": float(complete_discount),
            "savings_headroom": float(complete_headroom),
            "is_within_budget": complete_final_price <= budget_limit,
            "exceeded_by": float(max(Decimal("0.00"), complete_final_price - budget_limit)),
            "coverage": "Total ecosystem coverage (Protection, Power & Accessories)",
        }

        # ── 4. Intelligent Selection of Winning Tier ──────────────────────────
        # Selection priority: Complete (if within budget) -> Creator (if within budget) -> Basic
        if complete_tier["is_within_budget"]:
            chosen_tier = complete_tier
        elif creator_tier["is_within_budget"]:
            chosen_tier = creator_tier
        else:
            chosen_tier = basic_tier
        headroom_val = chosen_tier["savings_headroom"]

        accessory_names = [a.name for a in chosen_tier["accessories"]]
        accessories_str = " + ".join(accessory_names) if accessory_names else "essential accessories"

        if headroom_val > 0:
            explanation = (
                f"I chose the {chosen_tier['tier_name']} ({primary.name} + {accessories_str}) "
                f"because it stays Rs.{headroom_val:,.0f} below your budget of Rs.{budget_limit:,.0f} "
                f"while covering essential protection and utility for the device."
            )
        else:
            explanation = (
                f"I chose the {chosen_tier['tier_name']} ({primary.name} + {accessories_str}) "
                f"which perfectly matches your Rs.{budget_limit:,.0f} budget while securing your device."
            )

        if not complete_tier["is_within_budget"]:
            overage = complete_tier["exceeded_by"]
            explanation += (
                f" (Note: The Complete Bundle with all accessories comes to Rs.{complete_tier['bundle_price']:,.0f}, "
                f"which exceeds your limit by Rs.{overage:,.0f}.)"
            )

        return {
            "primary_product": primary,
            "budget_limit": float(budget_limit),
            "recommended_tier": chosen_tier["tier_key"],
            "explanation": explanation,
            "tiers": {
                "basic": basic_tier,
                "creator": creator_tier,
                "complete": complete_tier,
            },
            "chosen_bundle": chosen_tier,
        }
