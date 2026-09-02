"""Seed FakeStore products - run with: python manage.py shell < scripts/seed_fakestore.py"""
import os
import django
import urllib.request
import json
from decimal import Decimal

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.utils.text import slugify
from products.models import Category, Brand, Product, ProductImage, Review, Inventory
from sellers.models import SellerProfile, Store

User = get_user_model()

def unique_store_slug(name: str) -> str:
    base = slugify(name)
    slug = base
    suffix = 2
    while Store.objects.filter(slug=slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug

def main():
    print("Fetching products from FakeStore API...")
    url = "https://fakestoreapi.com/products"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    seller_user, _ = User.objects.update_or_create(
        email="admin@razorhub.local",
        defaults={
            "username": "admin@razorhub.local",
            "first_name": "RazorHub",
            "last_name": "Admin",
            "role": "seller",
            "is_active": True,
        },
    )
    seller_user.set_password("admin123")
    seller_user.save()

    seller_profile, _ = SellerProfile.objects.update_or_create(
        user=seller_user,
        defaults={"business_name": "RazorHub Official Store", "phone": "+91-9876543210", "status": "verified"},
    )

    store, _ = Store.objects.update_or_create(
        seller=seller_profile,
        defaults={
            "name": "RazorHub Retail",
            "slug": "razorhub-retail",
            "description": "The official retail store of RazorHub, offering premium products across diverse categories.",
            "address": "123 Commerce St, Tech Park",
            "support_email": "support@razorhub.local",
            "support_phone": "+91-9876543210",
            "is_active": True,
        },
    )
    print(f"Store ready: {store.name}")
    
    brand, _ = Brand.objects.get_or_create(name="Generic")

    for item in data:
        cat_name = item['category'].title()
        category, _ = Category.objects.get_or_create(
            name=cat_name,
            defaults={"description": f"All items related to {cat_name}"}
        )
        
        price = Decimal(str(item['price']))
        # convert USD to INR roughly for realistic prices (e.g., * 80)
        inr_price = price * Decimal("80.00")
        
        product, created = Product.objects.update_or_create(
            name=item['title'][:300],
            defaults={
                "category": category,
                "store": store,
                "brand": brand,
                "price": inr_price,
                "description": item['description'],
                "stock": 100,
                "rating": Decimal(str(item['rating']['rate'])),
                "is_active": True,
                "is_featured": item['rating']['rate'] > 4.0,
            }
        )
        
        ProductImage.objects.update_or_create(
            product=product,
            is_primary=True,
            defaults={"image_url": item['image'], "alt_text": item['title'][:200], "order": 0},
        )
        
        Inventory.objects.update_or_create(
            product=product,
            defaults={"sku": f"FS-{item['id']}", "quantity": 100, "low_stock_threshold": 10},
        )
        
        status = "Created" if created else "Updated"
        print(f"  {status}: {product.name[:30]}... - INR {product.price}")
        
    print("Database seeding from FakeStore API complete!")

if __name__ == "__main__":
    main()
