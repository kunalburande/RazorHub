"""
Upsell & Cross-Sell Agent — Signal-Based Product Recommendations.

Watches cart contents, product context, and browsing signals to recommend
higher-value or complementary products. Every recommendation is:
  • Signal-driven (not random)
  • Gated (never auto-charges)
  • Explainable (cites WHY the suggestion is made)
  • Audited (logged with revenue impact)
"""
import logging
from . import BaseAgent
from intelligence.services.upsell_service import UpsellService
from products.models import Product

logger = logging.getLogger(__name__)


class UpsellAgent(BaseAgent):
    name = "upsell"

    def get_system_prompt(self, context: dict) -> str:
        cart_info = context.get("cart", {})
        cart_items = cart_info.get("items", [])
        platform = context.get("platform", "razorhub")

        if cart_items:
            cart_summary = "User's current cart:\n" + "\n".join([
                f"- {item.get('name', 'Unknown')} × {item.get('quantity', 1)} — ₹{item.get('price', '?')}"
                for item in cart_items
            ])
        else:
            cart_summary = "User's cart is empty."

        return f"""You are the Upsell & Cross-Sell Agent for {platform}.
You recommend complementary or upgraded products based on what the user is looking at or has in their cart.

{cart_summary}

Rules:
- Always explain WHY you're suggesting the product (e.g., "Because you bought a laptop, here's a compatible mouse").
- Use [PRODUCT:slug] tags for product cards.
- Never push aggressively — be helpful, not salesy.
- Never auto-add anything to cart — always ask first.
- Keep responses concise (2-4 sentences + product suggestions).
- Use ₹ for currency (INR)."""

    def execute(self, messages: list[dict], context: dict) -> dict:
        """
        Generate upsell/cross-sell recommendations based on detected signals.
        """
        cart_items = context.get("cart", {}).get("items", [])
        user = context.get("user")
        last_query = messages[-1].get("content", "") if messages else ""

        # Check if user is looking at a specific product
        product = None
        product_slug = context.get("product_slug")
        if product_slug:
            try:
                product = Product.objects.select_related('category', 'brand').get(slug=product_slug)
            except Product.DoesNotExist:
                pass

        # Guardrail: suppress for unhappy customers
        if user and UpsellService.should_suppress_upsell(user=user):
            return {
                "content": "I'm here to help! What are you looking for today?",
                "upsell_suppressed": True,
            }

        # Get recommendations
        result = UpsellService.get_recommendations(
            cart_items=cart_items,
            product=product,
            user=user,
            limit=4,
        )

        recommendations = result.get("recommendations", [])

        if not recommendations:
            # Fallback: show featured products
            try:
                content = self.call_gemini(messages, context)
                return {"content": content}
            except Exception:
                featured = Product.objects.filter(is_active=True, is_featured=True)[:3]
                if featured:
                    lines = ["Here are some products you might like:\n"]
                    for p in featured:
                        lines.append(f"• **{p.name}** — **₹{p.current_price:,.2f}** [PRODUCT:{p.slug}]")
                    return {"content": "\n".join(lines)}
                return {"content": "I'd love to help you find something great! What are you looking for?"}

        # Build response with recommendations
        response_parts = []

        # Handle incentive (free shipping)
        incentives = [r for r in recommendations if r["type"] == "incentive"]
        product_recs = [r for r in recommendations if r["type"] in ("cross_sell", "upsell")]

        if incentives:
            incentive = incentives[0]["data"]
            response_parts.append(f"🚚 **{incentive['message']}**\n")

            if incentive.get("suggestions"):
                response_parts.append("Here are some items that would qualify you:\n")
                for s in incentive["suggestions"][:2]:
                    response_parts.append(
                        f"• **{s['name']}** — **₹{s['price']:,.2f}** [PRODUCT:{s['slug']}]"
                    )
                response_parts.append("")

        if product_recs:
            if any(r["type"] == "upsell" for r in product_recs):
                response_parts.append("✨ **You might also like these premium options:**\n")
            else:
                response_parts.append("🔗 **Recommended for you:**\n")

            for rec in product_recs[:3]:
                prod = rec.get("product", {})
                reason = rec.get("reason", "Popular choice")
                response_parts.append(
                    f"• **{prod.get('name', '')}** — **₹{prod.get('price', 0):,.2f}**\n"
                    f"  _{reason}_\n"
                    f"  [PRODUCT:{prod.get('slug', '')}]"
                )

        response_parts.append("\nWould you like to add any of these to your cart? 🛒")

        # Try to polish with LLM
        raw_content = "\n".join(response_parts)
        try:
            polish_messages = messages.copy()
            polish_messages.append({
                "role": "assistant",
                "content": f"[UPSELL RECOMMENDATIONS]\n{raw_content}"
            })
            polish_messages.append({
                "role": "user",
                "content": "Make this product recommendation more conversational and engaging. Keep all product names, prices, and [PRODUCT:slug] tags exactly as they are."
            })
            polished = self.call_gemini(polish_messages, context)
            if polished and len(polished) > 20:
                raw_content = polished
        except Exception:
            pass  # Use raw content

        # Build tool calls for frontend rendering
        tool_calls = []
        for rec in product_recs[:3]:
            prod = rec.get("product", {})
            tool_calls.append({
                "type": "upsell_offer",
                "product_id": prod.get("id"),
                "product_name": prod.get("name", ""),
                "product_slug": prod.get("slug", ""),
                "price": prod.get("price", 0),
                "signal": rec.get("signal", ""),
                "reason": rec.get("reason", ""),
            })

        return {
            "content": raw_content,
            "toolCalls": tool_calls if tool_calls else None,
        }
