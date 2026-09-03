import os
import sys
import django
from decimal import Decimal, ROUND_HALF_UP

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.db import transaction
from products.models import Product

CATEGORY_MARGIN_TARGETS = {
    'electronics': Decimal('0.22'),
    'laptops': Decimal('0.18'),
    'mobiles': Decimal('0.16'),
    'appliances': Decimal('0.25'),
    'gaming': Decimal('0.24'),
    'fashion': Decimal('0.55'),
    'mens-clothing': Decimal('0.52'),
    'womens-clothing': Decimal('0.58'),
    'sneakers': Decimal('0.48'),
    'jewelery': Decimal('0.50'),
    'jewellery-accessories': Decimal('0.50'),
    'groceries': Decimal('0.18'),
    'books': Decimal('0.35'),
    'stationery': Decimal('0.38'),
    'photography': Decimal('0.28'),
    'furniture': Decimal('0.42'),
    'home-kitchen': Decimal('0.40'),
    'pets': Decimal('0.45'),
    'sports-fitness': Decimal('0.36'),
    'automotive': Decimal('0.32'),
    'eco-sustainable': Decimal('0.46'),
}
DEFAULT_MARGIN = Decimal('0.35')

def enrich_costs():
    print("Enriching product costs and margins...", flush=True)
    products = list(Product.objects.select_related('category').all())
    updated = 0

    with transaction.atomic():
        for p in products:
            selling_price = p.discount_price if p.discount_price else p.price
            if selling_price <= 0:
                continue

            # Check if cost_price already valid and positive
            if p.cost_price and p.cost_price > 0 and p.cost_price < selling_price:
                # Re-compute margin
                p._compute_paise_and_margin()
                p.save(update_fields=['price_paise', 'cost_paise', 'margin_pct'])
                continue

            slug = p.category.slug if p.category else ''
            target_margin = CATEGORY_MARGIN_TARGETS.get(slug, DEFAULT_MARGIN)
            # Add small deterministic variation based on product ID (+/- 4%)
            variation = Decimal(str(((p.id % 9) - 4) * 0.01))
            margin = max(Decimal('0.12'), min(Decimal('0.70'), target_margin + variation))

            # Cost = Selling Price * (1 - margin)
            cost = (selling_price * (Decimal('1') - margin)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            p.cost_price = cost
            p._compute_paise_and_margin()
            p.save(update_fields=['cost_price', 'price_paise', 'cost_paise', 'margin_pct'])
            updated += 1

    print(f"Successfully enriched {updated} products with cost prices and margins.", flush=True)
    
    # Audit summary
    sample = Product.objects.filter(is_active=True).order_by('?')[:5]
    print("\nSample Products Audit:")
    for s in sample:
        print(f" - {s.name[:35]:<35} | Price: ₹{s.current_price:<8} | Cost: ₹{s.cost_price:<8} | Margin: {s.margin_pct}%")

if __name__ == "__main__":
    enrich_costs()
