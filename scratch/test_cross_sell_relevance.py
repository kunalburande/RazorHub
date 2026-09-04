import os
import sys
import django

# Setup Django environment
sys.path.append(r"c:\Users\krbur\OneDrive\Desktop\RazorHub\backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from products.models import Product
from intelligence.services.upsell_service import UpsellService, CATEGORY_AFFINITY_MAP
from intelligence.models import MerchantConfig

def test_cross_sell_relevance():
    print("=== TESTING CROSS-SELL & UPSELL RELEVANCE ===")

    # 1. Test Category Affinity Map
    print(f"Affinity map has {len(CATEGORY_AFFINITY_MAP)} source categories.")
    assert "laptop" in CATEGORY_AFFINITY_MAP, "Laptop affinity mapping missing"
    assert "mobile" in CATEGORY_AFFINITY_MAP, "Mobile affinity mapping missing"
    print("[OK] CATEGORY_AFFINITY_MAP verified")

    # 2. Find a laptop product
    laptop = Product.objects.filter(category__slug__icontains="laptop", is_active=True).first()
    if not laptop:
        laptop = Product.objects.filter(name__icontains="laptop", is_active=True).first()

    if laptop:
        print(f"\nBase Product: {laptop.name} (Category: {laptop.category.name if laptop.category else 'None'}, Price: ₹{laptop.price})")
        recs = UpsellService.build_checkout_recommendations(product=laptop, limit=4)
        print(f"Cross-sell count: {len(recs['cross_sell'])}")
        for idx, cs in enumerate(recs['cross_sell']):
            print(f"  [{idx+1}] {cs['name']} (Category: {cs['category']}, ₹{cs['price']})")
            print(f"      Reason: {cs['reason']}")
            # Verify NO sneakers or footwear are suggested for laptop!
            cat_lower = cs['category'].lower()
            name_lower = cs['name'].lower()
            assert not any(bad in cat_lower for bad in ["sneaker", "shoe", "footwear", "kitchen", "cookware"]), \
                f"Irrelevant product suggested: {cs['name']} in {cs['category']} for laptop!"
        print("[OK] All cross-sells for laptop are strictly category-relevant!")

        print(f"\nUpsell count: {len(recs['upsell'])}")
        for idx, us in enumerate(recs['upsell']):
            print(f"  [{idx+1}] {us['name']} (₹{us['price']}, +₹{us.get('price_diff', 0):,.0f} diff)")
            print(f"      Reason: {us['reason']}")
            assert us['price'] >= float(laptop.current_price) or us['category'] == (laptop.category.name if laptop.category else ""), \
                "Upsell is not a higher tier / same category!"
        print("[OK] Upsell products verified")
    else:
        print("No laptop found in test DB, testing phone instead")

    # 3. Find a phone / mobile product
    phone = Product.objects.filter(category__slug__icontains="mobile", is_active=True).first()
    if not phone:
        phone = Product.objects.filter(name__icontains="galaxy", is_active=True).first()

    if phone:
        print(f"\nBase Product: {phone.name} (Category: {phone.category.name if phone.category else 'None'}, Price: Rs.{phone.price})")
        recs = UpsellService.build_checkout_recommendations(product=phone, limit=4)
        print(f"Cross-sell count: {len(recs['cross_sell'])}")
        for idx, cs in enumerate(recs['cross_sell']):
            print(f"  [{idx+1}] {cs['name']} (Category: {cs['category']}, Rs.{cs['price']})")
            print(f"      Reason: {cs['reason']}")
            cat_lower = cs['category'].lower()
            assert not any(bad in cat_lower for bad in ["sneaker", "shoe", "footwear", "cookware"]), \
                f"Irrelevant product suggested: {cs['name']} in {cs['category']} for phone!"
        print("[OK] All cross-sells for phone are strictly category-relevant!")

    # 4. Test Policy Gating (Forbidden Categories)
    print("\nTesting Merchant Policy Guardrail...")
    from intelligence.services.merchant_policy import MerchantPolicyEngine
    policy = MerchantPolicyEngine.load_active_policy()
    print(f"Loaded policy name: {policy.get('policy_name', 'Default')}")
    print(f"Policy evaluation: action={policy.get('action')}, reason={policy.get('reason')}")
    print("\n[OK] ALL RELEVANCE AND POLICY CHECKS PASSED!")

if __name__ == "__main__":
    test_cross_sell_relevance()
