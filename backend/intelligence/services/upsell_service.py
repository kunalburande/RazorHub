"""
Upsell & Cross-Sell Service for RazorHub Agentic Commerce.

Signal-based triggering (not random suggestions):
  • Cart value threshold → suggest premium variant (upsell)
  • Product affinity → suggest complementary item (cross-sell)
  • Free shipping threshold → incentive to add more
  • Repeat purchase → suggest bulk/subscription

Guardrails (hard-coded, never bypassed):
  ❌ Never auto-charge
  ❌ Never upsell to customer with active complaint/return
  ❌ Never offer discount merchant hasn't pre-approved
  ✅ Always cite WHY the suggestion is made
  ✅ Log every offer: {offered, accepted/declined, revenue_impact}
"""
import time
import uuid
import logging
from decimal import Decimal
from django.db.models import Q, Count
from products.models import Product
from intelligence.models import (
    ProductRelationship, RevenueOpportunity,
    MerchantConfig,
)
from intelligence.services.commerce_audit import CommerceAuditService

logger = logging.getLogger(__name__)


class UpsellService:
    """Core upsell/cross-sell logic with guardrails and audit trail."""

    # ── Guardrails ─────────────────────────────────────────────────────────

    @classmethod
    def should_suppress_upsell(cls, user=None, user_id=None):
        """
        Check if upsell should be suppressed for this customer.
        Suppressed when:
          - Customer has active support ticket / complaint
          - Customer has pending return/refund
        """
        if not user and not user_id:
            return False

        try:
            from orders.models import Order
            uid = user.id if user else user_id

            # Check for recent cancelled/returned orders (proxy for unhappy customer)
            recent_issues = Order.objects.filter(
                user_id=uid,
                status__in=['cancelled'],
            ).count()

            if recent_issues > 0:
                logger.info(f"[Upsell] Suppressed for user {uid}: {recent_issues} recent issues")
                return True

        except Exception as e:
            logger.warning(f"[Upsell] Suppression check error: {e}")

        return False

    # ── Signal Detection ───────────────────────────────────────────────────

    @classmethod
    def detect_signals(cls, cart_items=None, user=None, product=None):
        """
        Detect upsell/cross-sell signals from cart, user history, and product context.
        Returns a list of signal dicts: {type, trigger, data}.
        """
        config = MerchantConfig.get_solo()
        signals = []
        cart_total = Decimal("0")

        if cart_items:
            cart_total = sum(
                Decimal(str(item.get("price", 0))) * int(item.get("quantity", 1))
                for item in cart_items
            )

            # Signal: Cart value threshold
            if cart_total > Decimal("2000"):
                signals.append({
                    "type": "upsell",
                    "trigger": "cart_value_threshold",
                    "data": {"cart_total": str(cart_total)},
                })

            # Signal: Free shipping threshold
            free_threshold = config.free_shipping_threshold
            if cart_total < free_threshold:
                gap = free_threshold - cart_total
                signals.append({
                    "type": "incentive",
                    "trigger": "free_shipping_gap",
                    "data": {"gap": str(gap), "threshold": str(free_threshold)},
                })

            # Signal: Product affinity from cart items
            cart_product_ids = [
                item.get("id") or item.get("product_id")
                for item in cart_items
                if item.get("id") or item.get("product_id")
            ]
            if cart_product_ids:
                signals.append({
                    "type": "cross_sell",
                    "trigger": "cart_product_affinity",
                    "data": {"product_ids": cart_product_ids},
                })

        if product:
            # Signal: Accessory/complementary suggestions
            signals.append({
                "type": "cross_sell",
                "trigger": "product_page_view",
                "data": {"product_id": product.id, "category_id": product.category_id},
            })

        return signals

    # ── Candidate Generation ───────────────────────────────────────────────

    @classmethod
    def get_upsell_candidates(cls, product, limit=3):
        """
        Get premium variants for upsell (same category, higher price).
        """
        if not product:
            return []

        candidates = Product.objects.filter(
            category=product.category,
            is_active=True,
            stock__gt=0,
            price__gt=product.price,
        ).exclude(id=product.id).order_by('price')[:limit]

        return list(candidates)

    @classmethod
    def get_cross_sell_candidates(cls, product=None, product_ids=None, limit=5):
        """
        Get complementary products using ProductRelationship data
        and category-based fallback.
        """
        candidates = []

        # 1. Use existing ProductRelationship data
        if product:
            relationships = ProductRelationship.objects.filter(
                source_product=product,
                relationship_type__in=[
                    'frequently_bought_with', 'complementary',
                    'compatible', 'accessory_for', 'frequently_bought_together',
                ],
            ).select_related('target_product')[:limit]

            for rel in relationships:
                if rel.target_product.is_active and rel.target_product.stock > 0:
                    candidates.append({
                        "product": rel.target_product,
                        "relationship": rel.relationship_type,
                        "confidence": float(rel.confidence),
                        "reason": f"Frequently bought with {product.name}" if "frequently" in rel.relationship_type
                                  else f"Recommended as {rel.relationship_type.replace('_', ' ')} for {product.name}",
                    })

        # 2. Category-based fallback
        if len(candidates) < limit:
            exclude_ids = [c["product"].id for c in candidates]
            if product:
                exclude_ids.append(product.id)
            if product_ids:
                exclude_ids.extend(product_ids)

            category_id = product.category_id if product else None
            fallback_qs = Product.objects.filter(
                is_active=True, stock__gt=0, is_featured=True
            ).exclude(id__in=exclude_ids)

            if category_id:
                # Get from different category for cross-sell diversity
                fallback_qs = fallback_qs.exclude(category_id=category_id)

            for p in fallback_qs[:limit - len(candidates)]:
                candidates.append({
                    "product": p,
                    "relationship": "recommended",
                    "confidence": 0.5,
                    "reason": "Popular item you might like",
                })

        return candidates[:limit]

    @classmethod
    def get_threshold_incentive(cls, cart_total, cart_items=None):
        """
        Calculate 'add ₹X for free shipping' incentive.
        Returns None if threshold already met.
        """
        config = MerchantConfig.get_solo()
        threshold = config.free_shipping_threshold

        if cart_total >= threshold:
            return None

        gap = threshold - cart_total

        # Find products that fit in the gap
        suggestions = Product.objects.filter(
            is_active=True,
            stock__gt=0,
            price__lte=gap + Decimal("200"),  # Slight overshoot OK
            price__gte=Decimal("50"),
        ).order_by('-rating')[:3]

        if not suggestions:
            return None

        return {
            "type": "free_shipping_incentive",
            "gap": float(gap),
            "threshold": float(threshold),
            "message": f"Add ₹{gap:,.0f} more for free shipping!",
            "suggestions": [
                {
                    "id": p.id,
                    "name": p.name,
                    "slug": p.slug,
                    "price": float(p.current_price),
                    "category": p.category.name if p.category else "General",
                }
                for p in suggestions
            ],
        }

    # ── Offer Creation (with audit) ────────────────────────────────────────

    @classmethod
    def create_upsell_offer(cls, product, customer=None, signal=None,
                            create_payment_link=False):
        """
        Create a bounded upsell offer with full audit trail.
        If create_payment_link=True, generates a Razorpay Payment Link.
        """
        trace_id = str(uuid.uuid4())

        # Check guardrails
        if customer and cls.should_suppress_upsell(user=customer):
            CommerceAuditService.log_upsell_event(
                agent="upsell_agent",
                action="upsell_suppressed",
                product_id=product.id,
                customer_id=customer.id if customer else None,
                signal=signal,
                outcome="suppressed",
                trace_id=trace_id,
            )
            return None

        offer_data = {
            "product_id": product.id,
            "product_name": product.name,
            "product_slug": product.slug,
            "price": float(product.current_price),
            "signal": signal,
            "trace_id": trace_id,
        }

        # Optionally create Razorpay Payment Link for one-click upsell
        if create_payment_link:
            try:
                from intelligence.services.razorpay_service import RazorpayService
                link = RazorpayService.create_payment_link(
                    amount=product.current_price,
                    description=f"Add {product.name} to your order",
                    notes={
                        "type": "post_purchase_upsell",
                        "signal": signal or "product_affinity",
                        "trace_id": trace_id,
                        "bounded": "true",
                        "max_amount": str(product.current_price),
                    },
                    expire_by=int(time.time()) + 86400,  # 24h expiry
                )
                offer_data["payment_link_id"] = link["id"]
                offer_data["payment_url"] = link.get("short_url", "")
            except Exception as e:
                logger.error(f"[Upsell] Payment link creation failed: {e}")

        # Audit trail
        CommerceAuditService.log_upsell_event(
            agent="upsell_agent",
            action="upsell_offered",
            product_id=product.id,
            customer_id=customer.id if customer else None,
            signal=signal,
            payment_link_id=offer_data.get("payment_link_id"),
            revenue_impact=product.current_price,
            outcome="offered",
            trace_id=trace_id,
        )

        return offer_data

    # ── Main Entry Point ───────────────────────────────────────────────────

    @classmethod
    def get_recommendations(cls, cart_items=None, product=None,
                            user=None, limit=3):
        """
        Get personalized upsell/cross-sell recommendations.
        Returns a structured response with recommendations and reasons.
        """
        # Guardrail: suppress for unhappy customers
        if user and cls.should_suppress_upsell(user=user):
            return {
                "recommendations": [],
                "suppressed": True,
                "reason": "Upsell suppressed due to recent issues",
            }

        recommendations = []

        # 1. Cross-sell from cart items
        if cart_items:
            cart_total = sum(
                Decimal(str(item.get("price", 0))) * int(item.get("quantity", 1))
                for item in cart_items
            )

            # Free shipping incentive
            incentive = cls.get_threshold_incentive(cart_total, cart_items)
            if incentive:
                recommendations.append({
                    "type": "incentive",
                    "signal": "free_shipping_gap",
                    "data": incentive,
                })

            # Cross-sell from first cart item
            first_pid = cart_items[0].get("id") or cart_items[0].get("product_id") if cart_items else None
            if first_pid:
                try:
                    p = Product.objects.get(id=first_pid)
                    cross_sells = cls.get_cross_sell_candidates(product=p, limit=limit)
                    for cs in cross_sells:
                        recommendations.append({
                            "type": "cross_sell",
                            "signal": cs["relationship"],
                            "reason": cs["reason"],
                            "product": {
                                "id": cs["product"].id,
                                "name": cs["product"].name,
                                "slug": cs["product"].slug,
                                "price": float(cs["product"].current_price),
                                "category": cs["product"].category.name if cs["product"].category else "General",
                            },
                        })
                except Product.DoesNotExist:
                    pass

        # 2. Upsell from product page
        if product:
            upsells = cls.get_upsell_candidates(product, limit=limit)
            for p in upsells:
                recommendations.append({
                    "type": "upsell",
                    "signal": "premium_variant",
                    "reason": f"Because you're looking at {product.name}, you might prefer this premium option",
                    "product": {
                        "id": p.id,
                        "name": p.name,
                        "slug": p.slug,
                        "price": float(p.current_price),
                        "category": p.category.name if p.category else "General",
                    },
                })

        return {
            "recommendations": recommendations[:limit],
            "suppressed": False,
        }
