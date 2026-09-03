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
        raw_query = messages[-1].get("content", "") if messages else ""
        last_query = raw_query.lower()

        # Check if user query contains budget / bundle compilation intent
        from intelligence.services.bundle_compiler import BundleCompilerService
        from django.db.models import Q
        parsed = BundleCompilerService.parse_intent_and_budget(raw_query)

        if parsed["budget_limit"] is not None or "bundle" in last_query:
            budget = parsed["budget_limit"] or Decimal("50000.00")
            cat_slug = parsed["category_slug"]

            prod_qs = Product.objects.filter(is_active=True, price__lte=budget, stock__gt=0)
            if cat_slug:
                prod_qs = prod_qs.filter(category__slug=cat_slug)
            if parsed["use_case"] == "photography":
                prod_qs = prod_qs.filter(Q(name__icontains="pro") | Q(name__icontains="camera") | Q(description__icontains="camera") | Q(category__slug="photography"))

            primary = prod_qs.order_by('-price', '-rating').first()
            if not primary:
                primary = Product.objects.filter(is_active=True, price__lte=budget, stock__gt=0).order_by('-price').first()

            if primary:
                bundle_result = BundleCompilerService.compile_bundle(
                    primary=primary,
                    budget_limit=budget
                )
                chosen = bundle_result["chosen_bundle"]
                lines = [
                    f"🎯 **Autonomous Bundle Compiler — {chosen['tier_name']}**\n",
                    bundle_result["explanation"],
                    "\n**Selected Package Items:**",
                    f"• **{primary.name}** — **₹{primary.current_price:,.2f}** [PRODUCT:{primary.slug}]"
                ]
                for acc in chosen["accessories"]:
                    lines.append(f"• **{acc.name}** — **₹{acc.current_price:,.2f}** [PRODUCT:{acc.slug}]")

                lines.append(f"\n📦 **Package Total:** **₹{chosen['bundle_price']:,.2f}** (Budget: ₹{budget:,.2f})")
                if chosen["savings_headroom"] > 0:
                    lines.append(f"💰 **Budget Headroom Remaining:** **₹{chosen['savings_headroom']:,.2f}**")

                acc_slugs = ",".join(a.slug for a in chosen["accessories"])
                lines.append(f"\nTap to add the complete package: [ADD_BUNDLE:{primary.slug},{acc_slugs}]")
                return {"content": "\n".join(lines), "bundle": bundle_result}

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
