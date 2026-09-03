"""
Causal Uplift Model Service — Closed-Loop Incremental Lift & Persuasion Modeling.

Traditional recommender systems answer:
    "Which customer/product has the highest purchase probability?"
    -> P(Purchase | Offer)

Our Uplift Agent answers:
    "Will showing this offer actually CAUSE the customer to buy?"
    -> Uplift = P(Purchase | Offer) - P(Purchase | No Offer)

This distinguishes between:
  1. PERSUADABLES (High Uplift): Offer changes behavior (e.g. 0.30 -> 0.52 = +0.22 lift). TARGET HERE!
  2. SURE THINGS (Low Uplift): Customer would buy anyway (e.g. 0.70 -> 0.73 = +0.03 lift). SUPPRESS DISCOUNT.
  3. LOST CAUSES (Low Uplift): Won't buy either way (e.g. 0.03 -> 0.05 = +0.02 lift). CONSERVE IMPRESSIONS.
  4. SLEEPING DOGS (Negative Lift): Offer triggers annoyance or cart fatigue (Uplift < 0). HARD SUPPRESS.
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, Optional

from products.models import Product

logger = logging.getLogger(__name__)


class UpliftQuadrant:
    PERSUADABLE = "PERSUADABLE"
    SURE_THING = "SURE_THING"
    LOST_CAUSE = "LOST_CAUSE"
    SLEEPING_DOG = "SLEEPING_DOG"


class UpliftModelService:
    """Core causal inference and uplift scoring engine."""

    @classmethod
    def estimate_baseline_propensity(
        cls,
        user,
        candidate: Product,
        base_product: Optional[Product] = None
    ) -> Decimal:
        """
        Estimate P(Purchase | No Offer): Organic baseline probability of purchasing
        without any recommendation, banner, or promotional intervention.
        """
        if not user or not user.is_authenticated:
            # Cold / anonymous user default organic baseline
            return Decimal("0.2000")

        p0 = Decimal("0.2000")

        try:
            from orders.models import OrderItem
            from wishlist.models import Wishlist

            # 1. Past purchase frequency in candidate category
            category_orders_count = OrderItem.objects.filter(
                order__user=user,
                product__category=candidate.category
            ).count()

            if category_orders_count >= 3:
                # Habitual buyer in this category -> Sure Thing territory
                p0 += Decimal("0.4500")
            elif category_orders_count >= 1:
                p0 += Decimal("0.2000")

            # 2. Brand loyalty check
            if candidate.brand:
                brand_orders = OrderItem.objects.filter(
                    order__user=user,
                    product__brand=candidate.brand
                ).exists()
                if brand_orders:
                    p0 += Decimal("0.1000")

            # 3. Active wishlist presence (indicates strong pre-existing purchase intent)
            in_wishlist = Wishlist.objects.filter(user=user, products=candidate).exists()
            if in_wishlist:
                p0 += Decimal("0.1500")

        except Exception as e:
            logger.warning(f"[Uplift] Error estimating baseline propensity: {e}")

        # Clamp baseline within [0.05, 0.85]
        return min(Decimal("0.8500"), max(Decimal("0.0500"), p0))

    @classmethod
    def estimate_treatment_propensity(
        cls,
        user,
        candidate: Product,
        base_product: Optional[Product] = None,
        relationship_type: str = "complementary",
        p_baseline: Optional[Decimal] = None
    ) -> Decimal:
        """
        Estimate P(Purchase | Offer): Probability of purchase when actively presented
        with a tailored recommendation or curated bundle offer.
        """
        if p_baseline is None:
            p_baseline = cls.estimate_baseline_propensity(user, candidate, base_product)

        cand_price = candidate.discount_price if candidate.discount_price else candidate.price
        base_price = (base_product.discount_price if base_product.discount_price else base_product.price) if base_product else cand_price

        # Price elasticity ratio
        ratio = float(cand_price / base_price) if base_price > 0 else 1.0

        # Base treatment boost depending on offer price ratio
        if ratio <= 0.16:
            offer_lift_potential = Decimal("0.2500")  # Impulse add-on has high persuasion power
        elif ratio <= 0.35:
            offer_lift_potential = Decimal("0.2200")  # Curated companion (e.g. care kit)
        elif ratio <= 0.50:
            offer_lift_potential = Decimal("0.1200")  # Substantial companion
        else:
            offer_lift_potential = Decimal("0.0600")

        # Relationship affinity bonus
        if relationship_type in ["accessory_for", "frequently_bought_together", "frequently_bought_with"]:
            offer_lift_potential += Decimal("0.0400")

        # Social proof modifier
        rating = float(candidate.rating or 4.0)
        if rating >= 4.5:
            offer_lift_potential += Decimal("0.0300")
        elif rating < 3.8:
            offer_lift_potential -= Decimal("0.0400")

        # Diminishing returns formula: as baseline approaches 1.0, additional lift room shrinks
        # Uplift ceiling = (1.0 - p_baseline)
        headroom = Decimal("1.0000") - p_baseline
        actual_lift = offer_lift_potential * headroom

        p_treatment = (p_baseline + actual_lift).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        return min(Decimal("0.9500"), max(Decimal("0.0500"), p_treatment))

    @classmethod
    def classify_customer_quadrant(
        cls,
        p_baseline: Decimal,
        p_treatment: Decimal,
        uplift: Decimal
    ) -> Dict[str, str]:
        """
        Classifies the customer-offer interaction into one of four causal quadrants
        and determines the strategic merchant action.
        """
        if uplift < Decimal("0.0000"):
            return {
                "quadrant": UpliftQuadrant.SLEEPING_DOG,
                "label": "Sleeping Dog",
                "action": "HARD_SUPPRESS",
                "badge_color": "rose",
                "rationale": "Recommendation causes customer irritation or checkout friction. Do not present offer."
            }

        if p_baseline >= Decimal("0.6000") and uplift < Decimal("0.1000"):
            return {
                "quadrant": UpliftQuadrant.SURE_THING,
                "label": "Sure Thing",
                "action": "SUPPRESS_DISCOUNT",
                "badge_color": "amber",
                "rationale": f"Customer already intends to purchase organically (P0={float(p_baseline):.2f}). Offering discounts or spending recommendation slots produces negligible incremental lift (+{float(uplift):.2f})."
            }

        if p_treatment < Decimal("0.1200") and uplift < Decimal("0.0800"):
            return {
                "quadrant": UpliftQuadrant.LOST_CAUSE,
                "label": "Lost Cause",
                "action": "CONSERVE_BUDGET",
                "badge_color": "slate",
                "rationale": f"Customer shows low conversion propensity regardless of offer (P1={float(p_treatment):.2f}). Conserve recommendation real estate."
            }

        return {
            "quadrant": UpliftQuadrant.PERSUADABLE,
            "label": "Persuadable",
            "action": "PRIORITIZE_OFFER",
            "badge_color": "emerald",
            "rationale": f"High incremental uplift (+{float(uplift):.2f}). Presenting this offer directly alters customer behavior from P0={float(p_baseline):.2f} to P1={float(p_treatment):.2f}."
        }

    @classmethod
    def evaluate_uplift(
        cls,
        user,
        candidate: Product,
        base_product: Optional[Product] = None,
        relationship_type: str = "complementary",
        baseline_override: Optional[Decimal] = None,
        treatment_override: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculates complete causal uplift metrics for a candidate recommendation.
        Returns:
            - p_baseline: P(Purchase | No Offer)
            - p_treatment: P(Purchase | Offer)
            - uplift: P1 - P0
            - quadrant: PERSUADABLE | SURE_THING | LOST_CAUSE | SLEEPING_DOG
            - strategy: Merchant decisioning directive
        """
        p_base = baseline_override if baseline_override is not None else cls.estimate_baseline_propensity(user, candidate, base_product)
        p_treat = treatment_override if treatment_override is not None else cls.estimate_treatment_propensity(user, candidate, base_product, relationship_type, p_base)

        uplift = (p_treat - p_base).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        classification = cls.classify_customer_quadrant(p_base, p_treat, uplift)

        return {
            "p_baseline": float(p_base),
            "p_treatment": float(p_treat),
            "uplift": float(uplift),
            "quadrant": classification["quadrant"],
            "quadrant_label": classification["label"],
            "action": classification["action"],
            "badge_color": classification["badge_color"],
            "rationale": classification["rationale"],
        }
