"""
Search Agent — handles product discovery, semantic search, catalog browsing.
Queries the RazorHub product database directly.
"""
import logging
from . import BaseAgent
from products.models import Product

logger = logging.getLogger(__name__)


class SearchAgent(BaseAgent):
    name = "search"

    def get_system_prompt(self, context: dict) -> str:
        return """You are a product search specialist for an e-commerce platform called RazorHub.
You receive a user's search query along with product catalog data.
Your job is to find and present the most relevant products in a helpful, conversational way.

Guidelines:
- Present products with their name, price, and a brief highlight.
- Use **bold** for product names and prices.
- If multiple products match, show the top 3-5 most relevant.
- Keep responses concise (3-6 sentences max).
- Always mention product availability (in stock / low stock / out of stock).
- Use the exact product slugs provided — embed them as [PRODUCT:slug] tags so the UI can render interactive product cards.
- Currency is Indian Rupees (₹ / INR) for RazorHub."""

    def _search_products(self, query: str, limit: int = 8) -> list[dict]:
        """Search products by keyword matching against name, description, category, brand."""
        from django.db.models import Q

        q = query.lower().strip()
        words = q.split()

        filters = Q()
        for word in words:
            if len(word) < 2 or word in ["show", "find", "some", "best", "good", "with", "from", "for", "please", "want"]:
                continue
            filters |= (
                Q(name__icontains=word) |
                Q(description__icontains=word) |
                Q(category__name__icontains=word) |
                Q(brand__name__icontains=word)
            )

        qs = Product.objects.filter(is_active=True)
        if filters:
            products = qs.filter(filters).select_related('category', 'brand', 'store')[:limit]
        else:
            products = qs.order_by('-rating', '-created_at')[:limit]

        return [
            {
                "name": p.name,
                "slug": p.slug,
                "price": str(p.current_price),
                "stock": p.stock,
                "category": p.category.name if p.category else "General",
                "brand": p.brand.name if p.brand else None,
                "rating": str(p.rating),
                "store": p.store.name if p.store else None,
            }
            for p in products
        ]

    def execute(self, messages: list[dict], context: dict) -> dict:
        """Search for products and generate a response."""
        query = context.get("refined_query", "")
        if not query and messages:
            query = messages[-1].get("content", "")

        results = self._search_products(query)

        # Build context for the LLM
        if results:
            product_context = "\n".join([
                f"- {p['name']} (slug: {p['slug']}, price: ₹{p['price']}, stock: {p['stock']}, "
                f"category: {p['category']}, rating: {p['rating']})"
                for p in results
            ])
        else:
            popular = Product.objects.filter(is_active=True).order_by('-rating')[:5]
            product_context = "No exact matches found. Here are some popular products:\n" + "\n".join([
                f"- {p.name} (slug: {p.slug}, price: ₹{p.current_price}, category: {p.category.name if p.category else 'General'})"
                for p in popular
            ])

        search_messages = messages.copy()
        if search_messages:
            search_messages[-1] = {
                "role": "user",
                "content": f"{search_messages[-1].get('content', '')}\n\n[CATALOG SEARCH RESULTS]\n{product_context}"
            }

        try:
            content = self.call_gemini(search_messages, context)
            return {"content": content}
        except Exception as e:
            logger.info(f"Search agent fallback rule generation: {e}")
            if results:
                lines = [f"I found these products for **{query}**:\n"]
                for p in results[:4]:
                    stock_str = f"({p['stock']} in stock)" if p['stock'] > 0 else "(Out of stock)"
                    lines.append(f"• **{p['name']}** — **₹{p['price']}** {stock_str}\n  [PRODUCT:{p['slug']}]")
                lines.append("\nTap any product card above to view details or add it to your cart! 🛍️")
                return {"content": "\n".join(lines)}
            return {"content": "I couldn't find any products matching your search right now. Browse our categories from the navigation bar!"}
