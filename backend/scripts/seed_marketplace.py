"""
Comprehensive Marketplace Seed Script
======================================
Creates:
- 1 Admin superuser
- 4 new sellers (+ keeps existing Pillai Enterprises)
- 4 new stores
- 20 customers with addresses
- Redistributes 322 products across 5 sellers
- 50+ orders with items and payments
- Fixes currency NPR → INR on all products
- Fixes category slugs and adds missing categories
"""
import os
import sys
import random
from decimal import Decimal

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from users.models import User, CustomerProfile, Address
from sellers.models import SellerProfile, Store
from products.models import Product, Category
from orders.models import Order, OrderItem, Payment
from crm.models import CustomerRecord, ActivityLog

# Try importing SellerRecord
try:
    from crm.models import SellerRecord
    HAS_SELLER_RECORD = True
except ImportError:
    HAS_SELLER_RECORD = False


def log(msg):
    print(f"  ✓ {msg}")


def create_admin():
    """Phase 1: Create admin superuser."""
    print("\n=== Phase 1: Creating Admin User ===")
    admin_email = "admin@razorhub.in"
    admin, created = User.objects.get_or_create(
        email=admin_email,
        defaults={
            "username": admin_email,
            "first_name": "RazorHub",
            "last_name": "Admin",
            "role": "admin",
            "is_staff": True,
            "is_superuser": True,
            "phone": "+91 9000000001",
        }
    )
    if created:
        admin.set_password("RazorHub@Admin2024")
        admin.save()
        log(f"Created admin: {admin_email}")
    else:
        admin.is_staff = True
        admin.is_superuser = True
        admin.role = "admin"
        admin.set_password("RazorHub@Admin2024")
        admin.save()
        log(f"Updated existing admin: {admin_email}")
    return admin


SELLER_DATA = [
    {
        "email": "seller@techvista.in",
        "first_name": "Arjun",
        "last_name": "Sharma",
        "business_name": "TechVista Electronics",
        "store_name": "TechVista Electronics",
        "store_slug": "techvista-electronics",
        "description": "India's trusted destination for laptops, mobiles, and electronics. Premium gadgets at competitive prices.",
        "category_slugs": ["electronics", "laptops", "mobiles"],
        "phone": "+91 9876543001",
        "tax_id": "GSTIN29ABCDE1234F1Z5",
    },
    {
        "email": "seller@stylecraft.in",
        "first_name": "Priya",
        "last_name": "Kapoor",
        "business_name": "StyleCraft Fashion",
        "store_name": "StyleCraft Fashion",
        "store_slug": "stylecraft-fashion",
        "description": "Curated fashion for men and women. Trendy apparel, ethnic wear, and accessories.",
        "category_slugs": ["fashion", "mens-clothing", "womens-clothing"],
        "phone": "+91 9876543002",
        "tax_id": "GSTIN29FGHIJ5678K2Z6",
    },
    {
        "email": "seller@homeessentials.in",
        "first_name": "Vikram",
        "last_name": "Patel",
        "business_name": "HomeEssentials India",
        "store_name": "HomeEssentials India",
        "store_slug": "homeessentials-india",
        "description": "Everything for your home - appliances, groceries, kitchen essentials. Fast delivery across India.",
        "category_slugs": ["appliances", "groceries"],
        "phone": "+91 9876543003",
        "tax_id": "GSTIN29LMNOP9012Q3Z7",
    },
    {
        "email": "seller@glamourbox.in",
        "first_name": "Neha",
        "last_name": "Reddy",
        "business_name": "GlamourBox",
        "store_name": "GlamourBox",
        "store_slug": "glamourbox",
        "description": "Premium jewellery and flash deal store. Daily deals on trending accessories and lifestyle products.",
        "category_slugs": ["jewelery", "flash-deals"],
        "phone": "+91 9876543004",
        "tax_id": "GSTIN29RSTUV3456W4Z8",
    },
]

CUSTOMER_DATA = [
    {"first_name": "Aarav", "last_name": "Singh", "city": "Mumbai", "state": "Maharashtra", "postal_code": "400001"},
    {"first_name": "Diya", "last_name": "Mehta", "city": "Delhi", "state": "Delhi", "postal_code": "110001"},
    {"first_name": "Vihaan", "last_name": "Kumar", "city": "Bengaluru", "state": "Karnataka", "postal_code": "560001"},
    {"first_name": "Ananya", "last_name": "Gupta", "city": "Chennai", "state": "Tamil Nadu", "postal_code": "600001"},
    {"first_name": "Reyansh", "last_name": "Iyer", "city": "Hyderabad", "state": "Telangana", "postal_code": "500001"},
    {"first_name": "Isha", "last_name": "Patel", "city": "Ahmedabad", "state": "Gujarat", "postal_code": "380001"},
    {"first_name": "Kabir", "last_name": "Das", "city": "Kolkata", "state": "West Bengal", "postal_code": "700001"},
    {"first_name": "Myra", "last_name": "Joshi", "city": "Pune", "state": "Maharashtra", "postal_code": "411001"},
    {"first_name": "Aryan", "last_name": "Nair", "city": "Kochi", "state": "Kerala", "postal_code": "682001"},
    {"first_name": "Saanvi", "last_name": "Rao", "city": "Jaipur", "state": "Rajasthan", "postal_code": "302001"},
    {"first_name": "Advait", "last_name": "Mishra", "city": "Lucknow", "state": "Uttar Pradesh", "postal_code": "226001"},
    {"first_name": "Kiara", "last_name": "Verma", "city": "Chandigarh", "state": "Chandigarh", "postal_code": "160001"},
    {"first_name": "Vivaan", "last_name": "Chopra", "city": "Indore", "state": "Madhya Pradesh", "postal_code": "452001"},
    {"first_name": "Anika", "last_name": "Bose", "city": "Bhopal", "state": "Madhya Pradesh", "postal_code": "462001"},
    {"first_name": "Dhruv", "last_name": "Thakur", "city": "Nagpur", "state": "Maharashtra", "postal_code": "440001"},
    {"first_name": "Riya", "last_name": "Agarwal", "city": "Varanasi", "state": "Uttar Pradesh", "postal_code": "221001"},
    {"first_name": "Rohan", "last_name": "Shetty", "city": "Mangalore", "state": "Karnataka", "postal_code": "575001"},
    {"first_name": "Tara", "last_name": "Pillai", "city": "Thiruvananthapuram", "state": "Kerala", "postal_code": "695001"},
    {"first_name": "Ishaan", "last_name": "Saxena", "city": "Dehradun", "state": "Uttarakhand", "postal_code": "248001"},
    {"first_name": "Zara", "last_name": "Khan", "city": "Surat", "state": "Gujarat", "postal_code": "395001"},
]

INDIAN_ADDRESSES = [
    "Flat 301, Sunrise Apartments, MG Road",
    "B-12, Sector 62, Industrial Area",
    "House No. 45, Gandhi Nagar, Lane 3",
    "Plot 78, Phase 2, Electronic City",
    "2nd Floor, Laxmi Tower, Park Street",
    "Villa 23, Palm Meadows, Whitefield",
    "Apt 504, Ocean View, Marine Drive",
    "Block C, DLF Phase 3, Cyber City",
    "No. 67, Anna Nagar East, 2nd Avenue",
    "Flat 102, Royal Enclave, Banjara Hills",
    "G-5, Panchsheel Park, South Extension",
    "Tower B, Prestige Shantiniketan, ITPL Road",
    "302, Sapphire Heights, FC Road",
    "A-Wing, Lodha Palava, Dombivli East",
    "Plot 34, Jubilee Hills, Road No. 36",
    "Flat 201, Brigade Gateway, Rajajinagar",
    "C-401, Hiranandani Gardens, Powai",
    "No. 12, Indiranagar, 100 Feet Road",
    "Flat 6B, Raheja Residency, Koramangala",
    "House 89, Civil Lines, Near Clock Tower",
]


def create_sellers():
    """Phase 2: Create 4 new sellers with stores."""
    print("\n=== Phase 2a: Creating Sellers & Stores ===")
    stores = {}

    for sd in SELLER_DATA:
        user, created = User.objects.get_or_create(
            email=sd["email"],
            defaults={
                "username": sd["email"],
                "first_name": sd["first_name"],
                "last_name": sd["last_name"],
                "role": "seller",
                "phone": sd["phone"],
            }
        )
        if created:
            user.set_password("Seller@2024")
            user.save()

        seller, _ = SellerProfile.objects.get_or_create(
            user=user,
            defaults={
                "business_name": sd["business_name"],
                "phone": sd["phone"],
                "tax_id": sd["tax_id"],
                "status": "verified",
            }
        )
        # Force verified
        if seller.status != "verified":
            seller.status = "verified"
            seller.save(update_fields=["status"])

        store, _ = Store.objects.get_or_create(
            seller=seller,
            defaults={
                "name": sd["store_name"],
                "slug": sd["store_slug"],
                "description": sd["description"],
                "support_email": sd["email"],
                "support_phone": sd["phone"],
                "is_active": True,
            }
        )
        stores[tuple(sd["category_slugs"])] = store
        log(f"Seller: {sd['business_name']} -> Store: {store.name} (id={store.id})")

        # CRM records
        CustomerRecord.objects.get_or_create(user=user)
        if HAS_SELLER_RECORD:
            SellerRecord.objects.get_or_create(seller=seller)

    return stores


def create_customers():
    """Phase 2: Create 20 customers with addresses."""
    print("\n=== Phase 2b: Creating Customers & Addresses ===")
    customers = []

    for i, cd in enumerate(CUSTOMER_DATA):
        email = f"{cd['first_name'].lower()}.{cd['last_name'].lower()}@customer.in"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": cd["first_name"],
                "last_name": cd["last_name"],
                "role": "customer",
                "phone": f"+91 98{random.randint(10000000, 99999999)}",
            }
        )
        if created:
            user.set_password("Customer@2024")
            user.save()

        CustomerProfile.objects.get_or_create(
            user=user,
            defaults={"full_name": f"{cd['first_name']} {cd['last_name']}"}
        )
        CustomerRecord.objects.get_or_create(user=user)

        # Create 1-2 addresses
        addr_line = INDIAN_ADDRESSES[i % len(INDIAN_ADDRESSES)]
        Address.objects.get_or_create(
            user=user,
            label="Home",
            defaults={
                "address_type": "shipping",
                "full_name": f"{cd['first_name']} {cd['last_name']}",
                "phone": user.phone or f"+91 98{random.randint(10000000, 99999999)}",
                "line1": addr_line,
                "city": cd["city"],
                "state": cd["state"],
                "postal_code": cd["postal_code"],
                "country": "India",
                "is_default": True,
            }
        )

        if i % 3 == 0:  # Every 3rd customer gets a work address too
            Address.objects.get_or_create(
                user=user,
                label="Work",
                defaults={
                    "address_type": "shipping",
                    "full_name": f"{cd['first_name']} {cd['last_name']}",
                    "phone": user.phone or f"+91 98{random.randint(10000000, 99999999)}",
                    "line1": INDIAN_ADDRESSES[(i + 5) % len(INDIAN_ADDRESSES)],
                    "city": cd["city"],
                    "state": cd["state"],
                    "postal_code": cd["postal_code"],
                    "country": "India",
                    "is_default": False,
                }
            )

        customers.append(user)

    log(f"Created/verified {len(customers)} customers with addresses")
    return customers


def fix_categories():
    """Phase 6: Fix category slugs and add missing categories."""
    print("\n=== Phase 6: Fixing Categories ===")

    # Fix "Laptops & Computing" slug from 'gaming' to 'laptops'
    try:
        laptops_cat = Category.objects.get(slug="gaming")
        laptops_cat.slug = "laptops"
        laptops_cat.name = "Laptops & Computing"
        laptops_cat.save()
        log("Fixed 'gaming' -> 'laptops' category slug")
    except Category.DoesNotExist:
        log("No 'gaming' slug found to fix")

    # Add Books category if missing
    books, created = Category.objects.get_or_create(
        slug="books",
        defaults={
            "name": "Books & Stationery",
            "description": "Fiction, non-fiction, textbooks, journals, and office supplies.",
            "order": 11,
        }
    )
    if created:
        log("Created 'Books & Stationery' category")
    else:
        log("Books category already exists")

    # Fix category names for consistency
    fixes = {
        "jewelery": ("Jewellery & Accessories", "Fine jewellery, fashion accessories, watches, and lifestyle products."),
        "flash-deals": ("Flash Deals", "Limited time offers and daily deals on trending products."),
    }
    for slug, (name, desc) in fixes.items():
        try:
            cat = Category.objects.get(slug=slug)
            if cat.name != name:
                cat.name = name
                cat.description = desc
                cat.save()
                log(f"Fixed category '{slug}' -> '{name}'")
        except Category.DoesNotExist:
            pass

    return Category.objects.all()


def redistribute_products(stores_by_cats):
    """Redistribute existing products across sellers based on category."""
    print("\n=== Phase 2c: Redistributing Products ===")

    # Build category -> store mapping
    cat_to_store = {}
    for cat_slugs, store in stores_by_cats.items():
        for slug in cat_slugs:
            cat_to_store[slug] = store

    # Keep Pillai's existing products untouched
    pillai_store = Store.objects.filter(slug="pillai-enterprises").first()

    redistributed = 0
    for product in Product.objects.select_related("category", "store").all():
        # Skip Pillai's products
        if pillai_store and product.store_id == pillai_store.id:
            continue

        cat_slug = product.category.slug if product.category else None
        target_store = cat_to_store.get(cat_slug)

        if target_store and product.store_id != target_store.id:
            product.store = target_store
            product.currency = "INR"
            product.save(update_fields=["store", "currency"])
            redistributed += 1

    # Fix any remaining NPR products
    remaining = Product.objects.filter(currency="NPR").update(currency="INR")
    log(f"Redistributed {redistributed} products across sellers")
    log(f"Fixed {remaining} remaining NPR -> INR currency entries")


ORDER_STATUSES = ["pending", "processing", "shipped", "delivered", "delivered", "delivered", "cancelled"]


def create_orders(customers):
    """Phase 2: Create 50+ realistic orders."""
    print("\n=== Phase 2d: Creating Orders ===")

    all_products = list(Product.objects.filter(is_active=True).select_related("store", "category")[:300])
    if not all_products:
        log("WARNING: No products found. Skipping order creation.")
        return

    now = timezone.now()
    orders_created = 0
    items_created = 0

    for i in range(55):
        customer = random.choice(customers)
        status = random.choice(ORDER_STATUSES)

        # Pick 1-4 products from the same store for consistency
        product_pool = random.choice(all_products)
        store = product_pool.store
        store_products = [p for p in all_products if p.store_id == (store.id if store else None)]
        if not store_products:
            store_products = [product_pool]

        num_items = random.randint(1, min(4, len(store_products)))
        chosen_products = random.sample(store_products, num_items)

        # Calculate totals
        order_total = Decimal("0")
        item_data = []
        for prod in chosen_products:
            qty = random.randint(1, 3)
            price = prod.discount_price or prod.price
            line_total = price * qty
            order_total += line_total
            item_data.append((prod, qty, price))

        delivery_fee = Decimal("50") if order_total > Decimal("500") else Decimal("99")
        order_total += delivery_fee

        # Random date in last 60 days
        days_ago = random.randint(0, 60)
        order_date = now - timedelta(days=days_ago, hours=random.randint(0, 23), minutes=random.randint(0, 59))

        # Get shipping address
        address = customer.addresses.first()
        shipping_addr = f"{address.line1}, {address.city}, {address.state} {address.postal_code}" if address else f"{customer.first_name}'s address, India"

        with transaction.atomic():
            order = Order.objects.create(
                user=customer,
                status=status,
                payment_method=random.choice(["razorpay", "razorpay", "razorpay", "cod"]),
                delivery_fee=delivery_fee,
                total_price=order_total,
                shipping_address=shipping_addr,
                delivery_eta=f"{random.randint(2, 7)} business days",
            )
            # Override created_at
            Order.objects.filter(pk=order.pk).update(created_at=order_date)

            for prod, qty, price in item_data:
                OrderItem.objects.create(
                    order=order,
                    product=prod,
                    quantity=qty,
                    price=price,
                )
                items_created += 1

            # Create payment record
            if order.payment_method == "razorpay":
                payment_status = "paid" if status in ("processing", "shipped", "delivered") else ("pending" if status == "pending" else "failed")
            else:
                payment_status = "paid" if status in ("delivered",) else "pending"

            Payment.objects.create(
                order=order,
                method=order.payment_method,
                status=payment_status,
                amount=order_total,
                provider_reference=f"pay_test_{random.randint(100000, 999999)}" if order.payment_method == "razorpay" else "",
            )

            orders_created += 1

    log(f"Created {orders_created} orders with {items_created} items")


def create_seeded_users_doc():
    """Create SEEDED_USERS.md documentation."""
    print("\n=== Creating SEEDED_USERS.md ===")
    doc = """# Seeded Test Users - RazorHub Marketplace

## Admin
| Email | Password | Role |
|-------|----------|------|
| admin@razorhub.in | RazorHub@Admin2024 | Admin (superuser) |

## Sellers
| Email | Password | Business Name | Store |
|-------|----------|--------------|-------|
| seller@techvista.in | Seller@2024 | TechVista Electronics | TechVista Electronics |
| seller@stylecraft.in | Seller@2024 | StyleCraft Fashion | StyleCraft Fashion |
| seller@homeessentials.in | Seller@2024 | HomeEssentials India | HomeEssentials India |
| seller@glamourbox.in | Seller@2024 | GlamourBox | GlamourBox |
| seller.saanvi0@store.in | (pre-existing) | Pillai Enterprises | Pillai Enterprises |

> **Seller Registration Code (dev):** `demo`

## Customers (sample)
| Email | Password |
|-------|----------|
| aarav.singh@customer.in | Customer@2024 |
| diya.mehta@customer.in | Customer@2024 |
| vihaan.kumar@customer.in | Customer@2024 |
| ananya.gupta@customer.in | Customer@2024 |
| reyansh.iyer@customer.in | Customer@2024 |
| ... (20 total customers) | Customer@2024 |

## Notes
- All seller accounts have `status: verified`
- All customer accounts have at least 1 shipping address
- Products are distributed across sellers by category
- 55 orders exist across all customers and stores
"""
    doc_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SEEDED_USERS.md")
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write(doc)
    log(f"Created SEEDED_USERS.md")


def run():
    print("=" * 50)
    print("  RazorHub Marketplace Seed Script")
    print("=" * 50)

    # Phase 1: Admin
    create_admin()

    # Phase 6 (early): Fix categories first so product redistribution works
    fix_categories()

    # Phase 2a: Sellers & Stores
    stores = create_sellers()

    # Phase 2b: Customers
    customers = create_customers()

    # Phase 2c: Redistribute products
    redistribute_products(stores)

    # Phase 2d: Orders
    create_orders(customers)

    # Documentation
    create_seeded_users_doc()

    # Final summary
    print("\n" + "=" * 50)
    print("  Seed Complete - Summary")
    print("=" * 50)
    print(f"  Users:    {User.objects.count()}")
    print(f"  Admins:   {User.objects.filter(is_superuser=True).count()}")
    print(f"  Sellers:  {SellerProfile.objects.count()}")
    print(f"  Stores:   {Store.objects.count()}")
    print(f"  Products: {Product.objects.count()}")
    print(f"  Orders:   {Order.objects.count()}")
    print(f"  Payments: {Payment.objects.count()}")
    print("=" * 50)


if __name__ == "__main__":
    run()
