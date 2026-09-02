import sys
import os
import django
import random
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.utils.text import slugify
from products.models import Category, Brand, Product, ProductImage, Inventory
from sellers.models import Store

def main():
    print("Starting script...")
    sys.stdout.flush()
    try:
        try:
            store = Store.objects.get(slug="razorhub-retail")
        except Store.DoesNotExist:
            store = Store.objects.first()

        if not store:
            print("No store found!")
            return

        brand, _ = Brand.objects.get_or_create(name="Generic Brand")

        categories = list(Category.objects.all())
        
        print(f"Generating 30 products for {len(categories)} categories...")
        sys.stdout.flush()
        
        for category in categories:
            print(f"Processing category: {category.name}")
            sys.stdout.flush()
            for i in range(1, 31):
                product_name = f"{category.name} Item {i} - Premium Edition"
                price = Decimal(str(random.randint(500, 15000) + 0.99))
                
                product, created = Product.objects.update_or_create(
                    name=product_name[:300],
                    defaults={
                        "category": category,
                        "store": store,
                        "brand": brand,
                        "price": price,
                        "description": f"High quality {category.name} product inspired by top e-commerce platforms like Amazon and Flipkart. This is product number {i}.",
                        "stock": random.randint(10, 200),
                        "rating": Decimal(str(round(random.uniform(3.0, 5.0), 1))),
                        "is_active": True,
                        "is_featured": random.choice([True, False, False]),
                    }
                )
                
                ProductImage.objects.update_or_create(
                    product=product,
                    is_primary=True,
                    defaults={"image_url": f"https://picsum.photos/seed/{slugify(product_name)}/600/600", "alt_text": product_name[:200], "order": 0},
                )
                
                Inventory.objects.update_or_create(
                    product=product,
                    defaults={"sku": f"GEN-{category.id}-{i}", "quantity": product.stock, "low_stock_threshold": 5},
                )

        print("Finished generating dummy products!")
    except Exception as e:
        print(f"Error: {e}")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
