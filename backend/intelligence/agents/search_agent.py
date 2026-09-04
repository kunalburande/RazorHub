"""
Search Agent — handles product discovery, semantic search, catalog browsing, and side-by-side product comparisons.
Queries the RazorHub product database directly with precise keyword extraction and category filtering.
"""
import logging
import re
from . import BaseAgent
from products.models import Product, Category
from products.serializers import ProductListSerializer

logger = logging.getLogger(__name__)

STOP_WORDS = {
    "show", "find", "some", "best", "good", "with", "from", "for", "please",
    "want", "top", "rated", "all", "the", "me", "give", "display", "get",
    "any", "i", "a", "an", "items", "products", "item", "product", "recommend",
    "suggest", "available", "current", "catalog", "what", "deals", "active", "today",
    "tell", "list", "look", "search", "under", "below", "less", "than", "more", "price"
}


class SearchAgent(BaseAgent):
    name = "search"

    def get_system_prompt(self, context: dict) -> str:
        return """You are an expert product shopping assistant for RazorHub.
You receive a user's query along with real matching products retrieved directly from our live database.

Rules:
1. ONLY discuss and recommend the products provided in the [CATALOG SEARCH RESULTS]. Do NOT recommend unrelated items.
2. If the user is comparing two or more products (e.g. X vs Y), provide a clear, structured side-by-side comparison with sections:
   - **Pricing & Value**
   - **Key Features & Ratings**
   - **Recommendation Summary**
3. Always format prices in Indian Rupees (e.g., **₹40,538**), rating (e.g., ⭐ 4.7), and availability.
4. Conclude with a helpful tip or prompt to add to cart or compare on the canvas.
5. Embed product tags like [PRODUCT:slug] so interactive cards can be displayed.
6. Keep the response friendly, highly readable, and formatted with clean bullet points."""

    def _search_comparison(self, query: str) -> tuple[list[dict], list[dict]]:
        """Extract multi-product comparison entities (e.g. 'Compare A vs B')."""
        q = query.lower().strip()
        vs_match = re.search(r'compare\s+(.*?)\s+(?:vs|and|with|to)\s+(.*)', q, re.I)
        if not vs_match:
            vs_match = re.search(r'(.*?)\s+vs\s+(.*)', q, re.I)

        if not vs_match:
            return [], []

        term_a = vs_match.group(1).strip()
        term_b = vs_match.group(2).strip()

        def find_best_term_matches(term: str) -> list[Product]:
            words = [w for w in re.findall(r'\b[a-z0-9]+\b', term.lower()) if len(w) > 1 and w not in STOP_WORDS]
            if not words:
                return []

            qs = Product.objects.filter(is_active=True).select_related('category', 'brand', 'store')
            # First pass: try narrowing down by all words
            narrow_qs = qs
            for w in words:
                if narrow_qs.filter(name__icontains=w).exists():
                    narrow_qs = narrow_qs.filter(name__icontains=w)

            # Avoid covers or screen protectors if device exists
            devices_qs = narrow_qs.exclude(name__icontains="cover").exclude(name__icontains="case").exclude(name__icontains="glass")
            if devices_qs.exists():
                return list(devices_qs.order_by('-rating')[:2])
            return list(narrow_qs.order_by('-rating')[:2])

        matches_a = find_best_term_matches(term_a)
        matches_b = find_best_term_matches(term_b)
        combined = matches_a + matches_b

        # Remove duplicates
        seen = set()
        unique_prods = []
        for p in combined:
            if p.id not in seen:
                seen.add(p.id)
                unique_prods.append(p)

        if not unique_prods:
            return [], []

        prompt_data = [
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
            for p in unique_prods
        ]
        cards_data = ProductListSerializer(unique_prods, many=True).data
        return prompt_data, cards_data

    def _search_products(self, query: str, limit: int = 8) -> tuple[list[dict], list[dict]]:
        """
        Search products with smart category matching, price bounding, and rating sorting.
        Returns: (product_dicts_for_prompt, serialized_product_cards)
        """
        from django.db.models import Q

        # Check comparison first
        comp_prompt, comp_cards = self._search_comparison(query)
        if comp_prompt:
            return comp_prompt, comp_cards

        q = (query or "").lower().strip()

        # 1. Price extraction
        price_match = re.search(r'(?:under|below|less than|within)\s*(?:rs\.?|inr|₹)?\s*([0-9]+(?:,[0-9]+)*)', q)
        max_price = None
        if price_match:
            try:
                max_price = int(price_match.group(1).replace(',', ''))
            except ValueError:
                pass

        # 2. Extract clean search words
        raw_words = [w for w in re.findall(r'\b[a-z0-9]+\b', q) if len(w) > 1]
        content_words = [w for w in raw_words if w not in STOP_WORDS and not w.isdigit()]

        qs = Product.objects.filter(is_active=True).select_related('category', 'brand', 'store')

        if max_price:
            qs = qs.filter(price__lte=max_price)

        # 3. Sort strategy
        if any(k in q for k in ["top", "rated", "best", "popular", "highest"]):
            qs = qs.order_by('-rating', '-created_at')
        elif any(k in q for k in ["cheap", "budget", "lowest", "affordable"]):
            qs = qs.order_by('price')
        else:
            qs = qs.order_by('-rating', '-created_at')

        # 4. Check for direct category matches and synonyms
        CATEGORY_SYNONYMS = {
            "mobiles": ["phone", "phones", "smartphone", "smartphones", "mobile", "mobiles", "cellphone", "cellphones", "handset", "iphone", "android", "pixel", "galaxy"],
            "laptops": ["laptop", "laptops", "notebook", "notebooks", "macbook", "ultrabook", "chromebook", "computer", "pc"],
            "audio-sound": ["headphone", "headphones", "earphone", "earphones", "earbud", "earbuds", "headset", "audio", "sound", "speaker", "speakers", "soundbar", "tws"],
            "photography": ["camera", "cameras", "dslr", "mirrorless", "lens", "lenses", "tripod", "gimbal", "photography", "photo"],
            "gaming": ["gaming", "console", "playstation", "ps5", "xbox", "nintendo", "rog", "controller"],
            "appliances": ["fridge", "refrigerator", "washing", "machine", "microwave", "oven", "ac", "conditioner", "vacuum", "purifier", "appliance", "appliances"],
            "sneakers": ["shoes", "shoe", "sneaker", "sneakers", "boots", "footwear", "running", "trainers"],
            "mens-clothing": ["shirt", "tshirt", "t-shirt", "jeans", "trouser", "trousers", "jacket", "suit", "blazer", "hoodie"],
            "womens-clothing": ["dress", "saree", "kurti", "top", "skirt", "women"],
            "furniture": ["sofa", "chair", "table", "bed", "desk", "wardrobe", "furniture"],
            "books": ["book", "books", "novel", "novels", "paperback"],
            "groceries": ["grocery", "groceries", "food", "snack", "snacks", "tea", "coffee", "rice", "oil", "pulse"],
        }

        categories = list(Category.objects.all())
        matched_cat = None

        # Check synonym map first
        for slug_prefix, syns in CATEGORY_SYNONYMS.items():
            if any(w in syns for w in content_words):
                matched_cat = next((c for c in categories if slug_prefix in c.slug.lower() or slug_prefix in c.name.lower()), None)
                if matched_cat:
                    break

        # Fallback to direct word match in category names
        if not matched_cat:
            for word in content_words:
                variations = [word]
                if word.endswith('s') and len(word) > 3:
                    variations.append(word[:-1])
                if word.endswith('ies') and len(word) > 4:
                    variations.append(word[:-3] + 'y')

                for cat in categories:
                    cat_name_lower = cat.name.lower()
                    if any(v in cat_name_lower for v in variations):
                        matched_cat = cat
                        break
                if matched_cat:
                    break

        # Check if user specifically requested accessories
        is_accessory_query = any(k in q for k in ["holder", "mount", "case", "cover", "protector", "stand", "strap", "cable", "adapter", "charger", "skin"])
        if not is_accessory_query:
            # When searching for devices (smartphones, laptops, tablets), exclude mounts/holders/cases
            qs = qs.exclude(name__icontains="holder").exclude(name__icontains="mount").exclude(name__icontains="case").exclude(name__icontains="cover")

        if matched_cat:
            qs = qs.filter(category=matched_cat)
            # Remove category synonyms from remaining keywords so they don't filter out devices
            synonyms_for_cat = CATEGORY_SYNONYMS.get(matched_cat.slug.lower(), [])
            remaining_words = [w for w in content_words if w not in matched_cat.name.lower() and w not in synonyms_for_cat]
        else:
            remaining_words = content_words

        # 5. Filter by remaining content keywords (e.g. brand, specs)
        for w in remaining_words:
            variations = [w]
            if w.endswith('s') and len(w) > 3:
                variations.append(w[:-1])
            word_q = Q()
            for v in variations:
                word_q |= Q(name__icontains=v) | Q(brand__name__icontains=v) | Q(description__icontains=v)
            if qs.filter(word_q).exists():
                qs = qs.filter(word_q)

        products = list(qs[:limit])

        # If no strict matches, fallback within the category or relevant context (NEVER random dining tables for phones)
        if not products and matched_cat:
            products = list(Product.objects.filter(is_active=True, category=matched_cat).order_by('-rating')[:limit])
        elif not products and content_words:
            loose_q = Q()
            for w in content_words:
                loose_q |= Q(name__icontains=w) | Q(category__name__icontains=w)
            products = list(Product.objects.filter(is_active=True).filter(loose_q).order_by('-rating')[:limit])

        if not products:
            products = list(Product.objects.filter(is_active=True).order_by('-rating')[:limit])

        prompt_data = [
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

        serializer = ProductListSerializer(products, many=True)
        cards_data = serializer.data

        return prompt_data, cards_data

    def execute(self, messages: list[dict], context: dict) -> dict:
        """Search for products and generate a response."""
        query = context.get("refined_query", "")
        if not query and messages:
            query = messages[-1].get("content", "")

        results, product_cards = self._search_products(query)

        product_context = "\n".join([
            f"- **{p['name']}** (slug: {p['slug']}, price: ₹{float(p['price']):,.2f}, rating: ⭐ {p['rating']}, "
            f"stock: {'In Stock' if p['stock'] > 0 else 'Out of Stock'}, category: {p['category']})"
            for p in results
        ])

        is_comparison = any(w in query.lower() for w in ["vs", "compare", "difference"])

        if is_comparison and len(results) >= 2:
            task_instruction = (
                f"The user wants a side-by-side comparison for: '{query}'.\n"
                f"Present a structured comparison between {results[0]['name']} and {results[1]['name']}.\n"
                f"Include sections: 1. Overview & Pricing, 2. Key Specs & Ratings, 3. Verdict/Recommendation.\n"
                f"Always include [PRODUCT:{results[0]['slug']}] and [PRODUCT:{results[1]['slug']}] tags."
            )
        else:
            task_instruction = f"Present these exact {len(results)} products clearly to the user. Always embed [PRODUCT:slug] tags."

        search_messages = messages.copy()
        if search_messages:
            search_messages[-1] = {
                "role": "user",
                "content": (
                    f"{search_messages[-1].get('content', '')}\n\n"
                    f"[CATALOG SEARCH RESULTS FOR: '{query}']\n"
                    f"{product_context}\n\n"
                    f"{task_instruction}"
                )
            }

        # Generate follow-up suggestions
        followups = []
        if is_comparison and len(results) >= 2:
            followups.append(f"Add {results[0]['name']} to cart")
            followups.append(f"Add {results[1]['name']} to cart")
            followups.append(f"Compare specs on canvas")
        elif results:
            followups.append(f"Add {results[0]['name'][:25]} to cart")
            followups.append(f"Sort by lowest price")
            followups.append("Show top rated deals")

        try:
            content = self.call_gemini(search_messages, context)
            return {
                "content": content,
                "productCards": product_cards,
                "suggestedFollowups": followups,
            }
        except Exception as e:
            logger.info(f"Search agent fallback rule generation: {e}")
            if is_comparison and len(results) >= 2:
                lines = [
                    f"### ⚖️ Side-by-Side Comparison: **{results[0]['name']}** vs **{results[1]['name']}**\n",
                    f"**1. {results[0]['name']}**",
                    f"• **Price:** ₹{float(results[0]['price']):,.2f} | **Rating:** ⭐ {results[0]['rating']}",
                    f"• **Category:** {results[0]['category']} | **Availability:** {'In Stock' if results[0]['stock'] > 0 else 'Out of Stock'}",
                    f"  [PRODUCT:{results[0]['slug']}]\n",
                    f"**2. {results[1]['name']}**",
                    f"• **Price:** ₹{float(results[1]['price']):,.2f} | **Rating:** ⭐ {results[1]['rating']}",
                    f"• **Category:** {results[1]['category']} | **Availability:** {'In Stock' if results[1]['stock'] > 0 else 'Out of Stock'}",
                    f"  [PRODUCT:{results[1]['slug']}]\n",
                    "**Verdict:** Both devices offer flagship experiences. Tap either product card below to add directly to your cart, or view the full side-by-side specs matrix on the left canvas! 📱"
                ]
            else:
                lines = [f"Here are the top-rated products found for **\"{query}\"**:\n"]
                for p in results[:5]:
                    stock_str = f"({p['stock']} in stock)" if p['stock'] > 0 else "(Out of stock)"
                    lines.append(f"• **{p['name']}** — **₹{float(p['price']):,.2f}** (⭐ {p['rating']}) {stock_str}\n  [PRODUCT:{p['slug']}]")
                lines.append("\nTap any product card below to view details, compare specs, or add it to your cart! 🛍️")

            return {
                "content": "\n".join(lines),
                "productCards": product_cards,
                "suggestedFollowups": followups,
            }
