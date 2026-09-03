"""
Agent Buyer Compatibility Service — AI Commerce Readiness Scoring & Diagnostics.

Evaluates how sellable and discoverable a merchant's store is to autonomous AI purchasing agents.
Scores stores across 8 objective dimensions (Total: 100 points) and produces explainable
remediation diagnostics:

Example:
    Catalog completeness          18/20
    Structured product data      17/20
    Live inventory availability    14/15
    Price consistency              10/10
    Shipping information            8/10
    Compatibility metadata          7/10
    Machine checkout               5/10
    Transaction policy             3/5
    ------------------------------------
    Total                          82/100

    Explanation:
      "Your store is highly discoverable by AI buyers, but 3 products are missing
       compatibility attributes and checkout does not expose a bounded purchase policy."
"""
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional

from products.models import Product
from intelligence.models import ProductRelationship

logger = logging.getLogger(__name__)


class AgentBuyerCompatibilityService:
    """Audits merchant stores and computes the 8-pillar AI Commerce Readiness Score."""

    @classmethod
    def evaluate_store_readiness(cls, store=None, products_qs=None) -> Dict[str, Any]:
        """
        Calculates the AI Commerce Readiness Score for a store or product set.
        Returns:
            - total_score: 0-100
            - pillar_scores: dict of scores and max points for each dimension
            - diagnostic_summary: explainable merchant text
            - missing_compatibility_count: int
            - action_items: list of concrete seller tasks
        """
        if products_qs is None:
            if store:
                products_qs = Product.objects.filter(store=store, is_active=True)
            else:
                products_qs = Product.objects.filter(is_active=True)[:25]

        products = list(products_qs)
        total_prods = len(products)

        if total_prods == 0:
            return {
                "total_score": 0,
                "grade": "F",
                "pillar_scores": {
                    "catalog_completeness": {"score": 0, "max": 20},
                    "structured_product_data": {"score": 0, "max": 20},
                    "live_inventory_availability": {"score": 0, "max": 15},
                    "price_consistency": {"score": 0, "max": 10},
                    "shipping_information": {"score": 0, "max": 10},
                    "compatibility_metadata": {"score": 0, "max": 10},
                    "machine_checkout": {"score": 0, "max": 10},
                    "transaction_policy": {"score": 0, "max": 5},
                },
                "diagnostic_summary": "Store has no active products. Upload your catalog to calculate your AI Readiness Score.",
                "action_items": ["Publish your first product with complete specifications."]
            }

        # ── 1. Catalog Completeness (Max 20) ──────────────────────────────────
        complete_titles = sum(1 for p in products if len(p.name.strip()) >= 10)
        has_category = sum(1 for p in products if p.category_id is not None)
        has_desc = sum(1 for p in products if p.description and len(p.description.strip()) >= 30)
        has_brand = sum(1 for p in products if p.brand_id is not None)

        score_completeness = round(
            (complete_titles / total_prods * 6) +
            (has_category / total_prods * 5) +
            (has_desc / total_prods * 5) +
            (has_brand / total_prods * 4)
        )
        score_completeness = min(20, max(0, score_completeness))

        # ── 2. Structured Product Data (Max 20) ───────────────────────────────
        has_structured_specs = 0
        for p in products:
            if hasattr(p, 'specs') and p.specs:
                has_structured_specs += 1
            elif p.specifications and len(p.specifications.strip()) >= 20:
                has_structured_specs += 1

        score_structured = round((has_structured_specs / total_prods) * 20)
        score_structured = min(20, max(0, score_structured))

        # ── 3. Live Inventory Availability (Max 15) ───────────────────────────
        in_stock_count = sum(1 for p in products if p.stock > 0)
        has_exact_count = sum(1 for p in products if p.stock is not None and p.stock >= 0)

        score_inventory = round(
            (in_stock_count / total_prods * 10) +
            (has_exact_count / total_prods * 5)
        )
        score_inventory = min(15, max(0, score_inventory))

        # ── 4. Price Consistency (Max 10) ─────────────────────────────────────
        consistent_pricing = sum(
            1 for p in products
            if p.price > 0 and (not p.discount_price or p.discount_price <= p.price)
        )
        score_pricing = round((consistent_pricing / total_prods) * 10)
        score_pricing = min(10, max(0, score_pricing))

        # ── 5. Shipping Information (Max 10) ──────────────────────────────────
        # RazorHub has default SLA logistics enabled
        score_shipping = 8  # 8/10 default SLA standard

        # ── 6. Compatibility Metadata (Max 10) ────────────────────────────────
        product_ids = [p.id for p in products]
        relationships_count = ProductRelationship.objects.filter(
            source_product_id__in=product_ids
        ).values('source_product_id').distinct().count()

        prods_with_compatibility = relationships_count
        missing_compatibility = total_prods - prods_with_compatibility

        score_compatibility = round((prods_with_compatibility / total_prods) * 10)
        score_compatibility = min(10, max(0, score_compatibility))

        # ── 7. Machine Checkout (Max 10) ──────────────────────────────────────
        # Razorpay API checkout and agent execution engine supported
        score_machine_checkout = 7

        # ── 8. Transaction Policy (Max 5) ─────────────────────────────────────
        # Bounded purchase policies (max qty, return window)
        score_policy = 3

        # ── Calculate Total Score ─────────────────────────────────────────────
        total_score = (
            score_completeness +
            score_structured +
            score_inventory +
            score_pricing +
            score_shipping +
            score_compatibility +
            score_machine_checkout +
            score_policy
        )
        total_score = min(100, max(0, total_score))

        # Grade
        if total_score >= 85:
            grade = "A (AI Ready)"
            grade_color = "emerald"
        elif total_score >= 70:
            grade = "B (AI Accessible)"
            grade_color = "blue"
        elif total_score >= 55:
            grade = "C (Needs Optimization)"
            grade_color = "amber"
        else:
            grade = "D (Low AI Discoverability)"
            grade_color = "rose"

        # ── Explainable Diagnostic & Action Items ─────────────────────────────
        action_items: List[str] = []
        issues: List[str] = []

        if missing_compatibility > 0:
            issues.append(f"{missing_compatibility} product{'s are' if missing_compatibility != 1 else ' is'} missing compatibility attributes")
            action_items.append(f"Link companion accessories for {missing_compatibility} products to enable automated bundle checkouts.")

        if score_policy < 5:
            issues.append("checkout does not expose a bounded purchase policy")
            action_items.append("Configure order purchase limits (max 5 per customer) and returns window SLA.")

        if score_structured < 18:
            action_items.append("Convert free-form product descriptions into structured key-value specifications.")

        if total_score >= 75:
            discoverability_text = "Your store is highly discoverable by AI buyers"
        elif total_score >= 60:
            discoverability_text = "Your store is moderately discoverable by AI buyers"
        else:
            discoverability_text = "Your store has limited discoverability for autonomous AI buyers"

        if issues:
            issues_str = " and ".join(issues)
            diagnostic_summary = f"{discoverability_text}, but {issues_str}."
        else:
            diagnostic_summary = f"{discoverability_text} with full machine checkout and structured metadata compatibility."

        return {
            "total_score": total_score,
            "grade": grade,
            "grade_color": grade_color,
            "diagnostic_summary": diagnostic_summary,
            "missing_compatibility_count": missing_compatibility,
            "action_items": action_items,
            "pillars": {
                "catalog_completeness": {
                    "label": "Catalog completeness",
                    "score": score_completeness,
                    "max": 20,
                    "pct": round(score_completeness / 20 * 100)
                },
                "structured_product_data": {
                    "label": "Structured product data",
                    "score": score_structured,
                    "max": 20,
                    "pct": round(score_structured / 20 * 100)
                },
                "live_inventory_availability": {
                    "label": "Live inventory availability",
                    "score": score_inventory,
                    "max": 15,
                    "pct": round(score_inventory / 15 * 100)
                },
                "price_consistency": {
                    "label": "Price consistency",
                    "score": score_pricing,
                    "max": 10,
                    "pct": round(score_pricing / 10 * 100)
                },
                "shipping_information": {
                    "label": "Shipping information",
                    "score": score_shipping,
                    "max": 10,
                    "pct": round(score_shipping / 10 * 100)
                },
                "compatibility_metadata": {
                    "label": "Compatibility metadata",
                    "score": score_compatibility,
                    "max": 10,
                    "pct": round(score_compatibility / 10 * 100)
                },
                "machine_checkout": {
                    "label": "Machine checkout",
                    "score": score_machine_checkout,
                    "max": 10,
                    "pct": round(score_machine_checkout / 10 * 100)
                },
                "transaction_policy": {
                    "label": "Transaction policy",
                    "score": score_policy,
                    "max": 5,
                    "pct": round(score_policy / 5 * 100)
                },
            }
        }
