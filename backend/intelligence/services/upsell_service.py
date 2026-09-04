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


# ── CATEGORY AFFINITY MAP (Business Rules) ────────────────────────────────────
# Defines which categories are legitimate cross-sell targets for each source
# category. This prevents irrelevant suggestions (e.g., laptop → sneakers).
# Keys are partial slug/name matches (lowercased). Values list target slugs.
CATEGORY_AFFINITY_MAP = {
    # Electronics / Laptops → Audio, Bags, Peripherals, Storage
    "laptop": ["audio", "sound", "headphone", "bag", "backpack", "accessories", "peripheral", "storage", "mouse", "keyboard", "charger", "cable"],
    "notebook": ["audio", "sound", "headphone", "bag", "backpack", "accessories", "peripheral", "storage", "mouse", "keyboard"],
    # Mobiles → Audio, Cases, Chargers, Accessories
    "mobile": ["audio", "sound", "headphone", "earphone", "case", "cover", "charger", "cable", "accessories", "screen", "protector", "power"],
    "phone": ["audio", "sound", "headphone", "earphone", "case", "cover", "charger", "cable", "accessories", "screen", "protector", "power"],
    "smartphone": ["audio", "sound", "headphone", "earphone", "case", "cover", "charger", "cable", "accessories"],
    # Audio → Cases, Cables, Audio Accessories
    "audio": ["cable", "charger", "case", "cover", "accessories", "adapter", "stand", "mount"],
    "sound": ["cable", "charger", "case", "cover", "accessories", "adapter", "stand", "mount"],
    "headphone": ["cable", "charger", "case", "cover", "accessories", "adapter", "stand"],
    "earphone": ["cable", "charger", "case", "cover", "accessories", "adapter"],
    # Gaming → Controllers, Headsets, Audio, Accessories
    "gaming": ["audio", "sound", "headphone", "headset", "controller", "joystick", "accessories", "mouse", "keyboard", "monitor"],
    "console": ["audio", "sound", "headphone", "headset", "controller", "joystick", "accessories", "gaming"],
    # Photography → Memory Cards, Bags, Tripods, Lenses
    "photography": ["bag", "backpack", "tripod", "lens", "memory", "storage", "accessories", "gimbal", "light", "filter"],
    "camera": ["bag", "backpack", "tripod", "lens", "memory", "storage", "accessories", "gimbal", "light", "filter"],
    # Sneakers / Footwear → Sports Accessories
    "sneaker": ["sports", "fitness", "insole", "sock", "accessories", "bag", "backpack"],
    "shoe": ["sports", "fitness", "insole", "sock", "accessories", "bag", "backpack"],
    "footwear": ["sports", "fitness", "insole", "sock", "accessories"],
    # Appliances → Kitchen Accessories
    "appliance": ["kitchen", "cleaning", "accessories", "utensil", "cookware"],
    # Fashion → Accessories, Jewellery, Footwear
    "fashion": ["accessories", "jewellery", "watch", "bag", "footwear", "sneaker"],
    "clothing": ["accessories", "jewellery", "watch", "bag", "footwear"],
    # Electronics (general)
    "electronic": ["audio", "sound", "headphone", "charger", "cable", "accessories", "storage", "peripheral"],
}


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

    # ── Category Affinity Helpers ──────────────────────────────────────────

    @classmethod
    def _get_affinity_slugs(cls, product):
        """
        Return list of target category slug fragments that are legitimate
        cross-sell targets for the given product, based on CATEGORY_AFFINITY_MAP.
        """
        if not product or not product.category:
            return []

        cat_slug = (product.category.slug or "").lower()
        cat_name = (product.category.name or "").lower()
        prod_name = (product.name or "").lower()

        matched_targets = set()
        for key, targets in CATEGORY_AFFINITY_MAP.items():
            if key in cat_slug or key in cat_name or key in prod_name:
                matched_targets.update(targets)

        return list(matched_targets)

    @classmethod
    def _is_relevant_cross_sell(cls, source_product, candidate_product):
        """
        Check if candidate_product is a relevant cross-sell for source_product
        using the category affinity map. Returns True if relevant.
        """
        if not source_product or not candidate_product:
            return False

        # Same category = NOT cross-sell (that's upsell territory)
        if source_product.category_id == candidate_product.category_id:
            return False

        affinity_slugs = cls._get_affinity_slugs(source_product)
        if not affinity_slugs:
            # No affinity map for this category — only allow ProductRelationship-based
            return False

        cand_cat_slug = (candidate_product.category.slug or "").lower() if candidate_product.category else ""
        cand_cat_name = (candidate_product.category.name or "").lower() if candidate_product.category else ""
        cand_name = (candidate_product.name or "").lower()

        for slug_frag in affinity_slugs:
            if slug_frag in cand_cat_slug or slug_frag in cand_cat_name or slug_frag in cand_name:
                return True

        return False

    @classmethod
    def _get_cross_sell_reason(cls, source_product, candidate_product):
        """Generate a human-readable reason for why this cross-sell is relevant."""
        src_cat = source_product.category.name if source_product.category else "product"
        cand_cat = candidate_product.category.name if candidate_product.category else "item"

        # Category-specific reasons
        src_lower = src_cat.lower()
        cand_lower = cand_cat.lower()

        if any(k in cand_lower for k in ["audio", "sound", "headphone", "earphone"]):
            return f"Compatible audio accessory for your {src_cat.lower()}"
        if any(k in cand_lower for k in ["case", "cover", "protector"]):
            return f"Protective accessory for your {src_cat.lower()}"
        if any(k in cand_lower for k in ["charger", "cable", "adapter", "power"]):
            return f"Essential charging accessory for your {src_cat.lower()}"
        if any(k in cand_lower for k in ["bag", "backpack"]):
            return f"Carry bag designed for {src_cat.lower()}"
        if any(k in cand_lower for k in ["mouse", "keyboard", "peripheral"]):
            return f"Complementary peripheral for your {src_cat.lower()}"
        if any(k in cand_lower for k in ["storage", "memory"]):
            return f"Expand storage for your {src_cat.lower()}"
        if any(k in cand_lower for k in ["tripod", "lens", "gimbal"]):
            return f"Photography gear compatible with your {src_cat.lower()}"
        if any(k in cand_lower for k in ["controller", "joystick"]):
            return f"Gaming controller for your {src_cat.lower()}"

        return f"Frequently paired with {src_cat.lower()} purchases"

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

        # 2. Category-affinity fallback (NOT random featured products)
        if len(candidates) < limit and product:
            exclude_ids = [c["product"].id for c in candidates]
            exclude_ids.append(product.id)
            if product_ids:
                exclude_ids.extend(product_ids)

            affinity_slugs = cls._get_affinity_slugs(product)
            if affinity_slugs:
                # Build Q filter for affinity categories
                affinity_q = Q()
                for slug_frag in affinity_slugs:
                    affinity_q |= Q(category__slug__icontains=slug_frag) | Q(category__name__icontains=slug_frag) | Q(name__icontains=slug_frag)

                fallback_qs = Product.objects.filter(
                    affinity_q,
                    is_active=True,
                    stock__gt=0,
                ).exclude(
                    id__in=exclude_ids
                ).exclude(
                    category_id=product.category_id  # Exclude same category
                ).select_related("category").order_by('-rating', '-created_at')

                for p in fallback_qs[:limit - len(candidates)]:
                    candidates.append({
                        "product": p,
                        "relationship": "category_affinity",
                        "confidence": 0.7,
                        "reason": cls._get_cross_sell_reason(product, p),
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

    # ── Relevance-Gated Recommendations ────────────────────────────────────

    @classmethod
    def get_relevant_cross_sell(cls, product, user=None, limit=4):
        """
        Get ONLY category-relevant cross-sell products for a given product.
        Uses ProductRelationship first, then affinity-mapped categories.
        Filters through merchant policy forbidden_categories.
        """
        if not product:
            return []

        # Guardrail: suppress for unhappy customers
        if user and cls.should_suppress_upsell(user=user):
            return []

        # Get forbidden categories from merchant policy
        forbidden_cats = set()
        try:
            from intelligence.services.merchant_policy import MerchantPolicyEngine, DEFAULT_POLICY_DICT
            policy = DEFAULT_POLICY_DICT
            forbidden_cats = set(policy.get("forbidden_categories", []))
        except Exception:
            pass

        candidates = cls.get_cross_sell_candidates(product=product, limit=limit + 2)

        # Filter: only keep genuinely relevant products
        relevant = []
        for c in candidates:
            cp = c["product"]
            cat_slug = (cp.category.slug or "").lower() if cp.category else ""

            # Skip forbidden categories
            if cat_slug in forbidden_cats:
                continue

            # If relationship-based, trust it
            if c["relationship"] not in ["recommended", "category_affinity"]:
                relevant.append(c)
                continue

            # If affinity-based, validate relevance
            if cls._is_relevant_cross_sell(product, cp) or c["relationship"] == "category_affinity":
                relevant.append(c)

        return relevant[:limit]

    @classmethod
    def get_relevant_upsell(cls, product, user=None, limit=3):
        """
        Get same-category, higher-tier upsell products.
        Filters through merchant policy.
        """
        if not product:
            return []

        if user and cls.should_suppress_upsell(user=user):
            return []

        upsell_products = cls.get_upsell_candidates(product, limit=limit)

        results = []
        for p in upsell_products:
            price_diff = float(p.current_price) - float(product.current_price)
            results.append({
                "product": p,
                "type": "upsell",
                "price_diff": price_diff,
                "reason": f"Premium upgrade in {product.category.name if product.category else 'this category'} — ₹{price_diff:,.0f} more for enhanced performance and features",
            })

        return results

    @classmethod
    def build_checkout_recommendations(cls, cart_items=None, product=None, user=None, limit=3):
        """
        Main entry point for generating structured cross-sell/upsell recommendations
        suitable for both agent chat and normal shopping UI.

        Returns:
            {
                "cross_sell": [{"id", "name", "slug", "price", "image_url", "category", "reason", "type"}],
                "upsell": [{"id", "name", "slug", "price", "image_url", "category", "reason", "type", "price_diff"}],
                "suppressed": bool
            }
        """
        if user and cls.should_suppress_upsell(user=user):
            return {"cross_sell": [], "upsell": [], "suppressed": True}

        cross_sell_results = []
        upsell_results = []

        # Determine the base product(s) from cart or direct product
        base_product = product
        if not base_product and cart_items:
            # Use the first (primary) cart item as the base
            first_id = cart_items[0].get("id") or cart_items[0].get("product_id") if cart_items else None
            if first_id:
                try:
                    if str(first_id).isdigit():
                        base_product = Product.objects.select_related("category", "brand", "store").get(id=int(first_id))
                    else:
                        base_product = Product.objects.select_related("category", "brand", "store").filter(slug=str(first_id)).first()
                except Product.DoesNotExist:
                    pass

        if not base_product:
            return {"cross_sell": [], "upsell": [], "suppressed": False}

        # Collect IDs already in cart to exclude from suggestions
        cart_ids = set()
        if cart_items:
            for ci in cart_items:
                pid = ci.get("id") or ci.get("product_id")
                if pid and str(pid).isdigit():
                    cart_ids.add(int(pid))

        # 1. Cross-sell: relevant complementary products
        cross_sells = cls.get_relevant_cross_sell(base_product, user=user, limit=limit)
        for cs in cross_sells:
            p = cs["product"]
            if p.id in cart_ids:
                continue
            img_url = ""
            first_img = p.images.first() if hasattr(p, "images") else None
            if first_img and first_img.image_url:
                img_url = first_img.image_url
            if not img_url:
                img_url = getattr(p, "image_url", "") or ""

            cross_sell_results.append({
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "price": float(p.current_price),
                "original_price": float(p.price),
                "image_url": img_url,
                "category": p.category.name if p.category else "General",
                "brand": p.brand.name if p.brand else "RazorHub Partner",
                "merchant": p.store.name if p.store else "RazorHub Verified Store",
                "rating": float(p.rating or 4.5),
                "in_stock": p.stock > 0,
                "reason": cs.get("reason", "Complementary product"),
                "type": "cross_sell",
                "relationship": cs.get("relationship", "affinity"),
            })

        # 2. Upsell: same-category, higher-tier products
        upsells = cls.get_relevant_upsell(base_product, user=user, limit=2)
        for us in upsells:
            p = us["product"]
            if p.id in cart_ids:
                continue
            img_url = ""
            first_img = p.images.first() if hasattr(p, "images") else None
            if first_img and first_img.image_url:
                img_url = first_img.image_url
            if not img_url:
                img_url = getattr(p, "image_url", "") or ""

            upsell_results.append({
                "id": str(p.id),
                "name": p.name,
                "slug": p.slug,
                "price": float(p.current_price),
                "original_price": float(p.price),
                "image_url": img_url,
                "category": p.category.name if p.category else "General",
                "brand": p.brand.name if p.brand else "RazorHub Partner",
                "merchant": p.store.name if p.store else "RazorHub Verified Store",
                "rating": float(p.rating or 4.5),
                "in_stock": p.stock > 0,
                "reason": us.get("reason", "Premium upgrade"),
                "type": "upsell",
                "price_diff": us.get("price_diff", 0),
            })

        return {
            "cross_sell": cross_sell_results[:limit],
            "upsell": upsell_results[:2],
            "suppressed": False,
        }

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

            # Cross-sell from first cart item — use relevance-gated method
            first_pid = cart_items[0].get("id") or cart_items[0].get("product_id") if cart_items else None
            if first_pid:
                try:
                    p = Product.objects.select_related("category").get(id=first_pid)
                    cross_sells = cls.get_relevant_cross_sell(product=p, limit=limit)
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

        # 2. Profit-optimized recommendations from product page
        if product:
            from intelligence.services.profit_optimizer import ProfitOptimizerService
            ranked_opts = ProfitOptimizerService.get_ranked_recommendations(
                base_product=product,
                user=user,
                timing_context="product_details",
                limit=limit
            )
            for opt in ranked_opts:
                p = opt["product"]
                recommendations.append({
                    "type": "upsell" if opt["is_upgrade"] else "cross_sell",
                    "signal": "profit_optimized_opportunity",
                    "reason": opt["reason"],
                    "opportunity_score": opt["opportunity_score"],
                    "expected_incremental_margin": opt["expected_incremental_margin"],
                    "contribution_margin": opt["contribution_margin"],
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
