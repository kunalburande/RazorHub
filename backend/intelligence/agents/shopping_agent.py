"""
Shopping Agent — handles cart operations, recommendations, comparisons, deals.
"""
import logging
from . import BaseAgent
from products.models import Product

logger = logging.getLogger(__name__)


class ShoppingAgent(BaseAgent):
    name = "shopping"

    def get_system_prompt(self, context: dict) -> str:
        cart_info = context.get("cart", {})
        cart_items = cart_info.get("items", [])
        platform = context.get("platform", "razorhub")

        if cart_items:
            cart_summary = "User's current cart:\n" + "\n".join([
                f"- {item.get('name', 'Unknown')} × {item.get('quantity', 1)} — ₹{item.get('price', '?')} each (slug: {item.get('slug', '')})"
                for item in cart_items
            ])
        else:
            cart_summary = "User's cart is currently empty."

        catalog_snippet = ""
        catalog = context.get("catalog", [])
        if catalog:
            catalog_snippet = "\n\nAvailable products for recommendations:\n" + "\n".join([
                f"- {p.get('name', '')} (slug: {p.get('slug', '')}, price: ₹{p.get('price', '')}, category: {p.get('category', '')})"
                for p in catalog[:30]
            ])

        return f"""You are a shopping assistant for an e-commerce platform called RazorHub.
You help users with their cart, provide product recommendations, and guide them through checkout.

{cart_summary}
{catalog_snippet}

Guidelines:
- When summarizing the cart, use [PRODUCT:slug] tags so the UI renders clickable cards.
- When recommending products, include [PRODUCT:slug] tags.
- For add-to-cart requests, use [ADD_TO_CART:slug] tags.
- Keep responses brief and helpful (2-5 sentences).
- Use **bold** for product names and prices.
- All prices are in Indian Rupees (₹ / INR).
- Platform: {platform}."""

    def execute(self, messages: list[dict], context: dict) -> dict:
        """Handle shopping-related queries."""
        last_query = messages[-1].get("content", "").lower() if messages else ""

        try:
            content = self.call_gemini(messages, context)
            return {"content": content}
        except Exception as e:
            logger.info(f"Shopping agent fallback: {e}")

            # Check if user asked for deals
            if "deal" in last_query or "discount" in last_query or "offer" in last_query:
                deals = Product.objects.filter(is_active=True).order_by('discount_price', '-rating')[:4]
                lines = ["🔥 **Here are today's top deals on RazorHub:**\n"]
                for p in deals:
                    lines.append(f"• **{p.name}** — **₹{p.current_price}** [PRODUCT:{p.slug}]")
                lines.append("\nTap any product card to grab the deal before it expires! ⚡")
                return {"content": "\n".join(lines)}

            # Check cart summary
            cart_items = context.get("cart", {}).get("items", [])
            if cart_items:
                total = sum(float(i.get('price', 0)) * int(i.get('quantity', 1)) for i in cart_items)
                lines = [f"🛒 **Your Cart Summary:** ({len(cart_items)} item{'s' if len(cart_items) != 1 else ''})\n"]
                for item in cart_items:
                    lines.append(f"• **{item.get('name', 'Product')}** × {item.get('quantity', 1)} — **₹{item.get('price', '0')}**\n  [PRODUCT:{item.get('slug', '')}]")
                lines.append(f"\n💰 **Estimated Total:** **₹{total:,.2f}**")
                lines.append("Would you like to proceed to checkout or look for more items?")
                return {"content": "\n".join(lines)}

            # Empty cart recommendations
            featured = Product.objects.filter(is_active=True, is_featured=True)[:3]
            if not featured:
                featured = Product.objects.filter(is_active=True)[:3]
            lines = ["Your cart is currently empty! Here are some trending products you might like:\n"]
            for p in featured:
                lines.append(f"• **{p.name}** — **₹{p.current_price}** [PRODUCT:{p.slug}]")
            return {"content": "\n".join(lines)}
