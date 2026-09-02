from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import zoneinfo

# ─── Zone definitions ────────────────────────────────────────────────
# RazorHub central fulfillment hubs located in major metropolitan areas across India.
# Zones radiate outward; each has a base fee and standard ETA.

ZONE_CONFIG = {
    # Zone 1 — Core Metro City Areas (< ~5 km from distribution hub)
    "core": {
        "base_fee": Decimal("30.00"),
        "eta_food": "20-30 mins",
        "eta_standard": "1-2 hours",
    },
    # Zone 2 — Inner City & Suburbs (5-15 km)
    "inner": {
        "base_fee": Decimal("50.00"),
        "eta_food": "30-45 mins",
        "eta_standard": "2-4 hours",
    },
    # Zone 3 — Extended Urban / Regional Metro (15-30 km)
    "middle": {
        "base_fee": Decimal("75.00"),
        "eta_food": "45-60 mins",
        "eta_standard": "Same day / 1 day",
    },
    # Zone 4 — Outer Region / Inter-city (30-100 km)
    "outer": {
        "base_fee": Decimal("110.00"),
        "eta_food": "Not available",
        "eta_standard": "1-2 days",
    },
    # Zone 5 — National / Remote Outskirts
    "remote": {
        "base_fee": Decimal("160.00"),
        "eta_food": "Not available",
        "eta_standard": "2-4 days",
    },
}

# Map Indian localities, tech hubs, and major cities to delivery zones. Keys are lowercase.
AREA_ZONE_MAP = {
    # ── Bengaluru Localities ──
    "indiranagar": "core", "koramangala": "core", "mg road": "core", "brigade road": "core",
    "hsr layout": "core", "hsr": "core", "jayanagar": "core", "jp nagar": "core",
    "whitefield": "inner", "electronic city": "inner", "bellandur": "core", "marathahalli": "inner",
    "malleshwaram": "core", "rajajinagar": "core", "hebbal": "inner", "yelahanka": "middle",
    "sarjapur": "inner", "sarjapur road": "inner", "btm layout": "core", "btm": "core",
    "banashankari": "inner", "kalyan nagar": "inner", "kammanahalli": "inner", "bengaluru": "core", "bangalore": "core",

    # ── Delhi NCR Localities ──
    "connaught place": "core", "cp": "core", "hauz khas": "core", "saket": "core",
    "south extension": "core", "vasant kunj": "core", "greater kailash": "core", "gk": "core",
    "dwarka": "inner", "rohini": "inner", "karol bagh": "core", "lajpat nagar": "core",
    "chandni chowk": "core", "pitampura": "inner", "janakpuri": "inner", "delhi": "core", "new delhi": "core",
    "noida": "inner", "greater noida": "middle", "gurugram": "inner", "gurgaon": "inner",
    "cyber city": "inner", "ghaziabad": "middle", "faridabad": "middle",

    # ── Mumbai & MMR Localities ──
    "bandra": "core", "bandra west": "core", "andheri": "core", "andheri west": "core", "andheri east": "core",
    "bkc": "core", "bandra kurla complex": "core", "colaba": "core", "marine drive": "core",
    "dadar": "core", "worli": "core", "lower parel": "core", "juhu": "core", "powai": "inner",
    "malad": "inner", "borivali": "inner", "kandivali": "inner", "goregaon": "inner", "ghatkopar": "inner",
    "thane": "middle", "navi mumbai": "middle", "vashi": "middle", "mumbai": "core",

    # ── Hyderabad Localities ──
    "hitec city": "core", "gachibowli": "core", "madhapur": "core", "kondapur": "core",
    "jubilee hills": "core", "banjara hills": "core", "kukatpally": "inner", "begumpet": "core",
    "secunderabad": "inner", "ameerpet": "core", "dilsukhnagar": "inner", "hyderabad": "core",

    # ── Chennai Localities ──
    "t nagar": "core", "t. nagar": "core", "adyar": "core", "anna nagar": "core",
    "velachery": "inner", "mylapore": "core", "omr": "inner", "guindy": "core",
    "nungambakkam": "core", "alwarpet": "core", "tambaram": "middle", "chennai": "core",

    # ── Pune Localities ──
    "kothrud": "core", "hinjawadi": "inner", "hinjewadi": "inner", "viman nagar": "core",
    "baner": "core", "wakad": "inner", "kalyani nagar": "core", "hadapsar": "inner",
    "shivajinagar": "core", "aundh": "core", "pune": "core",

    # ── Kolkata Localities ──
    "park street": "core", "salt lake": "core", "new town": "inner", "ballygunge": "core",
    "alipore": "core", "howrah": "inner", "dum dum": "inner", "kolkata": "core",

    # ── Major Indian Cities (Tier 1 & Tier 2) ──
    "ahmedabad": "inner", "surat": "inner", "vadodara": "inner",
    "jaipur": "inner", "chandigarh": "inner", "lucknow": "inner", "kanpur": "inner",
    "indore": "inner", "bhopal": "inner", "nagpur": "inner", "nashik": "inner",
    "kochi": "inner", "coimbatore": "inner", "thiruvananthapuram": "inner",
    "patna": "middle", "bhubaneswar": "middle", "visakhapatnam": "middle", "vijayawada": "middle",
    "guwahati": "middle", "ranchi": "middle", "dehradun": "middle", "mysuru": "middle", "mysore": "middle",
    "goa": "middle", "panaji": "middle", "mangaluru": "middle", "mangalore": "middle",
    "amritsar": "middle", "ludhiana": "middle", "varanasi": "middle", "agra": "middle",
    "shimla": "outer", "srinagar": "remote", "jammu": "outer", "ladakh": "remote", "leh": "remote",
}

# ─── Category-based surcharges ───────────────────────────────────────
CATEGORY_SURCHARGE = {
    "electronics": Decimal("30.00"),
    "furniture": Decimal("80.00"),
    "appliances": Decimal("50.00"),
    "beverages": Decimal("15.00"),     # heavy liquids
}

# ─── Thresholds & multipliers ────────────────────────────────────────
FREE_DELIVERY_THRESHOLD = Decimal("999.00")    # free delivery over ₹999
HEAVY_ORDER_ITEMS_THRESHOLD = 5                # surcharge if > 5 distinct items
HEAVY_ORDER_SURCHARGE = Decimal("25.00")
PEAK_HOUR_MULTIPLIER = Decimal("1.20")         # 20% surge during peak hours
NIGHT_SURCHARGE = Decimal("40.00")             # flat surcharge 9 PM – 6 AM
MIN_DELIVERY_FEE = Decimal("30.00")            # minimum ₹30
MAX_DELIVERY_FEE = Decimal("250.00")           # cap at ₹250


def _resolve_zone(shipping_address: str) -> str:
    """Match an address string to the best zone, defaulting to 'middle'."""
    addr = shipping_address.lower().strip()
    # Try longest match first so "new delhi" beats "delhi", "hsr layout" beats "hsr"
    for area in sorted(AREA_ZONE_MAP.keys(), key=len, reverse=True):
        if area in addr:
            return AREA_ZONE_MAP[area]
    return "middle"  # sensible default for unlisted Indian cities / areas


def _get_ist_now() -> datetime:
    """Return current timestamp in Indian Standard Time (IST - Asia/Kolkata)."""
    try:
        ist_zone = zoneinfo.ZoneInfo("Asia/Kolkata")
        return datetime.now(ist_zone)
    except Exception:
        return datetime.now()


def _is_peak_hour() -> bool:
    """Check if current IST falls in peak delivery windows (11:00-14:00, 18:00-21:00)."""
    hour = _get_ist_now().hour
    return (11 <= hour <= 14) or (18 <= hour <= 21)


def _is_night() -> bool:
    """Check if current IST falls in night delivery window (21:00-06:00)."""
    hour = _get_ist_now().hour
    return hour >= 21 or hour < 6


def calculate_delivery_info(shipping_address: str, products, quantity_map: dict = None) -> tuple:
    """
    Calculate delivery fee and ETA for an order on a per-item basis.

    Algorithm:
    1. Resolve customer shipping zone and product origin zone.
    2. If zones match (same local hub zone), fee is ₹0 for local dispatch.
    3. Otherwise, use higher of customer zone base fee or product base fee.
    4. Apply category and time-of-day surcharges (IST).
    5. Return total aggregated fee and dictionary of item ETAs/fees.
    """
    if quantity_map is None:
        quantity_map = {}

    shipping_zone = _resolve_zone(shipping_address)
    shipping_zone_cfg = ZONE_CONFIG[shipping_zone]

    if not products:
        return Decimal("50.00"), {}

    total_fee = Decimal("0.00")
    item_deliveries = {}
    
    is_night = _is_night()
    is_peak = _is_peak_hour()

    for product in products:
        # 1. Determine product origin zone (store area)
        store_area = product.store.area if product.store and product.store.area else "indiranagar"
        product_zone = _resolve_zone(store_area)
        
        # 2. Check for free local delivery (same zone)
        if product_zone == shipping_zone:
            item_fee = Decimal("0.00")
        else:
            # 3. Base fee: higher of customer zone fee or product's base fee override
            item_fee = max(shipping_zone_cfg["base_fee"], product.base_delivery_fee)
            
            # 4. Category surcharge
            cat_slug = product.category.slug.lower() if product.category else ""
            if cat_slug in CATEGORY_SURCHARGE:
                item_fee += CATEGORY_SURCHARGE[cat_slug]
                
            # 5. Time-of-day multipliers
            if is_night:
                item_fee += NIGHT_SURCHARGE
            elif is_peak:
                item_fee = (item_fee * PEAK_HOUR_MULTIPLIER).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                
            # 6. Clamp between MIN and MAX
            if item_fee > Decimal("0.00"):
                item_fee = max(item_fee, MIN_DELIVERY_FEE)
                item_fee = min(item_fee, MAX_DELIVERY_FEE)
                
            item_fee = item_fee.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # 7. Determine ETA
        dte = product.delivery_time_estimate.lower()
        if "min" in dte or "hour" in dte:
            eta = shipping_zone_cfg["eta_food"]
        else:
            eta = shipping_zone_cfg["eta_standard"]

        item_deliveries[str(product.id)] = {
            "fee": str(item_fee),
            "eta": eta
        }
        total_fee += item_fee

    return total_fee, item_deliveries


import hashlib
import json
from django.conf import settings
from datetime import timedelta
from orders.serializers import PROMO_CODES

def _generate_quote_hash(cart_id, items_data, totals, expires_at_iso):
    """Generate a stable HMAC-SHA256 hash for a cart quote."""
    hash_data = {
        "cart_id": str(cart_id),
        "items": sorted([
            {"product_id": str(item["product_id"]), "quantity": item["quantity"], "price": float(item["price"])}
            for item in items_data
        ], key=lambda x: x["product_id"]),
        "subtotal": float(totals["subtotal"]),
        "delivery_fee": float(totals["delivery_fee"]),
        "discount_amount": float(totals["discount_amount"]),
        "total": float(totals["total"]),
        "promo_code": totals.get("promo_code", ""),
        "shipping_address": totals.get("shipping_address", ""),
        "expires_at": expires_at_iso
    }
    hash_str = json.dumps(hash_data, sort_keys=True)
    
    # Use HMAC with SECRET_KEY to prevent forgery
    import hmac
    return hmac.new(settings.SECRET_KEY.encode('utf-8'), hash_str.encode('utf-8'), hashlib.sha256).hexdigest()


def generate_quote(cart, shipping_address="", promo_code=""):
    """Generates an immutable quote for a Cart."""
    items = cart.items.select_related('product', 'product__store', 'product__category')
    
    items_data = []
    products = []
    quantity_map = {}
    subtotal = Decimal("0")
    
    for item in items:
        products.append(item.product)
        quantity_map[item.product.id] = item.quantity
        items_data.append({
            "product_id": item.product.id,
            "quantity": item.quantity,
            "price": item.product.current_price
        })
        subtotal += item.product.current_price * item.quantity
        
    delivery_fee, _ = calculate_delivery_info(shipping_address, products, quantity_map)
    
    promo_code = promo_code.strip().lower()
    discount_rate = PROMO_CODES.get(promo_code, Decimal("0"))
    discount_amount = (subtotal * discount_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    total = (subtotal + delivery_fee - discount_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    
    expires_at = _get_ist_now() + timedelta(minutes=15)
    expires_at_iso = expires_at.isoformat()
    
    totals = {
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "discount_amount": discount_amount,
        "total": total,
        "promo_code": promo_code,
        "shipping_address": shipping_address,
    }
    
    quote_hash = _generate_quote_hash(cart.id, items_data, totals, expires_at_iso)
    
    return {
        "cartId": cart.id,
        "subtotal": subtotal,
        "deliveryFee": delivery_fee,
        "discountAmount": discount_amount,
        "total": total,
        "currency": "INR",
        "expiresAt": expires_at_iso,
        "quoteHash": quote_hash,
        "promoCode": promo_code,
        "shippingAddress": shipping_address,
    }


def validate_quote(cart, quote_hash, expires_at_iso, shipping_address="", promo_code=""):
    """Validates an existing quote hash."""
    try:
        expires_at = datetime.fromisoformat(expires_at_iso)
    except ValueError:
        return False, "Invalid expiry format"
        
    if _get_ist_now() > expires_at:
        return False, "Quote expired"
        
    # Re-run generation logic to verify nothing changed (prices, inventory, logic)
    fresh_quote = generate_quote(cart, shipping_address, promo_code)
    
    # We must match the hash, BUT since generation uses the current time for expiry, 
    # we need to override it with the provided expiry to check the hash correctly
    # Wait, the easiest way is to recalculate the hash with the provided expires_at_iso
    items_data = []
    for item in cart.items.all():
        items_data.append({
            "product_id": item.product.id,
            "quantity": item.quantity,
            "price": item.product.current_price
        })
        
    totals = {
        "subtotal": fresh_quote["subtotal"],
        "delivery_fee": fresh_quote["deliveryFee"],
        "discount_amount": fresh_quote["discountAmount"],
        "total": fresh_quote["total"],
        "promo_code": fresh_quote["promoCode"],
        "shipping_address": fresh_quote["shippingAddress"],
    }
    
    expected_hash = _generate_quote_hash(cart.id, items_data, totals, expires_at_iso)
    
    if expected_hash != quote_hash:
        return False, "Quote hash mismatch or cart changed"
        
    return True, "Valid"
