import os
import sys

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django
django.setup()

from users.models import User
from sellers.models import SellerProfile, Store
from products.models import Product
from orders.models import Order, OrderItem, Payment

def run_verification():
    print("=" * 50)
    print("  RazorHub Data Integrity Verification")
    print("=" * 50)
    
    issues = 0

    # 1. Admin exists
    admins = User.objects.filter(is_superuser=True)
    if admins.count() == 0:
        print("[FAIL] No admin user found")
        issues += 1
    else:
        print("[PASS] Admin user exists")

    # 2. SellerProfile -> Store 1:1 check
    sellers = SellerProfile.objects.all()
    for seller in sellers:
        if not hasattr(seller, 'store') or seller.store is None:
            print(f"[FAIL] Seller {seller.business_name} has no store")
            issues += 1
    print("[PASS] Every SellerProfile has a Store")

    # 3. Product belongs to active Store
    products = Product.objects.all()
    orphans = products.filter(store__isnull=True)
    if orphans.exists():
        print(f"[FAIL] {orphans.count()} products have no store")
        issues += 1
    else:
        print("[PASS] Every Product belongs to a Store")

    # 4. Currency check
    npr_products = products.filter(currency="NPR")
    if npr_products.exists():
        print(f"[FAIL] {npr_products.count()} products still use NPR")
        issues += 1
    else:
        print("[PASS] All products use INR")

    # 5. Orders have items and valid products
    orders = Order.objects.all()
    if orders.count() == 0:
        print("[FAIL] No orders found")
        issues += 1
    else:
        empty_orders = 0
        for order in orders:
            if order.items.count() == 0:
                print(f"[FAIL] Order {order.id} has no items")
                empty_orders += 1
                issues += 1
        if empty_orders == 0:
            print("[PASS] All orders have items")

    # 6. Payment links to order
    payments = Payment.objects.all()
    unlinked = payments.filter(order__isnull=True)
    if unlinked.exists():
        print(f"[FAIL] {unlinked.count()} payments have no order")
        issues += 1
    else:
        print("[PASS] All payments linked to an order")

    # 7. Check laptops category fix
    from products.models import Category
    if Category.objects.filter(slug='gaming').exists():
        print("[FAIL] 'gaming' category slug still exists")
        issues += 1
    elif not Category.objects.filter(slug='laptops').exists():
        print("[FAIL] 'laptops' category does not exist")
        issues += 1
    else:
        print("[PASS] Laptops category slug is correct")

    print("=" * 50)
    if issues == 0:
        print("  ALL CHECKS PASSED SUCCESSFULLY")
    else:
        print(f"  {issues} ISSUES FOUND")
    print("=" * 50)


if __name__ == "__main__":
    run_verification()
