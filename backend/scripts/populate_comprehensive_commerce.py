import os
import sys
import random
from decimal import Decimal
from datetime import timedelta
import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.utils import timezone
from django.db import transaction
from django.db.models import Avg
from django.contrib.auth import get_user_model

from products.models import Product, Inventory, Review, Category
from sellers.models import SellerProfile, Store
from users.models import Address, CustomerProfile
from orders.models import Order, OrderItem, Payment, Cart, CartItem, TransactionDecision, Consent, IdempotencyRecord
from wishlist.models import Wishlist
from crm.models import Ticket, ActivityLog, SellerRecord, CustomerRecord

User = get_user_model()

PAYMENT_METHODS_POOL = [
    ("razorpay", "UPI - PhonePe (Fast Checkout)"),
    ("razorpay", "UPI - Google Pay"),
    ("razorpay", "UPI - Paytm"),
    ("razorpay", "HDFC NetBanking Direct"),
    ("razorpay", "ICICI Bank Corporate/Retail NetBanking"),
    ("razorpay", "Axis Bank Credit Card (Visa)"),
    ("razorpay", "SBI Debit Card (Mastercard)"),
    ("cod", "Cash on Delivery (Doorstep Verification)"),
]

LOGISTICS_CARRIERS = [
    "BlueDart Air Express (AWB #BD-9821-IN)",
    "Delhivery Surface Priority (AWB #DEL-4310-IN)",
    "Shadowfax Local Express (AWB #SF-5502-IN)",
    "DTDC Premium Cargo (AWB #DTDC-1129-IN)",
]

CATEGORY_REVIEW_BANK = {
    "electronics": [
        ("Exceptional soundstage and noise isolation", 5, "The wireless range is rock solid even through multiple walls. Battery easily delivers over 35 hours on a single charge. Very well packed."),
        ("Reliable device, great build quality", 4, "Charges rapidly via Type-C. Clean tactile buttons and low-latency audio during conference calls. Very satisfied with the purchase."),
    ],
    "laptops": [
        ("Blazing fast performance & sharp display", 5, "Boots in under 5 seconds. Handles 4K video rendering and multi-tasking without thermal throttling. Arrived in sealed original box."),
        ("Superb build and battery backup", 5, "Keyboard ergonomics are top notch. Display has excellent color accuracy for design work. Great value on RazorHub."),
    ],
    "mobiles": [
        ("Smooth 120Hz display & crisp cameras", 5, "Daylight photography is crisp with natural dynamic range. Charging speed is phenomenal (0 to 80% in 25 mins)."),
        ("Clean software experience", 4, "No bloatware, snappy app switching and premium in-hand feel. Solid battery life for heavy daily usage."),
    ],
    "fashion": [
        ("Tailored fit and breathable cotton", 5, "Stitching is precise and the fabric feels substantial. Fits true to size and maintains structure after washing."),
        ("Modern styling and rich color", 5, "Colors match the product photos accurately. Very comfortable for both casual and semi-formal wear."),
    ],
    "mens-clothing": [
        ("Comfortable everyday essential", 5, "Premium soft-washed fabric. Doesn't crease easily and collar stays sharp all day. Quick delivery to Bengaluru."),
        ("Great value for formal wear", 4, "Clean cut, elegant buttons, and durable fabric. Excellent addition to work wardrobe."),
    ],
    "womens-clothing": [
        ("Elegant drape and vibrant design", 5, "The craftsmanship is gorgeous. Fabric has a delicate sheen and flows gracefully. Got many compliments!"),
        ("Comfortable and stylish", 5, "Fabric feels cool and soft against the skin. True to measurements provided in the size chart."),
    ],
    "sneakers": [
        ("Responsive cushioning for daily running", 5, "Exceptional arch support and energy return on pavement runs. Outsole grip is reassuring even on wet surfaces."),
        ("Iconic street style and all-day comfort", 5, "Lightweight on feet, cushioned insole, and clean silhouette. Arrived double-boxed with extra laces."),
    ],
    "jewelery": [
        ("Hallmarked authentic finish", 5, "The shine and intricate detailing are remarkable. Comes with a verified certificate of authenticity and velvet pouch."),
        ("Delicate and timeless piece", 5, "Subtle design suitable for daily wear. Sturdy clasp and hypoallergenic finish. Very pleased."),
    ],
    "jewellery-accessories": [
        ("Classy timepiece with premium strap", 5, "Clean dial design with sapphire glass scratch protection. Genuine leather band breaks in comfortably."),
        ("Great gift choice", 5, "High-end presentation box and flawless metallic polish. Looks significantly more expensive than its price tag."),
    ],
    "groceries": [
        ("Fresh, aromatic and 100% organic", 5, "Fresh harvest quality with rich natural aroma. Resealable zip-lock packaging preserves flavor."),
        ("Pantry staple of consistent quality", 4, "Clean grains with zero debris. Cooked to perfection with long fluffy texture."),
    ],
    "books": [
        ("Thought-provoking and masterfully written", 5, "Page quality is crisp with clean typography. Delivered in mint condition without any bent spine or corners."),
        ("Essential reading, highly recommended", 5, "Compelling narrative from the first chapter. Bookmark included in packaging was a nice touch."),
    ],
    "stationery": [
        ("Smooth archival ink and bleeding-free paper", 5, "Notebook paper has zero bleed-through with fountain pens. Binding lays completely flat on desk."),
        ("Durable construction for professional notes", 4, "Hardcover is sturdy and elastic closure is tight. Perfect everyday journal."),
    ],
    "photography": [
        ("Sharp edge-to-edge optics", 5, "Fast autofocus and gorgeous creamy bokeh. Mount tolerances are snug and weather-sealing is reliable."),
        ("Indispensable studio equipment", 5, "Even light distribution and robust alloy build. Compact to pack for on-location shoots."),
    ],
    "furniture": [
        ("Solid hardwood and modern minimalism", 5, "Wood grain is beautiful with smooth matte protective varnish. Assembly took under 15 minutes with provided tools."),
        ("Ergonomic and sturdy build", 5, "Firm support for long work hours. Doesn't wobble and fabric upholstery is high density."),
    ],
    "appliances": [
        ("Whisper-quiet and energy efficient", 5, "Cut down power consumption visibly. Intuitive touch panel with practical preset modes."),
        ("Reliable kitchen workhorse", 5, "Motor power tackles tough ingredients effortlessly. Stainless steel jars are easy to rinse clean."),
    ],
    "home-kitchen": [
        ("Heavy-gauge tri-ply stainless steel", 5, "Heats evenly across induction and gas cooktops. Handles stay cool and food does not stick."),
        ("Modern aesthetic for daily cooking", 4, "Durable, dishwasher safe, and mirror polished. Great value set for kitchen upgrade."),
    ],
    "pets": [
        ("Nutritious ingredients, my pet loves it", 5, "Coat looks noticeably shinier after two weeks. Kibble size is ideal and packaging seals tightly."),
        ("Durable materials, stands up to chewing", 5, "Non-toxic tough rubber that keeps pet engaged. Easy to rinse and clean."),
    ],
    "sports-fitness": [
        ("Commercial gym grade durability", 5, "Non-slip knurled grip and precision weight calibration. Rubber coating protects home flooring."),
        ("High-density non-slip workout mat", 4, "Joint cushioning is superb and surface stays grippy even during intense sweaty workouts."),
    ],
    "gaming": [
        ("Zero input lag and tactile feedback", 5, "Mechanical switches have crisp actuation. RGB lighting is customizable and keycaps have textured PBT feel."),
        ("Immersive spatial audio", 5, "Pinpoints footsteps accurately in competitive shooters. Memory foam ear cushions remain comfortable for hours."),
    ],
    "automotive": [
        ("Professional streak-free ceramic finish", 5, "Repels rainwater and dust effortlessly. High-gloss mirror shine lasts for weeks after single coat."),
        ("Heavy duty portable inflator", 5, "Inflated car tire from 20 to 33 PSI in under 3 minutes. Built-in digital pressure gauge is very accurate."),
    ],
    "eco-sustainable": [
        ("Plastic-free, 100% biodegradable", 5, "Authentic organic materials with zero toxic smell. Mindful packaging with plantable seed tag."),
        ("Sustainable daily alternative", 5, "Feels premium and sturdy while being kind to the planet. Reusable and dishwasher safe."),
    ],
}

SUPPORT_TICKET_SCENARIOS = [
    ("Real-time GPS tracking request", "Order Transit", "Customer inquired about courier driver contact for same-day delivery gate pass.", "resolved"),
    ("Corporate GST tax invoice download", "Billing & Tax", "Customer requested revised B2B GST tax invoice with company credit details.", "resolved"),
    ("Manufacturer warranty registration", "Product Support", "Customer asked for serial number warranty portal verification link.", "resolved"),
    ("Delivery window confirmation", "Logistics", "Customer requested delivery between 4 PM - 7 PM to ensure recipient availability.", "open"),
    ("Bulk corporate order enquiry", "Sales & Enterprise", "Customer inquiring about volume pricing for 50 employee gift sets.", "open"),
    ("Packaging condition verification", "Quality Check", "Customer verified tamper-proof hologram seal on high-value electronics package.", "resolved"),
]


def run_comprehensive_population():
    print("=" * 70, flush=True)
    print("POPULATING COMPREHENSIVE MULTI-CATEGORY COMMERCE ECOSYSTEM")
    print("=" * 70, flush=True)

    # 1. Gather active participants
    customers = list(User.objects.filter(role=User.ROLE_CUSTOMER).select_related('customer_profile'))
    seller_profiles = list(SellerProfile.objects.select_related('user', 'store').filter(status='verified'))
    categories = list(Category.objects.all())
    products = list(Product.objects.filter(is_active=True).select_related('store', 'category', 'brand'))

    print(f"Loaded: {len(customers)} Customers | {len(seller_profiles)} Verified Sellers | {len(categories)} Categories | {len(products)} Products", flush=True)

    # 2. Clean slate for transactional and audit tables
    print("\n[Phase 1] Purging old transactions and orders for clean procedural seed...", flush=True)
    with transaction.atomic():
        Order.objects.all().delete()
        Payment.objects.all().delete()
        Cart.objects.all().delete()
        Wishlist.objects.all().delete()
        Review.objects.all().delete()
        Ticket.objects.all().delete()
        ActivityLog.objects.all().delete()
        SellerRecord.objects.all().delete()
        TransactionDecision.objects.all().delete()
        Consent.objects.all().delete()
        IdempotencyRecord.objects.all().delete()

    print("  -> Old orders and activity logs cleared.", flush=True)

    now = timezone.now()
    orders_created = 0
    items_created = 0
    reviews_created = 0
    tickets_created = 0
    activity_logs_created = 0

    # 3. Create 55+ Procedural Orders across ALL 13 Sellers and ALL Categories
    print("\n[Phase 2] Generating 55+ procedural orders spanning all sellers and categories...", flush=True)

    # We distribute orders systematically across all 13 stores: 4 to 6 orders per store!
    delivered_review_candidates = []
    covered_categories = set()

    with transaction.atomic():
        order_idx = 0
        for s_idx, sp in enumerate(seller_profiles):
            store = sp.store
            store_products = [p for p in products if p.store_id == store.id]
            if not store_products:
                continue

            # Generate 4 to 5 orders per store = 13 * 4.6 ~= 60 orders!
            num_orders_for_store = 5 if s_idx % 2 == 0 else 4

            for o_sub in range(num_orders_for_store):
                order_idx += 1
                cust = customers[(order_idx - 1) % len(customers)]
                cust_addr = Address.objects.filter(user=cust).first()

                shipping_addr = (
                    f"{cust_addr.full_name}, {cust_addr.line1}, {cust_addr.city}, {cust_addr.state} - {cust_addr.postal_code}, Ph: {cust_addr.phone}"
                    if cust_addr else
                    f"{cust.first_name} {cust.last_name}, MG Road, Bengaluru, Karnataka - 560038"
                )

                # Status distribution across lifecycle:
                # 0, 1, 2 -> delivered (earlier in month)
                # 3 -> shipped (in transit)
                # 4 -> processing or cancelled
                if o_sub in [0, 1, 2]:
                    status = 'delivered'
                    days_ago = random.randint(4, 28)
                    pay_method_key, pay_label = random.choice(PAYMENT_METHODS_POOL)
                    pay_status = Payment.STATUS_PAID
                    eta = random.choice(LOGISTICS_CARRIERS) + " - Delivered on time"
                elif o_sub == 3:
                    status = random.choice(['shipped', 'shipped', 'processing'])
                    days_ago = random.randint(1, 3)
                    pay_method_key, pay_label = random.choice(PAYMENT_METHODS_POOL)
                    pay_status = Payment.STATUS_PAID if pay_method_key == 'razorpay' else Payment.STATUS_PENDING
                    eta = random.choice(LOGISTICS_CARRIERS) + " - In Transit (ETA: 1-2 days)"
                else:
                    status = random.choice(['pending', 'cancelled', 'processing'])
                    days_ago = random.randint(0, 2)
                    pay_method_key, pay_label = random.choice(PAYMENT_METHODS_POOL)
                    if status == 'cancelled':
                        pay_status = Payment.STATUS_REFUNDED if pay_method_key == 'razorpay' else Payment.STATUS_FAILED
                        eta = "Order Cancelled - Restocked to store catalog"
                    elif status == 'pending':
                        pay_status = Payment.STATUS_PENDING
                        eta = "Awaiting warehouse fulfillment confirmation"
                    else:
                        pay_status = Payment.STATUS_PAID
                        eta = "Packing items at merchant hub"

                order_timestamp = now - timedelta(days=days_ago, hours=random.randint(1, 20), minutes=random.randint(5, 50))

                # Prioritize picking products from categories not yet covered
                unseen_prods = [p for p in store_products if p.category_id not in covered_categories]
                if unseen_prods:
                    chosen_items = [unseen_prods[0]]
                    covered_categories.add(unseen_prods[0].category_id)
                    remaining = [p for p in store_products if p.id != chosen_items[0].id]
                    if remaining and random.random() < 0.5:
                        chosen_items.extend(random.sample(remaining, 1))
                else:
                    basket_size = min(len(store_products), random.choice([1, 1, 2, 2, 3]))
                    chosen_items = random.sample(store_products, basket_size)
                    for item in chosen_items:
                        covered_categories.add(item.category_id)

                subtotal = sum(p.discount_price if p.discount_price else p.price for p in chosen_items)
                delivery_fee = Decimal("0.00") if subtotal >= Decimal("999.00") else Decimal("50.00")
                discount_amount = Decimal("150.00") if subtotal >= Decimal("3000.00") else Decimal("0.00")
                total_price = subtotal + delivery_fee - discount_amount

                order = Order.objects.create(
                    user=cust,
                    status=status,
                    payment_method=pay_method_key,
                    delivery_eta=eta,
                    delivery_fee=delivery_fee,
                    promo_code="FESTIVE150" if discount_amount > 0 else "",
                    discount_amount=discount_amount,
                    total_price=total_price,
                    shipping_address=shipping_addr,
                    customer_note="Handle with fragile care tag." if s_idx % 3 == 0 else "",
                )
                Order.objects.filter(id=order.id).update(created_at=order_timestamp, updated_at=order_timestamp)
                orders_created += 1

                # Attach order items and deduct/manage stock
                for p in chosen_items:
                    item_price = p.discount_price if p.discount_price else p.price
                    OrderItem.objects.create(
                        order=order,
                        product=p,
                        quantity=1,
                        price=item_price,
                    )
                    items_created += 1

                    # Real stock deduction for active orders
                    if status in ['delivered', 'shipped', 'processing']:
                        if p.stock > 5:
                            p.stock -= 1
                            p.save(update_fields=['stock'])
                            if hasattr(p, 'inventory'):
                                p.inventory.quantity = p.stock
                                p.inventory.save(update_fields=['quantity'])

                    # If delivered, record for authentic customer review
                    if status == 'delivered':
                        delivered_review_candidates.append((cust, p, order_timestamp + timedelta(days=random.randint(2, 4))))

                # Payment row
                Payment.objects.create(
                    order=order,
                    method=pay_method_key,
                    status=pay_status,
                    amount=total_price,
                    provider_reference=f"rzp_tx_{order.id:05d}_{random.randint(10000, 99999)}",
                )

                # Activity Log
                ActivityLog.objects.create(
                    actor=cust,
                    verb="order_placed",
                    target_type="order",
                    target_id=str(order.id),
                    metadata={
                        "store": store.name,
                        "total_price": str(total_price),
                        "payment_mode": pay_label,
                        "status": status,
                    },
                )
                activity_logs_created += 1

        print(f"  -> Generated {orders_created} orders across all {len(seller_profiles)} stores with {items_created} line items and payments.", flush=True)

        # 4. Verified Reviews across diverse categories
        print("\n[Phase 3] Generating 35+ verified customer reviews tied strictly to delivered purchases...", flush=True)
        seen_reviews = set()
        for cust, prod, rev_date in delivered_review_candidates:
            if reviews_created >= 38:
                break
            pair = (cust.id, prod.id)
            if pair in seen_reviews:
                continue
            seen_reviews.add(pair)

            c_slug = prod.category.slug if prod.category else "general"
            review_pool = CATEGORY_REVIEW_BANK.get(c_slug, [
                ("High quality and authentic product", 5, "Received in original sealed packaging. Exact specification match with fast dispatch."),
                ("Reliable seller and smooth delivery", 4, "Good product quality and responsive customer service. Arrived without any damage."),
            ])

            title, stars, text = random.choice(review_pool)
            rev = Review.objects.create(
                product=prod,
                user=cust,
                name=f"{cust.first_name} {cust.last_name}".strip(),
                rating=stars,
                title=title,
                comment=text,
                is_verified_purchase=True,
            )
            Review.objects.filter(id=rev.id).update(created_at=rev_date, updated_at=rev_date)
            reviews_created += 1

            # Update product rating
            avg_r = Review.objects.filter(product=prod).aggregate(Avg('rating'))['rating__avg'] or 5.0
            prod.rating = Decimal(str(round(avg_r, 2)))
            prod.save(update_fields=['rating'])

        print(f"  -> Generated {reviews_created} category-specific verified reviews.", flush=True)

        # 5. CRM Support Tickets & Seller Records
        print("\n[Phase 4] Creating CRM operational support tickets and seller records...", flush=True)
        all_orders = list(Order.objects.all())
        for idx, (subj, cat_label, body, st_status) in enumerate(SUPPORT_TICKET_SCENARIOS):
            cust = customers[idx % len(customers)]
            matched_order = all_orders[idx % len(all_orders)] if all_orders else None
            seller_ref = None
            if matched_order and matched_order.items.exists():
                prod = matched_order.items.first().product
                if prod.store:
                    seller_ref = prod.store.seller

            Ticket.objects.create(
                customer=cust,
                order=matched_order,
                seller=seller_ref,
                subject=subj,
                description=body,
                priority="medium",
                status=st_status,
            )
            tickets_created += 1

        for sp in seller_profiles:
            SellerRecord.objects.create(
                seller=sp,
                status="verified",
                risk_level="normal",
                notes=f"Active vendor storefront: {sp.store.name}. KYC validated. Order fulfillment rate: 98.4%.",
            )

        # 6. Active Shopping Carts & Wishlists
        for u_idx in range(12):
            shopper = customers[u_idx]
            cart = Cart.objects.create(user=shopper, actor_type="human")
            sampled_items = random.sample(products, random.choice([2, 3]))
            for itm in sampled_items:
                CartItem.objects.create(cart=cart, product=itm, quantity=1)

            wl, _ = Wishlist.objects.get_or_create(user=shopper)
            wl.products.set(random.sample(products, 4))

        print("  -> Initialized 12 active carts and wishlists.", flush=True)

    # ──────────────────────────────────────────────────────────────────────────
    # STATISTICAL INTEGRITY AUDIT
    # ──────────────────────────────────────────────────────────────────────────
    from collections import Counter
    cat_counts = Counter()
    store_counts = Counter()
    cust_counts = Counter()
    status_counts = Counter()

    for o in Order.objects.prefetch_related('items__product__category', 'items__product__store').all():
        status_counts[o.status] += 1
        cust_counts[o.user_id] += 1
        for itm in o.items.all():
            cat_counts[itm.product.category.name] += 1
            store_counts[itm.product.store.name if itm.product.store else 'None'] += 1

    print("\n" + "=" * 70, flush=True)
    print("COMPREHENSIVE MULTI-CATEGORY AUDIT SUMMARY")
    print("=" * 70, flush=True)
    print(f"Total Orders:            {Order.objects.count()} (Delivered: {status_counts['delivered']}, Shipped: {status_counts['shipped']}, Processing: {status_counts['processing']}, Cancelled: {status_counts['cancelled']}, Pending: {status_counts['pending']})", flush=True)
    print(f"Total Payments:          {Payment.objects.count()} (Paid: {Payment.objects.filter(status='paid').count()}, Pending: {Payment.objects.filter(status='pending').count()}, Refunded: {Payment.objects.filter(status='refunded').count()})", flush=True)
    print(f"Distinct Stores Active:  {len(store_counts)} / 13 stores with orders", flush=True)
    print(f"Distinct Categories Hit: {len(cat_counts)} / {len(categories)} categories", flush=True)
    print(f"Distinct Customers:      {len(cust_counts)} customers with purchase history", flush=True)
    print(f"Verified Reviews:        {Review.objects.count()} (100% tied to delivered purchases)", flush=True)
    print(f"Active Carts:            {Cart.objects.count()}", flush=True)
    print(f"Wishlists:               {Wishlist.objects.count()}", flush=True)
    print(f"CRM Support Tickets:     {Ticket.objects.count()}", flush=True)
    print(f"Seller CRM Records:      {SellerRecord.objects.count()}", flush=True)
    print(f"Activity Logs:           {ActivityLog.objects.count()}", flush=True)
    print("=" * 70, flush=True)
    print("ALL 13 STORES AND CATEGORIES ARE ACTIVELY OPERATIONAL!")


if __name__ == "__main__":
    run_comprehensive_population()
