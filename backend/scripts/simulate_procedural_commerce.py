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
from django.contrib.auth import get_user_model

from products.models import Product, Inventory, Review
from sellers.models import SellerProfile, Store
from users.models import Address, CustomerProfile
from orders.models import Order, OrderItem, Payment, Cart, CartItem
from wishlist.models import Wishlist
from crm.models import Ticket, ActivityLog, SellerRecord, CustomerRecord

User = get_user_model()

PAYMENT_GATEWAY_METHODS = [
    ("razorpay", "UPI - PhonePe"),
    ("razorpay", "UPI - Google Pay"),
    ("razorpay", "HDFC NetBanking"),
    ("razorpay", "ICICI NetBanking"),
    ("razorpay", "Axis Bank Credit Card"),
    ("razorpay", "SBI Debit Card"),
    ("cod", "Cash on Delivery"),
]

DELIVERY_ETAS = [
    "Delivered on time",
    "Delivered via BlueDart Express",
    "Delivered via Delhivery Logistics",
    "Out for delivery today",
    "Expected delivery in 1-2 business days",
    "Expected delivery in 3 business days",
]

REVIEW_TEMPLATES = {
    "electronics": [
        ("Exceptional performance & build", 5, "Sound quality and wireless range are phenomenal. Battery easily lasts through the work week. Arrived safely in bubble packaging."),
        ("Very good value for money", 4, "Setup took under 2 minutes. Syncs seamlessly with laptop and phone simultaneously. Solid build quality for this price."),
        ("Decent daily device", 4, "Does the job well. Charging is fast, mic quality is clear on video calls. Happy with the purchase."),
    ],
    "fashion": [
        ("Premium fabric and perfect fit", 5, "The stitch quality and material feel luxurious. Colors match the catalog photos exactly. Highly recommended!"),
        ("Comfortable everyday wear", 5, "Breathable fabric, looks very stylish and fits true to standard Indian sizing. Washed twice with zero shrinkage."),
        ("Good styling & finish", 4, "Looks great paired with denim or formal trousers. Quick delivery to Bengaluru within 48 hours."),
    ],
    "footwear": [
        ("Unbelievably comfortable sole", 5, "Wore these on a 10km run right out of the box. Cushioning is responsive and ankle support is firm. Excellent pair!"),
        ("Great grip and lightweight", 5, "Lightweight construction with grippy rubber outsole. Looks sleek and modern. Arrived with authentic brand box."),
        ("Solid quality sneakers", 4, "Fits snug and comfortable. Clean aesthetics. Highly recommend buying true to size."),
    ],
    "home": [
        ("Sturdy design & very useful", 5, "High quality materials, assembly was straightforward. Adds a modern, organized aesthetic to the room."),
        ("Great addition to the home", 5, "Works exactly as advertised. Energy efficient, silent operation, and durable construction."),
        ("Practical and durable", 4, "Good finishing and reliable daily utility. Packaging was completely scratch-proof."),
    ],
    "general": [
        ("Authentic product, fast dispatch", 5, "100% genuine sealed item. Seller dispatched within 6 hours of placing order. Will buy again!"),
        ("Great shopping experience", 5, "Clean packaging, on-time delivery, and the product exceeded expectations. Great value on RazorHub."),
        ("Satisfied with purchase", 4, "Smooth transaction and genuine product. Customer support was also helpful with delivery updates."),
    ]
}

TICKET_TOPICS = [
    ("Order Delivery Status Inquiry", "general", "Customer requesting updated GPS tracking for upcoming courier transit."),
    ("GST Business Invoice Request", "billing", "Customer requesting formal tax invoice with registered company GSTIN."),
    ("Product Setup & Warranty Query", "product", "Customer inquiring about official brand warranty registration process."),
    ("Address Update Confirmation", "order", "Customer verified alternative doorstep delivery gate instructions."),
]


def simulate_commerce_ecosystem():
    print("=" * 70, flush=True)
    print("STARTING PROCEDURAL COMMERCE SIMULATION", flush=True)
    print("=" * 70, flush=True)

    customers = list(User.objects.filter(role=User.ROLE_CUSTOMER).select_related('customer_profile'))
    sellers = list(SellerProfile.objects.select_related('user', 'store').filter(status='verified'))
    products = list(Product.objects.filter(is_active=True).select_related('store', 'category', 'brand'))

    if not customers or not sellers or not products:
        print("Missing prerequisites. Customers, sellers, or products not found.", flush=True)
        return

    now = timezone.now()
    orders_created = 0
    items_created = 0
    reviews_created = 0
    tickets_created = 0
    activity_logs_created = 0

    print(f"Targeting {len(customers)} customers across {len(sellers)} store catalogs...", flush=True)

    with transaction.atomic():
        # ──────────────────────────────────────────────────────────────────────
        # 1. PROCEDURAL ORDERS WITH PROPER LIFECYCLES & STOCK MANAGEMENT
        # ──────────────────────────────────────────────────────────────────────
        # We will create ~28 realistic historical & active orders
        order_specs = [
            # (status, days_ago, payment_method, is_paid)
            ('delivered', 14, 'razorpay', True),
            ('delivered', 12, 'razorpay', True),
            ('delivered', 10, 'cod', True),
            ('delivered', 9, 'razorpay', True),
            ('delivered', 8, 'razorpay', True),
            ('delivered', 7, 'razorpay', True),
            ('delivered', 6, 'razorpay', True),
            ('delivered', 5, 'razorpay', True),
            ('delivered', 4, 'razorpay', True),
            ('delivered', 3, 'razorpay', True),
            ('shipped', 2, 'razorpay', True),
            ('shipped', 2, 'razorpay', True),
            ('shipped', 1, 'cod', False),
            ('shipped', 1, 'razorpay', True),
            ('processing', 1, 'razorpay', True),
            ('processing', 1, 'razorpay', True),
            ('processing', 0, 'cod', False),
            ('pending', 0, 'razorpay', False),
            ('pending', 0, 'cod', False),
            ('cancelled', 4, 'razorpay', False), # Refunded
            ('cancelled', 2, 'cod', False),
        ]

        delivered_pairs = [] # (user, product) pairs for authentic reviews

        for i, (status, days_ago, pay_method_type, is_paid) in enumerate(order_specs):
            cust = customers[i % len(customers)]
            cust_addr = Address.objects.filter(user=cust).first()
            shipping_addr = (
                f"{cust_addr.full_name}, {cust_addr.line1}, {cust_addr.city}, {cust_addr.state} - {cust_addr.postal_code}, Phone: {cust_addr.phone}"
                if cust_addr else
                f"{cust.first_name} {cust.last_name}, MG Road, Bengaluru, Karnataka - 560038"
            )

            # Pick 1 or 2 products from a specific store catalog for realistic vendor basket
            store_seller = sellers[i % len(sellers)]
            store = store_seller.store
            store_prods = [p for p in products if p.store_id == store.id]
            if not store_prods:
                store_prods = products[i:i+3]

            chosen_prods = random.sample(store_prods, min(len(store_prods), random.choice([1, 2])))
            order_time = now - timedelta(days=days_ago, hours=random.randint(1, 18), minutes=random.randint(5, 55))

            subtotal = Decimal("0.00")
            for p in chosen_prods:
                subtotal += (p.discount_price if p.discount_price else p.price)

            delivery_fee = Decimal("0.00") if subtotal >= Decimal("999.00") else Decimal("60.00")
            discount_amount = Decimal("100.00") if subtotal >= Decimal("2500.00") else Decimal("0.00")
            total_price = subtotal + delivery_fee - discount_amount

            eta_text = "Delivered safely" if status == "delivered" else (
                "Out for delivery with courier" if status == "shipped" else (
                    "Being packed at store warehouse" if status == "processing" else (
                        "Order cancelled - inventory restocked" if status == "cancelled" else "Awaiting fulfillment confirmation"
                    )
                )
            )

            order = Order.objects.create(
                user=cust,
                status=status,
                payment_method=pay_method_type,
                delivery_eta=eta_text,
                delivery_fee=delivery_fee,
                promo_code="WELCOME100" if discount_amount > 0 else "",
                discount_amount=discount_amount,
                total_price=total_price,
                shipping_address=shipping_addr,
                customer_note="Please leave package with security if door unattended." if i % 3 == 0 else "",
            )
            # Backdate order created_at
            Order.objects.filter(id=order.id).update(created_at=order_time, updated_at=order_time)
            orders_created += 1

            # Attach Order Items and deduct/manage stock accordingly
            for p in chosen_prods:
                item_price = p.discount_price if p.discount_price else p.price
                OrderItem.objects.create(
                    order=order,
                    product=p,
                    quantity=1,
                    price=item_price,
                )
                items_created += 1

                # Procedural Stock Logic:
                # If delivered, shipped, or processing -> Stock was deducted for customer!
                if status in ['delivered', 'shipped', 'processing']:
                    if p.stock > 5:
                        p.stock -= 1
                        p.save(update_fields=['stock'])
                        if hasattr(p, 'inventory'):
                            p.inventory.quantity = p.stock
                            p.inventory.save(update_fields=['quantity'])

                # If cancelled -> Stock is restored / untouched
                elif status == 'cancelled':
                    pass # Stock remains healthy

                # Record delivered pairs for review generation
                if status == 'delivered':
                    delivered_pairs.append((cust, p, order_time + timedelta(days=2)))

            # Attach Payment record
            pay_gw, gw_label = random.choice(PAYMENT_GATEWAY_METHODS)
            if status == "delivered":
                pay_status = Payment.STATUS_PAID
            elif status in ["shipped", "processing"]:
                pay_status = Payment.STATUS_PAID if pay_method_type == "razorpay" else Payment.STATUS_PENDING
            elif status == "cancelled":
                pay_status = Payment.STATUS_REFUNDED if pay_method_type == "razorpay" else Payment.STATUS_FAILED
            else:
                pay_status = Payment.STATUS_PENDING

            Payment.objects.create(
                order=order,
                method=pay_method_type,
                status=pay_status,
                amount=total_price,
                provider_reference=f"pay_rzp_{order.id:04d}_{random.randint(10000, 99999)}",
            )

            # Activity Log for audit
            ActivityLog.objects.create(
                actor=cust,
                verb="placed_order",
                target_type="order",
                target_id=str(order.id),
                metadata={
                    "total_price": str(total_price),
                    "gateway": gw_label,
                    "status": status,
                },
            )
            activity_logs_created += 1

        print(f"  -> Created {orders_created} authentic orders with {items_created} line items and payment records.", flush=True)

        # ──────────────────────────────────────────────────────────────────────
        # 2. VERIFIED REVIEWS TIED STRICTLY TO DELIVERED ORDERS
        # ──────────────────────────────────────────────────────────────────────
        seen_reviews = set()
        for cust, prod, review_date in delivered_pairs:
            pair_key = (cust.id, prod.id)
            if pair_key in seen_reviews:
                continue
            seen_reviews.add(pair_key)

            # Pick template matching category
            c_slug = prod.category.slug if prod.category else 'general'
            template_list = REVIEW_TEMPLATES.get(c_slug, REVIEW_TEMPLATES['general'])
            title, rating, comment = random.choice(template_list)

            rev = Review.objects.create(
                product=prod,
                user=cust,
                name=f"{cust.first_name} {cust.last_name}".strip(),
                rating=rating,
                title=title,
                comment=comment,
                is_verified_purchase=True,
            )
            Review.objects.filter(id=rev.id).update(created_at=review_date, updated_at=review_date)
            reviews_created += 1

            # Update product rating and review_count
            prod_reviews = Review.objects.filter(product=prod)
            avg_rating = prod_reviews.aggregate(django.db.models.Avg('rating'))['rating__avg'] or 5.0
            prod.rating = Decimal(str(round(avg_rating, 2)))
            prod.save(update_fields=['rating'])

        print(f"  -> Generated {reviews_created} verified customer reviews on delivered items.", flush=True)

        # ──────────────────────────────────────────────────────────────────────
        # 3. CRM TICKETS & SELLER OPERATIONAL RECORDS
        # ──────────────────────────────────────────────────────────────────────
        # Create realistic support tickets
        created_orders = list(Order.objects.all())
        ticket_specs = [
            ("Order Delivery Status Inquiry", "Customer requesting updated GPS tracking for upcoming courier transit."),
            ("GST Business Invoice Request", "Customer requesting formal tax invoice with registered company GSTIN."),
            ("Product Setup & Warranty Query", "Customer inquiring about official brand warranty registration process."),
            ("Address Update Confirmation", "Customer verified alternative doorstep delivery gate instructions."),
        ]
        for idx, (title, note) in enumerate(ticket_specs):
            cust = customers[idx % len(customers)]
            matched_order = created_orders[idx % len(created_orders)] if created_orders else None
            seller_ref = None
            if matched_order and matched_order.items.exists():
                prod = matched_order.items.first().product
                if prod.store:
                    seller_ref = prod.store.seller

            status = "resolved" if idx < 2 else "open"
            Ticket.objects.create(
                customer=cust,
                order=matched_order,
                seller=seller_ref,
                subject=title,
                description=note,
                priority="medium",
                status=status,
            )
            tickets_created += 1

        # Create SellerRecord in CRM for each store
        for s in sellers:
            SellerRecord.objects.create(
                seller=s,
                status="verified",
                risk_level="normal",
                notes=f"Operational store: {s.store.name}. Category specialization: {s.business_name}. KYC complete.",
            )

        # ──────────────────────────────────────────────────────────────────────
        # 4. ACTIVE SHOPPING CARTS & WISHLISTS FOR ENGAGED CUSTOMERS
        # ──────────────────────────────────────────────────────────────────────
        for c_idx in range(8):
            shopper = customers[c_idx]
            # Active Cart
            cart = Cart.objects.create(user=shopper, actor_type="human")
            sampled_items = random.sample(products, 2)
            for itm in sampled_items:
                CartItem.objects.create(cart=cart, product=itm, quantity=1)

            # Active Wishlist
            wl, _ = Wishlist.objects.get_or_create(user=shopper)
            wl_items = random.sample(products, 3)
            wl.products.set(wl_items)

        print("  -> Initialized active customer shopping carts and wishlists.", flush=True)

    # ──────────────────────────────────────────────────────────────────────────
    # VERIFICATION AUDIT
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70, flush=True)
    print("PROCEDURAL COMMERCE AUDIT SUMMARY")
    print("=" * 70, flush=True)
    print(f"Total Orders:        {Order.objects.count()} (Delivered: {Order.objects.filter(status='delivered').count()}, Shipped: {Order.objects.filter(status='shipped').count()}, Processing: {Order.objects.filter(status='processing').count()}, Cancelled: {Order.objects.filter(status='cancelled').count()})", flush=True)
    print(f"Total Payments:      {Payment.objects.count()} (Paid: {Payment.objects.filter(status='paid').count()}, Pending: {Payment.objects.filter(status='pending').count()}, Refunded: {Payment.objects.filter(status='refunded').count()})", flush=True)
    print(f"Verified Reviews:    {Review.objects.count()} (100% tied to delivered purchases)", flush=True)
    print(f"Active Carts:        {Cart.objects.count()}", flush=True)
    print(f"Wishlists:           {Wishlist.objects.count()}", flush=True)
    print(f"CRM Tickets:         {Ticket.objects.count()}", flush=True)
    print(f"Seller CRM Records:  {SellerRecord.objects.count()}", flush=True)
    print(f"Activity Logs:       {ActivityLog.objects.count()}", flush=True)
    print("=" * 70, flush=True)
    print("PROCEDURAL COMMERCE SIMULATION COMPLETE!", flush=True)


if __name__ == "__main__":
    simulate_commerce_ecosystem()
