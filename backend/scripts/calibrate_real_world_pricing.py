import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product
from decimal import Decimal

# Realistic real-world Indian market pricing rules
RULES = [
    # (condition_lambda, min_p, max_p, target_p)
    (lambda name, cat: 'band' in name or 'tracker' in name, 1499, 3999),
    (lambda name, cat: 'tripod' in name, 699, 2499),
    (lambda name, cat: 'cable' in name or 'adapter' in name or 'charger' in name, 299, 1499),
    (lambda name, cat: 'mouse' in name or 'keyboard' in name, 499, 3999),
    (lambda name, cat: 't-shirt' in name or 'tee' in name, 399, 1499),
    (lambda name, cat: 'sock' in name or 'underwear' in name, 199, 699),
    (lambda name, cat: 'book' in cat and not ('laptop' in name), 150, 999),
    (lambda name, cat: 'stationery' in cat, 49, 499),
    (lambda name, cat: 'grocer' in cat or 'food' in cat, 40, 799),
    (lambda name, cat: 'earbud' in name or 'tws' in name or 'airpod' in name, 999, 6999),
    (lambda name, cat: 'water bottle' in name, 199, 899),
    (lambda name, cat: 'yoga mat' in name, 499, 1499),
]

def calibrate_prices():
    updated = 0
    for p in Product.objects.all():
        name_lower = p.name.lower()
        cat_lower = p.category.name.lower() if p.category else ''
        curr_price = float(p.discount_price or p.price)
        
        matched_rule = None
        for rule_fn, min_p, max_p in RULES:
            if rule_fn(name_lower, cat_lower):
                if curr_price > max_p or curr_price < min_p:
                    matched_rule = (min_p, max_p)
                    break
        
        if matched_rule:
            min_p, max_p = matched_rule
            # Normalize to realistic middle-range price ending in 9 or 99
            import random
            target = random.randint(min_p // 100, max_p // 100) * 100 - 1
            if target < min_p:
                target = min_p
            
            p.price = Decimal(str(int(target * 1.25))) # MRP
            p.discount_price = Decimal(str(int(target))) # Deal price
            p.save(update_fields=['price', 'discount_price'])
            updated += 1
            print(f'Calibrated ID {p.id}: {p.name[:32]} -> Rs.{target} (was Rs.{int(curr_price)})')
            
    print(f'Done! Calibrated {updated} products to realistic real-world pricing.')

if __name__ == '__main__':
    calibrate_prices()
