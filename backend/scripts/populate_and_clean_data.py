import os
import sys
import django
from decimal import Decimal

# Set up Django environment
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils.text import slugify

from products.models import Product, Inventory, Review
from sellers.models import SellerProfile, Store
from users.models import Address, CustomerProfile
from orders.models import Order, OrderItem, Payment, Cart, CartItem, TransactionDecision, Consent, IdempotencyRecord
from wishlist.models import Wishlist
from crm.models import Ticket, ActivityLog, SellerRecord, CustomerRecord, Notification
from intelligence.models import AuditEvent
from agent_runtime.models import AgentAuditLog, BusinessInvoice, BookkeepingEntry

User = get_user_model()

INDIAN_CITIES = [
    {"city": "Bengaluru", "state": "Karnataka", "postal_code": "560038", "area": "Indiranagar", "street": "42/1, 100 Feet Road"},
    {"city": "Mumbai", "state": "Maharashtra", "postal_code": "400050", "area": "Bandra West", "street": "88 Hill Road, Near Mehboob Studio"},
    {"city": "New Delhi", "state": "Delhi", "postal_code": "110001", "area": "Connaught Place", "street": "14 Barakhamba Road, Inner Circle"},
    {"city": "Hyderabad", "state": "Telangana", "postal_code": "500081", "area": "HITEC City", "street": "Plot 24, Cyber Towers Avenue"},
    {"city": "Pune", "state": "Maharashtra", "postal_code": "411006", "area": "Koregaon Park", "street": "Lane 5, North Main Road"},
    {"city": "Chennai", "state": "Tamil Nadu", "postal_code": "600034", "area": "Nungambakkam", "street": "29 Sterling Road"},
    {"city": "Kolkata", "state": "West Bengal", "postal_code": "700016", "area": "Park Street", "street": "77 Park Street, Camac Crossing"},
    {"city": "Ahmedabad", "state": "Gujarat", "postal_code": "380015", "area": "Bodakdev", "street": "502 Sindhu Bhavan Road"},
    {"city": "Jaipur", "state": "Rajasthan", "postal_code": "302001", "area": "C-Scheme", "street": "12 Bhagwan Das Road"},
    {"city": "Chandigarh", "state": "Punjab", "postal_code": "160017", "area": "Sector 17", "street": "SCO 45-46, Sector 17-C"},
]

SELLER_STORE_MAP = {
    "ananya.gupta@razorhub.com": {
        "store_name": "Ananya Electronics Hub",
        "business_name": "Ananya Electronics Hub Pvt Ltd",
        "category_focus": "Electronics, Laptops, Audio, Gaming",
        "phone": "+91 98450 11001",
        "tax_id": "29ABCDE1234F1Z5",
        "city": "Bengaluru",
        "state": "Karnataka",
        "area": "Indiranagar, Bengaluru",
        "address": "45/2 100 Feet Road, Indiranagar, Bengaluru, Karnataka 560038",
        "description": "Authorized retailer for premium high-performance electronics, gaming rigs, wireless audio, smart wearables, and computing peripherals.",
    },
    "amit.singh@razorhub.com": {
        "store_name": "Amit Fashion House",
        "business_name": "Amit Fashion House Pvt Ltd",
        "category_focus": "Fashion, Men's & Women's Clothing",
        "phone": "+91 98201 22002",
        "tax_id": "27AABCT3456K1Z2",
        "city": "Mumbai",
        "state": "Maharashtra",
        "area": "Bandra West, Mumbai",
        "address": "12 Linking Road, Bandra West, Mumbai, Maharashtra 400050",
        "description": "Contemporary luxury and everyday apparel, sustainable designer wear, tailored suits, and modern streetwear collections.",
    },
    "kavya.iyer@razorhub.com": {
        "store_name": "Kavya Photo Studio",
        "business_name": "Kavya Photo & Imaging Solutions",
        "category_focus": "Photography & Studio Equipment",
        "phone": "+91 98402 33003",
        "tax_id": "33AAACK7890J1Z4",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "area": "Alwarpet, Chennai",
        "address": "18 TTK Road, Alwarpet, Chennai, Tamil Nadu 600018",
        "description": "Pro-grade mirrorless cameras, cinematic prime lenses, strobe studio lighting, precision gimbals, and visual gear.",
    },
    "isha.banerjee@razorhub.com": {
        "store_name": "Isha Home & Living",
        "business_name": "Isha Home Decor & Living Ltd",
        "category_focus": "Furniture, Appliances, Home & Kitchen",
        "phone": "+91 98303 44004",
        "tax_id": "19AAACI5678M1Z1",
        "city": "Kolkata",
        "state": "West Bengal",
        "area": "Ballygunge, Kolkata",
        "address": "24 Southern Avenue, Ballygunge, Kolkata, West Bengal 700029",
        "description": "Modern Scandinavian furniture, artisanal home decor, ergonomic kitchen appliances, and mindful living accessories.",
    },
    "ramesh.sinha@razorhub.com": {
        "store_name": "Sinha Sports & Sneakers",
        "business_name": "Sinha Sports & Automotive Works",
        "category_focus": "Sneakers, Sports & Fitness, Automotive",
        "phone": "+91 98114 55005",
        "tax_id": "07AAACS9012N1Z9",
        "city": "New Delhi",
        "state": "Delhi",
        "area": "Connaught Place, New Delhi",
        "address": "32 Barakhamba Road, Connaught Place, New Delhi 110001",
        "description": "Exclusive performance footwear, collector sneakers, gym equipment, athletic apparel, and car care detailing kits.",
    },
    "saanvi.joshi@razorhub.com": {
        "store_name": "Joshi Jewels & Accessories",
        "business_name": "Joshi Luxury Jewels & Watches",
        "category_focus": "Jewellery, Watches, Accessories",
        "phone": "+91 98225 66006",
        "tax_id": "27AABCI4321P1Z7",
        "city": "Pune",
        "state": "Maharashtra",
        "area": "Koregaon Park, Pune",
        "address": "10 North Main Road, Koregaon Park, Pune, Maharashtra 411006",
        "description": "Fine 925 sterling silver jewelry, luxury horological timepieces, crafted leather goods, and timeless accessories.",
    },
    "deepak.tiwari@razorhub.com": {
        "store_name": "Deepak Grocery & Books",
        "business_name": "Deepak Provisions & Books Ltd",
        "category_focus": "Groceries, Books, Stationery",
        "phone": "+91 98976 77007",
        "tax_id": "09AAACD8765Q1Z3",
        "city": "Noida",
        "state": "Uttar Pradesh",
        "area": "Sector 18, Noida",
        "address": "Plot 8, Sector 18 Commercial Complex, Noida, Uttar Pradesh 201301",
        "description": "Organic gourmet food staples, artisanal coffees, best-selling literature, academic books, and fine writing stationery.",
    },
    "seller@techvista.in": {
        "store_name": "TechVista Electronics",
        "business_name": "TechVista Retail Solutions Pvt Ltd",
        "category_focus": "Consumer Electronics",
        "phone": "+91 98451 88008",
        "tax_id": "29AAACT1122R1Z6",
        "city": "Bengaluru",
        "state": "Karnataka",
        "area": "Koramangala, Bengaluru",
        "address": "56 80 Feet Road, 4th Block, Koramangala, Bengaluru, Karnataka 560034",
        "description": "Flagship consumer electronics, smart home automation hubs, and audio hardware.",
    },
    "seller@stylecraft.in": {
        "store_name": "StyleCraft Fashion",
        "business_name": "StyleCraft Apparels India Ltd",
        "category_focus": "Apparel & Accessories",
        "phone": "+91 98202 99009",
        "tax_id": "27AABCS3344S1Z1",
        "city": "Mumbai",
        "state": "Maharashtra",
        "area": "Lower Parel, Mumbai",
        "address": "Tower 2, Phoenix Mills Compound, Lower Parel, Mumbai, Maharashtra 400013",
        "description": "High-street fashion, designer activewear, bespoke formalwear, and curated accessories.",
    },
    "seller@homeessentials.in": {
        "store_name": "HomeEssentials India",
        "business_name": "HomeEssentials Retail Pvt Ltd",
        "category_focus": "Home & Living",
        "phone": "+91 98115 10101",
        "tax_id": "07AAACH5566T1Z8",
        "city": "New Delhi",
        "state": "Delhi",
        "area": "Okhla Phase III, New Delhi",
        "address": "A-12 Okhla Industrial Area, Phase III, New Delhi 110020",
        "description": "Essential home appliances, cooktops, organic bed linens, and storage organizational solutions.",
    },
    "seller@glamourbox.in": {
        "store_name": "GlamourBox",
        "business_name": "GlamourBox Luxury Care Pvt Ltd",
        "category_focus": "Beauty & Care",
        "phone": "+91 98403 20202",
        "tax_id": "33AAACG7788U1Z5",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "area": "Adyar, Chennai",
        "address": "40 Gandhi Nagar 2nd Main Road, Adyar, Chennai, Tamil Nadu 600020",
        "description": "Clean organic skincare, dermatologically tested haircare, luxury perfumes, and personal grooming.",
    },
    "seller.saanvi0@store.in": {
        "store_name": "Pillai Enterprises",
        "business_name": "Pillai Retail & Trading Co",
        "category_focus": "General Retail",
        "phone": "+91 98490 30303",
        "tax_id": "36AAACP9900V1Z2",
        "city": "Hyderabad",
        "state": "Telangana",
        "area": "Jubilee Hills, Hyderabad",
        "address": "Road No 36, Jubilee Hills, Hyderabad, Telangana 500033",
        "description": "Curated lifestyle essentials, artisan home crafts, and regional specialty retail.",
    },
    "admin@razorhub.local": {
        "store_name": "RazorHub Retail",
        "business_name": "RazorHub Direct Distribution",
        "category_focus": "Official Marketplace Store",
        "phone": "+91 80 4000 5000",
        "tax_id": "29AAACR0000W1Z0",
        "city": "Bengaluru",
        "state": "Karnataka",
        "area": "MG Road, Bengaluru",
        "address": "100 MG Road, Bengaluru, Karnataka 560001",
        "description": "Official RazorHub direct marketplace catalog, authentic warranty verified products.",
    }
}


def run_pipeline():
    print("=" * 70, flush=True)
    print("STARTING DATABASE CLEANUP, USER ENRICHMENT & STOCK INITIALIZATION", flush=True)
    print("=" * 70, flush=True)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 1: PURGE TRANSACTIONS, ORDERS, CARTS, WISHLISTS, TICKETS, REVIEWS
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[Step 1/4] Purging orders, payments, carts, wishlists, tickets, reviews, and logs...", flush=True)
    with transaction.atomic():
        cnt_orders = Order.objects.all().delete()[0]
        cnt_payments = Payment.objects.all().delete()[0]
        cnt_carts = Cart.objects.all().delete()[0]
        cnt_decisions = TransactionDecision.objects.all().delete()[0]
        cnt_consents = Consent.objects.all().delete()[0]
        cnt_idemp = IdempotencyRecord.objects.all().delete()[0]
        cnt_wishlist = Wishlist.objects.all().delete()[0]
        cnt_tickets = Ticket.objects.all().delete()[0]
        cnt_reviews = Review.objects.all().delete()[0]
        cnt_activity = ActivityLog.objects.all().delete()[0]
        cnt_seller_rec = SellerRecord.objects.all().delete()[0]
        cnt_customer_rec = CustomerRecord.objects.all().delete()[0]
        cnt_audit_events = AuditEvent.objects.all().delete()[0]
        cnt_agent_audit = AgentAuditLog.objects.all().delete()[0]
        cnt_invoices = BusinessInvoice.objects.all().delete()[0]
        cnt_bookkeeping = BookkeepingEntry.objects.all().delete()[0]
        cnt_notifications = Notification.objects.all().delete()[0]

    print(f"  -> Deleted {cnt_orders} orders, {cnt_payments} payments, {cnt_carts} carts", flush=True)
    print(f"  -> Deleted {cnt_wishlist} wishlists, {cnt_tickets} tickets, {cnt_reviews} reviews", flush=True)
    print(f"  -> Deleted {cnt_activity} activity logs, {cnt_seller_rec} seller records, {cnt_customer_rec} customer records", flush=True)
    print(f"  -> Deleted {cnt_audit_events} audit events, {cnt_invoices} invoices, {cnt_bookkeeping} bookkeeping entries", flush=True)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 2: ENRICH ALL USERS WITH COMPLETE NAMES, PHONES, AND ADDRESSES
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[Step 2/4] Enriching all registered users with complete profiles and addresses...", flush=True)
    all_users = list(User.objects.all().order_by("id"))
    updated_users_count = 0
    created_addresses_count = 0
    created_profiles_count = 0

    with transaction.atomic():
        for idx, u in enumerate(all_users):
            city_info = INDIAN_CITIES[idx % len(INDIAN_CITIES)]

            # 1. Format First and Last Name if missing
            if not u.first_name and not u.last_name:
                local_part = u.email.split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ")
                local_part = "".join([c for c in local_part if not c.isdigit()]).strip()
                tokens = local_part.split()
                if len(tokens) >= 2:
                    u.first_name = tokens[0].title()
                    u.last_name = " ".join(tokens[1:]).title()
                elif len(tokens) == 1:
                    u.first_name = tokens[0].title()
                    u.last_name = "Sharma"
                else:
                    u.first_name = "User"
                    u.last_name = f"{u.id}"
                u.save(update_fields=["first_name", "last_name"])

            full_name = f"{u.first_name} {u.last_name}".strip()

            # 2. Format phone number if missing
            if not u.phone:
                simulated_phone = f"+91 98{idx % 90 + 10:02d} {idx * 73 % 90000 + 10000:05d}"
                u.phone = simulated_phone
                u.save(update_fields=["phone"])

            # 3. Format address text on User model if missing
            full_addr_str = f"{city_info['street']}, {city_info['area']}, {city_info['city']}, {city_info['state']} {city_info['postal_code']}"
            if not u.address:
                u.address = full_addr_str
                u.save(update_fields=["address"])

            # 4. Ensure CustomerProfile exists for customers
            if u.role == User.ROLE_CUSTOMER:
                cp, cp_created = CustomerProfile.objects.get_or_create(
                    user=u,
                    defaults={
                        "full_name": full_name,
                        "notes": "Verified marketplace shopper account",
                        "lifetime_value": Decimal("0.00"),
                    }
                )
                if cp_created:
                    created_profiles_count += 1
                elif not cp.full_name:
                    cp.full_name = full_name
                    cp.save(update_fields=["full_name"])

            # 5. Ensure at least one default Address record exists in Address table
            addr_qs = Address.objects.filter(user=u)
            if not addr_qs.exists():
                Address.objects.create(
                    user=u,
                    label="Home",
                    address_type=Address.ADDRESS_SHIPPING,
                    full_name=full_name,
                    phone=u.phone,
                    line1=city_info["street"],
                    line2=city_info["area"],
                    city=city_info["city"],
                    state=city_info["state"],
                    postal_code=city_info["postal_code"],
                    country="India",
                    is_default=True,
                )
                created_addresses_count += 1
            else:
                for a in addr_qs:
                    changed = False
                    if not a.full_name:
                        a.full_name = full_name
                        changed = True
                    if not a.phone:
                        a.phone = u.phone
                        changed = True
                    if not a.line1:
                        a.line1 = city_info["street"]
                        changed = True
                    if not a.city:
                        a.city = city_info["city"]
                        changed = True
                    if not a.state:
                        a.state = city_info["state"]
                        changed = True
                    if not a.postal_code:
                        a.postal_code = city_info["postal_code"]
                        changed = True
                    if changed:
                        a.save()

            updated_users_count += 1

    print(f"  -> Enriched {updated_users_count} users", flush=True)
    print(f"  -> Created {created_addresses_count} new addresses (Total addresses: {Address.objects.count()})", flush=True)
    print(f"  -> Created {created_profiles_count} new customer profiles (Total profiles: {CustomerProfile.objects.count()})", flush=True)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 3: UPDATE SELLER PROFILES AND STORES
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[Step 3/4] Updating seller profiles, stores, and KYC business details...", flush=True)
    seller_users = User.objects.filter(role=User.ROLE_SELLER)
    updated_sellers_count = 0

    with transaction.atomic():
        for s_user in seller_users:
            info = SELLER_STORE_MAP.get(s_user.email)
            if not info:
                store_name = f"{s_user.first_name}'s Marketplace Store" if s_user.first_name else f"Store {s_user.id}"
                info = {
                    "store_name": store_name,
                    "business_name": f"{store_name} Pvt Ltd",
                    "category_focus": "Multi-category Retail",
                    "phone": s_user.phone or "+91 98000 00000",
                    "tax_id": f"29AAACS{s_user.id:04d}K1Z0",
                    "city": "Bengaluru",
                    "state": "Karnataka",
                    "area": "Central Commercial Hub",
                    "address": f"Suite {s_user.id * 10}, Business Bay, Bengaluru, Karnataka 560001",
                    "description": "Registered marketplace merchant with authenticated inventory and verified fulfillment.",
                }

            sp, _ = SellerProfile.objects.get_or_create(
                user=s_user,
                defaults={
                    "business_name": info["business_name"],
                    "phone": info["phone"],
                    "tax_id": info["tax_id"],
                    "status": SellerProfile.STATUS_VERIFIED,
                    "internal_notes": f"Specialization: {info['category_focus']}. KYC documents validated.",
                }
            )
            sp.business_name = info["business_name"]
            sp.phone = info["phone"]
            sp.tax_id = info["tax_id"]
            sp.status = SellerProfile.STATUS_VERIFIED
            sp.internal_notes = f"Specialization: {info['category_focus']}. KYC documents validated."
            sp.save()

            store_slug = slugify(info["store_name"])
            st, _ = Store.objects.get_or_create(
                seller=sp,
                defaults={
                    "name": info["store_name"],
                    "slug": store_slug,
                    "description": info["description"],
                    "address": info["address"],
                    "area": info["area"],
                    "support_email": s_user.email,
                    "support_phone": info["phone"],
                    "is_active": True,
                }
            )
            st.name = info["store_name"]
            if not st.slug:
                st.slug = store_slug
            st.description = info["description"]
            st.address = info["address"]
            st.area = info["area"]
            st.support_email = s_user.email
            st.support_phone = info["phone"]
            st.is_active = True
            st.save()

            updated_sellers_count += 1

    print(f"  -> Verified and updated {updated_sellers_count} seller profiles and linked stores.", flush=True)

    # ──────────────────────────────────────────────────────────────────────────
    # STEP 4: FILL INITIAL STOCKS & INVENTORY RECORDS FOR ALL PRODUCTS (FAST BULK)
    # ──────────────────────────────────────────────────────────────────────────
    print("\n[Step 4/4] Initializing product stocks and ensuring linked Inventory records...", flush=True)
    with transaction.atomic():
        # 1. Update any products with stock < 15 to a healthy initial stock
        low_stock_updated = Product.objects.filter(stock__lt=15).update(stock=35)

        # 2. Synchronize Inventory table
        # Find products missing an Inventory record
        existing_inv_product_ids = set(Inventory.objects.values_list("product_id", flat=True))
        all_product_ids = list(Product.objects.values_list("id", "sku", "stock"))

        new_inventories = []
        for pid, sku, stock in all_product_ids:
            if pid not in existing_inv_product_ids:
                new_inventories.append(
                    Inventory(
                        product_id=pid,
                        sku=sku or f"RH-{pid:05d}",
                        quantity=max(stock, 25),
                        low_stock_threshold=5,
                        reserved_quantity=0,
                        location="Bengaluru Central Fulfillment Hub WH-01",
                    )
                )

        if new_inventories:
            Inventory.objects.bulk_create(new_inventories)
            print(f"  -> Created {len(new_inventories)} missing inventory records.", flush=True)

        # 3. Ensure all existing inventories have positive stock
        Inventory.objects.filter(quantity__lt=15).update(
            quantity=35,
            low_stock_threshold=5,
            reserved_quantity=0,
            location="Bengaluru Central Fulfillment Hub WH-01",
        )

    print(f"  -> Updated {low_stock_updated} low-stock products to 35 units.", flush=True)
    print(f"  -> All {Product.objects.count()} products now have active stock & inventory records.", flush=True)

    # ──────────────────────────────────────────────────────────────────────────
    # FINAL INTEGRITY CHECK
    # ──────────────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70, flush=True)
    print("FINAL INTEGRITY VERIFICATION SUMMARY", flush=True)
    print("=" * 70, flush=True)
    print(f"Users Total:            {User.objects.count()} (0 deleted)", flush=True)
    print(f"  - Admins:             {User.objects.filter(role=User.ROLE_ADMIN).count()}", flush=True)
    print(f"  - Sellers:            {User.objects.filter(role=User.ROLE_SELLER).count()}", flush=True)
    print(f"  - Customers:          {User.objects.filter(role=User.ROLE_CUSTOMER).count()}", flush=True)
    print(f"Addresses Total:        {Address.objects.count()} (Users without address: {User.objects.filter(addresses__isnull=True).count()})", flush=True)
    print(f"Customer Profiles:      {CustomerProfile.objects.count()}", flush=True)
    print(f"Seller Profiles:        {SellerProfile.objects.count()} (All verified)", flush=True)
    print(f"Stores:                 {Store.objects.count()}", flush=True)
    print(f"Products Total:         {Product.objects.count()} (0 deleted)", flush=True)
    print(f"Products with Stock==0: {Product.objects.filter(stock=0).count()}", flush=True)
    print(f"Inventories Total:      {Inventory.objects.count()}", flush=True)
    print(f"Orders Total:           {Order.objects.count()} (Clean slate)", flush=True)
    print(f"Payments Total:         {Payment.objects.count()} (Clean slate)", flush=True)
    print(f"Carts Total:            {Cart.objects.count()} (Clean slate)", flush=True)
    print(f"Wishlists Total:        {Wishlist.objects.count()} (Clean slate)", flush=True)
    print(f"Tickets Total:          {Ticket.objects.count()} (Clean slate)", flush=True)
    print(f"Reviews Total:          {Review.objects.count()} (Clean slate)", flush=True)
    print(f"Activity Logs Total:    {ActivityLog.objects.count()} (Clean slate)", flush=True)
    print(f"Seller Records Total:   {SellerRecord.objects.count()} (Clean slate)", flush=True)
    print("=" * 70, flush=True)
    print("PIPELINE COMPLETED SUCCESSFULLY!", flush=True)


if __name__ == "__main__":
    run_pipeline()
