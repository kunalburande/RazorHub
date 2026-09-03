"""
Profit Optimizer Service — Maximizes Incremental Contribution Margin & Opportunity Score.

Instead of optimizing AOV (Average Order Value), this service selects candidate actions
that produce the highest expected incremental contribution margin without damaging
conversion, customer experience, or inventory health:

  Opportunity Score =
      Expected Incremental Margin
      × Customer Fit
      × Inventory Health
      × Timing
      × Conversion Confidence
      − Discount Cost
      − Cannibalization Risk
      − Customer Fatigue Risk

  Where:
      Expected Incremental Margin = P(acceptance) × Contribution Margin
"""
import logging
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Any, List, Optional

from django.db.models import Q
from products.models import Product
from intelligence.models import ProductRelationship, MerchantConfig

logger = logging.getLogger(__name__)


class ProfitOptimizerService:
    """Core intelligence engine for profit-first recommendations and upsells."""

    @classmethod
    def compute_contribution_margin(
        cls,
        candidate: Product,
        base_product: Optional[Product] = None,
        is_upgrade: bool = False
    ) -> Decimal:
        """
        Compute contribution margin in INR:
          - Add-on / Cross-sell: Selling Price - Cost Price
          - Upgrade: (Price_cand - Price_base) - (Cost_cand - Cost_base)
        """
        cand_price = candidate.discount_price if candidate.discount_price else candidate.price
        cand_cost = candidate.cost_price if candidate.cost_price else (cand_price * Decimal("0.70"))

        if is_upgrade and base_product:
            base_price = base_product.discount_price if base_product.discount_price else base_product.price
            base_cost = base_product.cost_price if base_product.cost_price else (base_price * Decimal("0.70"))
            
            incremental_revenue = cand_price - base_price
            incremental_cost = cand_cost - base_cost
            margin = incremental_revenue - incremental_cost
            return max(Decimal("0.00"), margin)

        margin = cand_price - cand_cost
        return max(Decimal("0.00"), margin)

    @classmethod
    def estimate_acceptance_probability(
        cls,
        candidate: Product,
        base_product: Optional[Product] = None,
        relationship_type: str = "complementary",
        is_upgrade: bool = False
    ) -> Decimal:
        """
        Calculate probability P(acceptance) based on price elasticity ratio,
        relationship affinity, and social proof.
        """
        cand_price = candidate.discount_price if candidate.discount_price else candidate.price
        base_price = (base_product.discount_price if base_product.discount_price else base_product.price) if base_product else cand_price

        # 1. Price elasticity ratio
        if base_price > 0:
            ratio = float(cand_price / base_price)
        else:
            ratio = 1.0

        if is_upgrade:
            # Upgrades typically have lower conversion rates: 10% - 15%
            p_base = 0.12
            if ratio < 1.3:
                p_base = 0.15
            elif ratio > 1.8:
                p_base = 0.09
        else:
            # Add-on price elasticity curve aligned with benchmark e-commerce data:
            # Low ticket impulse (<= 15% base price, e.g. socks @ 300 on 2000): 35%
            # Moderate companion (16% - 30% base price, e.g. care kit @ 500 on 2000): 32%
            # High companion (31% - 45% base price, e.g. insoles @ 800 on 2000): 18%
            # Heavy companion (> 45% base price): 12%
            if ratio <= 0.16:
                p_base = 0.35
            elif ratio <= 0.30:
                p_base = 0.32
            elif ratio <= 0.45:
                p_base = 0.18
            else:
                p_base = 0.12

        # 2. Relationship Type Affinity modifier
        rel_mod = 0.0
        if relationship_type in ["accessory_for", "frequently_bought_together", "frequently_bought_with"]:
            # Core accessories maintain high conversion rates
            rel_mod += 0.00
        elif relationship_type == "compatible":
            rel_mod += 0.01
        elif relationship_type == "substitute":
            rel_mod -= 0.04

        # 3. Social proof modifier (Rating & Review Count)
        rating_mod = 0.0
        r = float(candidate.rating or 4.0)
        if r >= 4.7:
            rating_mod += 0.02
        elif r < 3.8:
            rating_mod -= 0.04

        prob = p_base + rel_mod + rating_mod
        prob = max(0.05, min(0.65, prob))
        return Decimal(str(round(prob, 4)))

    @classmethod
    def calculate_customer_fit(
        cls,
        candidate: Product,
        user=None
    ) -> Decimal:
        """Customer Fit multiplier in [0.80, 1.20]."""
        if not user or not user.is_authenticated:
            return Decimal("1.00")

        score = Decimal("1.00")
        try:
            from orders.models import OrderItem
            past_orders = OrderItem.objects.filter(order__user=user)
            if past_orders.filter(product__category=candidate.category).exists():
                score += Decimal("0.10")
            if candidate.brand and past_orders.filter(product__brand=candidate.brand).exists():
                score += Decimal("0.05")
        except Exception:
            pass

        return min(Decimal("1.20"), max(Decimal("0.80"), score))

    @classmethod
    def calculate_inventory_health_multiplier(
        cls,
        candidate: Product
    ) -> Decimal:
        """
        Inventory Health multiplier in [0.70, 1.20].
        Overstocked/slow items get a boost (to liquidate working capital).
        Critically low stock gets penalized (to prevent premature stockouts).
        """
        stock = candidate.stock
        if hasattr(candidate, "inventory"):
            stock = candidate.inventory.quantity

        if stock <= 5:
            return Decimal("0.70")
        elif stock <= 15:
            return Decimal("0.90")
        elif stock >= 50:
            return Decimal("1.15")
        elif stock >= 30:
            return Decimal("1.05")

        return Decimal("1.00")

    @classmethod
    def calculate_timing_multiplier(
        cls,
        timing_context: str = "product_details"
    ) -> Decimal:
        """Contextual timing multiplier in [0.85, 1.15]."""
        timing_map = {
            "post_purchase": Decimal("1.15"),
            "checkout_step": Decimal("1.08"),
            "product_details": Decimal("1.00"),
            "cart_drawer": Decimal("1.05"),
            "browse": Decimal("0.85"),
        }
        return timing_map.get(timing_context, Decimal("1.00"))

    @classmethod
    def calculate_cannibalization_risk(
        cls,
        candidate: Product,
        base_product: Optional[Product] = None,
        relationship_type: str = "complementary",
        is_upgrade: bool = False
    ) -> Decimal:
        """
        Cannibalization Risk in INR:
        Only applies when recommending a substitute or alternative that might REPLACE
        a higher-margin product. For accessories, complementary products, and upgrades,
        cannibalization is 0.
        """
        if is_upgrade or not base_product:
            return Decimal("0.00")

        # Accessories and complementary additions NEVER cannibalize base purchases
        if relationship_type in ["accessory_for", "frequently_bought_together", "frequently_bought_with", "complementary", "compatible"]:
            return Decimal("0.00")

        if relationship_type in ["substitute", "alternative_to"]:
            cand_margin = cls.compute_contribution_margin(candidate)
            base_margin = cls.compute_contribution_margin(base_product)
            if base_margin > cand_margin:
                risk = (base_margin - cand_margin) * Decimal("0.15")
                return risk.quantize(Decimal("0.01"))

        return Decimal("0.00")

    @classmethod
    def calculate_opportunity_score(
        cls,
        candidate: Product,
        base_product: Optional[Product] = None,
        user=None,
        relationship_type: str = "complementary",
        timing_context: str = "product_details",
        discount_offered: Decimal = Decimal("0.00"),
        is_upgrade: bool = False,
        dismissed_count: int = 0,
        baseline_override: Optional[Decimal] = None,
        treatment_override: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Computes Opportunity Score using Causal Uplift Modeling:
          Uplift (tau) = P(Purchase | Offer) - P(Purchase | No Offer)
          Causal Incremental Margin = tau * Contribution Margin

          Opportunity Score =
              (Causal Incremental Margin * CF * IH * Timing * CC)
              - Discount Cost - Cannibalization Risk - Customer Fatigue Risk
        """
        from intelligence.services.uplift_service import UpliftModelService

        cand_price = candidate.discount_price if candidate.discount_price else candidate.price
        cand_cost = candidate.cost_price if candidate.cost_price else (cand_price * Decimal("0.70"))
        
        # 1. Contribution Margin
        contribution_margin = cls.compute_contribution_margin(candidate, base_product, is_upgrade=is_upgrade)

        # 2. Causal Uplift Evaluation: P(buy|offer) - P(buy|no offer)
        uplift_data = UpliftModelService.evaluate_uplift(
            user=user,
            candidate=candidate,
            base_product=base_product,
            relationship_type=relationship_type,
            baseline_override=baseline_override,
            treatment_override=treatment_override
        )
        p_baseline = Decimal(str(uplift_data["p_baseline"]))
        p_treatment = Decimal(str(uplift_data["p_treatment"]))
        uplift = Decimal(str(uplift_data["uplift"]))
        quadrant = uplift_data["quadrant"]
        quadrant_label = uplift_data["quadrant_label"]

        # Causal Expected Incremental Margin: only counts profit created BY the offer!
        causal_incremental_margin = (contribution_margin * max(Decimal("0.01"), uplift)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        expected_incremental_margin = (contribution_margin * p_treatment).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 3. Multipliers
        customer_fit = cls.calculate_customer_fit(candidate, user)
        inventory_health = cls.calculate_inventory_health_multiplier(candidate)
        timing = cls.calculate_timing_multiplier(timing_context)
        conversion_confidence = Decimal("0.95") if relationship_type in ["accessory_for", "frequently_bought_together"] else Decimal("0.85")

        multiplied_margin = causal_incremental_margin * customer_fit * inventory_health * timing * conversion_confidence

        # 4. Penalties
        discount_cost = (discount_offered * p_treatment).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        cannibalization_risk = cls.calculate_cannibalization_risk(candidate, base_product, relationship_type=relationship_type, is_upgrade=is_upgrade)
        customer_fatigue_risk = Decimal(str(dismissed_count * 8.00))

        # 5. Final Opportunity Score
        raw_score = multiplied_margin - discount_cost - cannibalization_risk - customer_fatigue_risk
        opportunity_score = max(Decimal("0.00"), raw_score).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        if is_upgrade:
            reason = f"Premium upgrade (+Rs.{contribution_margin:.0f} margin, Uplift: +{int(uplift*100)}% [{quadrant_label}])."
        else:
            reason = f"High-uplift companion (+{int(uplift*100)}% lift, {quadrant_label}). Yields Rs.{causal_incremental_margin:.0f} true incremental profit over organic baseline."

        return {
            "product": candidate,
            "is_upgrade": is_upgrade,
            "relationship_type": relationship_type,
            "price": float(cand_price),
            "cost_price": float(cand_cost),
            "contribution_margin": float(contribution_margin),
            "acceptance_probability": float(p_treatment),
            "p_baseline": float(p_baseline),
            "p_treatment": float(p_treatment),
            "uplift": float(uplift),
            "quadrant": quadrant,
            "quadrant_label": quadrant_label,
            "expected_incremental_margin": float(expected_incremental_margin),
            "causal_incremental_margin": float(causal_incremental_margin),
            "customer_fit": float(customer_fit),
            "inventory_health": float(inventory_health),
            "timing": float(timing),
            "conversion_confidence": float(conversion_confidence),
            "discount_cost": float(discount_cost),
            "cannibalization_risk": float(cannibalization_risk),
            "customer_fatigue_risk": float(customer_fatigue_risk),
            "opportunity_score": float(opportunity_score),
            "reason": reason,
        }

    @classmethod
    def get_ranked_recommendations(
        cls,
        base_product: Product,
        user=None,
        timing_context: str = "product_details",
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Fetches candidate recommendations, computes Opportunity Scores for each,
        and returns them ranked by descending Opportunity Score.
        """
        candidates: List[Dict[str, Any]] = []
        seen_ids = {base_product.id}

        # 1. Check existing ProductRelationship data
        relationships = ProductRelationship.objects.filter(
            source_product=base_product
        ).select_related("target_product", "target_product__category", "target_product__brand")[:10]

        for rel in relationships:
            target = rel.target_product
            if target.id not in seen_ids and target.is_active and target.stock > 0:
                is_upgrade = (rel.relationship_type == "upgrade_to")
                metric = cls.calculate_opportunity_score(
                    candidate=target,
                    base_product=base_product,
                    user=user,
                    relationship_type=rel.relationship_type,
                    timing_context=timing_context,
                    is_upgrade=is_upgrade
                )
                candidates.append(metric)
                seen_ids.add(target.id)

        # 2. Add complementary products
        companion_qs = Product.objects.filter(
            is_active=True,
            stock__gt=0,
            price__lte=base_product.price * Decimal("0.80"),
            price__gte=Decimal("150.00")
        ).exclude(id__in=seen_ids).select_related("category", "brand")[:15]

        for comp in companion_qs:
            metric = cls.calculate_opportunity_score(
                candidate=comp,
                base_product=base_product,
                user=user,
                relationship_type="complementary",
                timing_context=timing_context,
                is_upgrade=False
            )
            candidates.append(metric)
            seen_ids.add(comp.id)

        # 3. Add premium upgrades
        upgrade_qs = Product.objects.filter(
            category=base_product.category,
            price__gt=base_product.price,
            is_active=True,
            stock__gt=0
        ).exclude(id__in=seen_ids).order_by("price")[:3]

        for upg in upgrade_qs:
            metric = cls.calculate_opportunity_score(
                candidate=upg,
                base_product=base_product,
                user=user,
                relationship_type="upgrade_to",
                timing_context=timing_context,
                is_upgrade=True
            )
            candidates.append(metric)
            seen_ids.add(upg.id)

        candidates.sort(key=lambda x: x["opportunity_score"], reverse=True)
        return candidates[:limit]
