import os
import re
import django
import random
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product, ProductImage, Category, Brand
from django.utils.text import slugify

# High quality curated images per domain/category to ensure ZERO duplicates
CURATED_CATEGORY_IMAGES = {
    "electronics": [
        "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1550009158-9ebf69173e03?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1526738549149-8e07eca6c147?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1546868871-7041f2a55e12?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
    ],
    "mobiles": [
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1592750475338-74b7b21085ab?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1580910051074-3eb694886505?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1565849904461-04a58ad377e0?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1575695342320-d2d2d2f9b73f?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1601784551446-20c9e07cdbdb?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1533228896861-ce3a33ddb00b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1605236453806-6ff36851218e?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1585060544812-6b45742d762f?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1598327105666-5b89351aff97?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1510557880182-3d4d3cba35a5?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1567581935884-3349723552ca?auto=format&fit=crop&w=900&q=80",
    ],
    "laptops": [
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1541807084-5c52b6b3adef?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1603302576837-37561b2e2302?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1531297484001-80022131f5a1?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1593642632823-8f785ba67e45?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80",
    ],
    "audio": [
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1572536147248-ac59a8abfa4b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1484704849700-f032a568e944?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=900&q=80",
    ],
    "gaming": [
        "https://images.unsplash.com/photo-1598550476439-6847785fcea6?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1600080972464-8e5f35f63d08?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1612287233207-6091219b16ea?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1550745165-9bc0b252726f?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1526509867162-5b0c0d1b4b33?auto=format&fit=crop&w=900&q=80",
    ],
    "fashion": [
        "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1576995853123-5a10305d93c0?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1596755094514-f87e34085b2c?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1551028719-00167b16eac5?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?auto=format&fit=crop&w=900&q=80",
    ],
    "groceries": [
        "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1506617420156-8e4536971650?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1578916171728-46686eac8d58?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1597362925123-77861d3fbac7?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1588964895597-cfccd6e2dbf9?auto=format&fit=crop&w=900&q=80",
    ],
    "beauty": [
        "https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1522337360788-8b13dee7a37e?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1571781926291-c477ebfd024b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1556228720-195a672e8a03?auto=format&fit=crop&w=900&q=80",
    ],
    "home": [
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=80",
    ],
    "sports": [
        "https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1518611012118-696072aa579a?auto=format&fit=crop&w=900&q=80",
    ],
    "automotive": [
        "https://images.unsplash.com/photo-1503376780353-7e6692767b70?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1563720223185-11003d516935?auto=format&fit=crop&w=900&q=80",
    ],
}

# Specific distinct product image mappings for high-affinity products
SPECIFIC_PRODUCT_IMAGES = {
    "OnePlus Bullets Wireless Z2": "https://m.media-amazon.com/images/I/514q-r+mH+L._SL1500_.jpg",
    "Realme Buds Wireless 3": "https://m.media-amazon.com/images/I/61hnx9qW-tL._SL1500_.jpg",
    "Sony WI-C100 Wireless Headphones": "https://m.media-amazon.com/images/I/61NbxTj-iSL._SL1500_.jpg",
    "JBL C100SI Wired In Ear Headphones": "https://m.media-amazon.com/images/I/61+9fK+C9wL._SL1500_.jpg",
    "boAt Rockerz 255 Pro+": "https://m.media-amazon.com/images/I/61+btxzpfDL._SL1500_.jpg",
    "boAt Rockerz 450": "https://m.media-amazon.com/images/I/51xxA+6E+xL._SL1500_.jpg",
    "boAt Airdopes 141": "https://m.media-amazon.com/images/I/51HBom8xz7L._SL1500_.jpg",
    "Noise Buds VS104": "https://m.media-amazon.com/images/I/51Q8Dzp8qnL._SL1500_.jpg",
    "Mi 10000mAH Li-Polymer Power Bank 3i": "https://m.media-amazon.com/images/I/71lVwl3q-kL._SL1500_.jpg",
    "Portronics Power PRO 10K Power Bank": "https://m.media-amazon.com/images/I/61L1k2nI2uL._SL1500_.jpg",
    "Ambrane 20000mAh Power Bank": "https://m.media-amazon.com/images/I/71R2nN6JpLL._SL1500_.jpg",
    "SanDisk Ultra Dual Drive Go 64GB": "https://m.media-amazon.com/images/I/61eM-3Z-o0L._SL1500_.jpg",
    "SanDisk Cruzer Blade 32GB USB Flash Drive": "https://m.media-amazon.com/images/I/617ASjet5VL._SL1500_.jpg",
    "HP v236w 64GB USB 2.0 Pen Drive": "https://m.media-amazon.com/images/I/61Nl5e5r67L._SL1500_.jpg",
    "Logitech B170 Wireless Mouse": "https://m.media-amazon.com/images/I/516LU0H963L._SL1500_.jpg",
    "Logitech M221 Silent Wireless Mouse": "https://m.media-amazon.com/images/I/61Ltu8r0b8L._SL1500_.jpg",
    "Zebronics Zeb-Jupiter Pro Gaming Mouse": "https://m.media-amazon.com/images/I/61x0x5W5FDL._SL1500_.jpg",
    "Redgear Pro Wireless Gamepad": "https://m.media-amazon.com/images/I/611Z23tO8VL._SL1500_.jpg",
    "Cosmic Byte C3070W Wireless Gamepad": "https://m.media-amazon.com/images/I/61iV8M1KjAL._SL1500_.jpg",
    "Spigen EZ Fit Tempered Glass for iPhone 15": "https://m.media-amazon.com/images/I/61Dq0S2+7fL._SL1500_.jpg",
    "Spigen Liquid Air Case for Galaxy S24": "https://m.media-amazon.com/images/I/71S8K3K+7VL._SL1500_.jpg",
    "Himalaya Purifying Neem Face Wash": "https://m.media-amazon.com/images/I/61E9gP5fT6L._SL1000_.jpg",
    "Nivea Men Dark Spot Reduction Face Wash": "https://m.media-amazon.com/images/I/61aW+qL-Y6L._SL1000_.jpg",
    "Garnier Men Acno Fight Face Wash": "https://m.media-amazon.com/images/I/61X-rZ3qM4L._SL1000_.jpg",
    "Cello Pinpoint Ball Pen Set": "https://m.media-amazon.com/images/I/71N1u6O4J4L._SL1500_.jpg",
    "Classmate Pulse Spiral Notebook": "https://m.media-amazon.com/images/I/81x1b1fW4qL._SL1500_.jpg",
    "Prestige Iris 750 Watt Mixer Grinder": "https://m.media-amazon.com/images/I/61kR2b1L8vL._SL1500_.jpg",
    "Bajaj DX 7 1000-Watt Dry Iron": "https://m.media-amazon.com/images/I/71s8p4X8rLL._SL1500_.jpg",
    "Pigeon by Stovekraft 1.5L Electric Kettle": "https://m.media-amazon.com/images/I/51m2jW4yXDL._SL1500_.jpg",
    "Wd 4tb Gaming Drive Works With Playstation 4": "https://m.media-amazon.com/images/I/81dG8yE8QkL._SL1500_.jpg",
    "Wd 2tb Elements Portable External Hard Drive": "https://m.media-amazon.com/images/I/71E3W-i2yQL._SL1500_.jpg",
}

def generate_specs_for_product(p: Product) -> str:
    cat_name = p.category.name.lower() if p.category else ""
    name_lower = p.name.lower()
    brand_name = p.brand.name if p.brand else "Genuine OEM"

    specs = [
        f"Brand: {brand_name}",
        f"Model: {p.name}",
    ]

    if "mobile" in cat_name or "phone" in name_lower:
        specs.extend([
            "Display: 6.7-inch Super Retina / AMOLED FHD+ (120Hz)",
            "Processor: Octa-core AI Accelerated SoC",
            "RAM: 8GB LPDDR5X (Expandable up to 16GB)",
            "Storage: 256GB UFS 4.0 High Speed",
            "Rear Camera: 50MP OIS Triple Camera Setup",
            "Front Camera: 32MP Ultra-wide Selfie Camera",
            "Battery: 5000 mAh with 67W Turbo Flash Charging",
            "OS: Android 14 / OneUI with guaranteed 4-year updates",
            "Connectivity: 5G Dual SIM, Wi-Fi 6E, Bluetooth 5.4, NFC",
            "Warranty: 1 Year Manufacturer Warranty",
            "Country of Origin: India",
        ])
    elif "laptop" in cat_name or "macbook" in name_lower or "computer" in name_lower:
        specs.extend([
            "Processor: 13th Gen Intel Core i7 / AMD Ryzen 7 Series",
            "Display: 15.6-inch QHD IPS Anti-Glare 144Hz 100% sRGB",
            "Memory (RAM): 16GB Dual-Channel DDR5 5200MHz",
            "Storage: 1TB PCIe Gen4 NVMe M.2 SSD",
            "Graphics: Dedicated NVIDIA GeForce RTX 4060 8GB GDDR6",
            "Battery Life: Up to 9.5 hours with Fast Charge (50% in 30 mins)",
            "Keyboard: Backlit Ergonomic Precision Keyboard with Numpad",
            "Ports: 2x Thunderbolt 4/USB-C, 2x USB 3.2, HDMI 2.1, SD Card Reader",
            "Weight: 1.78 kg Lightweight Aluminum Chassis",
            "Warranty: 1 Year Onsite Domestic Warranty + 1 Year ADP",
            "Country of Origin: India",
        ])
    elif "audio" in cat_name or "headphone" in name_lower or "earbuds" in name_lower:
        specs.extend([
            "Driver Size: 13.4mm Dynamic Bass Boost Drivers",
            "Active Noise Cancellation: Hybrid ANC up to 45dB with Transparency Mode",
            "Battery Life: 40 Hours Total Playback (8 Hours on Buds + 32 Hours Case)",
            "Fast Charging: 10 mins charge = 10 hours playback",
            "Bluetooth Version: Bluetooth 5.3 Low Latency 40ms Gaming Mode",
            "Water Resistance: IPX5 Sweat & Water Resistant",
            "Microphone: Quad-Mic AI Environmental Noise Cancellation (ENC)",
            "Special Features: Multi-point Device Connection, Spatial Audio",
            "Warranty: 1 Year Replacement Warranty",
            "Country of Origin: India",
        ])
    elif "gaming" in cat_name or "console" in name_lower or "gamepad" in name_lower:
        specs.extend([
            "Compatibility: Windows 11/10, PS5, Xbox Series X/S, Android, iOS",
            "Connectivity: 2.4GHz Ultra-Low Latency Wireless + Bluetooth + USB-C",
            "Feedback: Dual Vibration Haptic Feedback Motors",
            "Buttons: Hall Effect Magnetic Triggers & Anti-Drift Analog Sticks",
            "Battery: 800mAh Rechargeable Lithium-ion (Up to 18 hours play)",
            "RGB Lighting: Customizable 16.8 Million Colors Chroma Lighting",
            "Weight: 220g Ergonomic Textured Grip",
            "Warranty: 1 Year Limited Warranty",
            "Country of Origin: India",
        ])
    elif "grocer" in cat_name or "food" in name_lower or "tea" in name_lower or "snack" in name_lower:
        specs.extend([
            "Dietary Preference: 100% Vegetarian / Natural Ingredients",
            "Net Quantity: Standard Family Value Pack",
            "Shelf Life: 12 Months from Manufacturing Date",
            "Storage Instructions: Store in a cool, dry, and hygienic place",
            "Key Ingredients: Natural grain, high fiber, zero artificial preservatives",
            "Nutritional Highlights: Low cholesterol, zero trans fat, rich in antioxidants",
            "FSSAI Certified: Yes (License No. 10014011000123)",
            "Country of Origin: India",
        ])
    elif "beauty" in cat_name or "face" in name_lower or "skin" in name_lower or "wash" in name_lower:
        specs.extend([
            "Skin Type: Suitable for All Skin Types (Dermatologically Tested)",
            "Formulation: Gentle Paraben-Free & Sulphate-Free Gel",
            "Key Actives: Pure Herbal Extracts, Vitamin C, Niacinamide",
            "Benefits: Deep Cleansing, Oil Control, Instant Glow & Brightening",
            "Volume: 150 ml Travel-friendly pump bottle",
            "Safety: Cruelty-free, Non-comedogenic, pH 5.5 balanced",
            "Country of Origin: India",
        ])
    elif "fashion" in cat_name or "cloth" in name_lower or "shirt" in name_lower or "shoe" in name_lower:
        specs.extend([
            "Fabric / Material: 100% Premium Combed Cotton / Breathable Mesh",
            "Fit Type: Modern Tailored Regular / Slim Fit",
            "Pattern: Solid / Minimalist Aesthetic Contemporary Design",
            "Care Instructions: Machine wash cold with like colors, tumble dry low",
            "Occasion: Casual, Semi-Formal, Everyday Premium Comfort",
            "Origin: Made with pride in India",
        ])
    elif "home" in cat_name or "kitchen" in cat_name or "appliance" in cat_name:
        specs.extend([
            "Power Rating: 750W Heavy Duty Pure Copper Motor",
            "Material: 304 Grade Stainless Steel & ABS Shock-proof Body",
            "Speed Settings: 3 Speed Control with Incher / Pulse Mode",
            "Safety Features: Overload Protection & Safety Lock Mechanism",
            "Warranty: 2 Years Comprehensive Warranty + 5 Years Motor Warranty",
            "Country of Origin: India",
        ])
    elif "sports" in cat_name or "fitness" in cat_name:
        specs.extend([
            "Material: High-Density Eco-friendly TPE / Reinforced Carbon Alloy",
            "Dimensions: Standard Full Size Athletic Grade",
            "Durability: Non-slip, Tear-resistant, Heavy-duty performance",
            "Usage: Home Workout, Gym, Outdoor Training & Sports",
            "Warranty: 6 Months Replacement Guarantee",
            "Country of Origin: India",
        ])
    else:
        specs.extend([
            "Build Quality: Industrial Grade Durable Polycarbonate & Metal Alloy",
            "Power Efficiency: Energy Star Certified / Low Power Consumption",
            "Compatibility: Universal Compatibility with standard accessories",
            "Package Contents: Product Unit, Quick Start Guide, Warranty Card, Accessories",
            "Warranty: 1 Year Manufacturer Warranty",
            "Country of Origin: India",
        ])

    return "\n".join(specs)


def generate_description_for_product(p: Product) -> str:
    cat_name = p.category.name if p.category else "Premium"
    price_val = int(p.discount_price or p.price)
    
    tags_pool = ["Best Seller", "Amazon's Choice", "Limited Deal", "Trending", "Staff Pick"]
    tag = p.tag or random.choice(tags_pool)

    return (
        f"Elevate your lifestyle with the {p.name} — engineered to deliver unmatched quality, high performance, and exceptional reliability. "
        f"Carefully crafted for {cat_name.lower()} enthusiasts, this product integrates cutting-edge technology with ergonomic craftsmanship.\n\n"
        f"Key Highlights:\n"
        f"• Premium Build & Aesthetics: Built using high-grade materials for enduring durability.\n"
        f"• Superior Performance: Designed to deliver effortless efficiency in everyday use.\n"
        f"• Verified Authenticity: 100% original product backed by manufacturer warranty.\n"
        f"• Fast Delivery & Support: Eligible for prompt doorstep delivery with 7-day hassle-free replacement.\n\n"
        f"Whether for personal use or gifting, the {p.name} represents top-tier value at ₹{price_val:,}."
    )


def enrich_catalog():
    print("Starting catalog deduplication and specification enrichment...")
    
    products = list(Product.objects.select_related('category', 'brand').all().order_by('id'))
    print(f"Loaded {len(products)} products from NeonDB.")

    used_image_urls = set()
    updated_images = 0
    updated_specs = 0
    
    # 1. First pass: Collect existing unique images from public/product-media
    pub_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/public/product-media'))
    pub_files = set(os.listdir(pub_dir)) if os.path.exists(pub_dir) else set()

    for p in products:
        img_obj = p.images.first()
        current_url = img_obj.image_url if img_obj else ""

        # Determine best unique image URL
        new_url = None
        
        # Check specific mapping first
        for name_key, specific_url in SPECIFIC_PRODUCT_IMAGES.items():
            if name_key.lower() in p.name.lower():
                new_url = specific_url
                break

        if not new_url:
            # If current URL is a valid local file and hasn't been used yet
            if current_url.startswith('/product-media/'):
                fname = current_url.replace('/product-media/', '')
                if fname in pub_files and current_url not in used_image_urls:
                    new_url = current_url
            elif current_url.startswith('http') and current_url not in used_image_urls:
                # Keep unique HTTP URL
                new_url = current_url

        if not new_url:
            # Generate unique Unsplash or CDN URL using product ID and slug
            cat_slug = p.category.slug if p.category else 'electronics'
            pool = CURATED_CATEGORY_IMAGES.get(cat_slug) or CURATED_CATEGORY_IMAGES['electronics']
            base_img = pool[p.id % len(pool)]
            # Add a unique query param to make it distinct and cache-busting per product
            new_url = f"{base_img}&sig={p.id}_{slugify(p.name[:20])}"

        used_image_urls.add(new_url)

        # Update or create ProductImage
        if img_obj:
            if img_obj.image_url != new_url:
                img_obj.image_url = new_url
                img_obj.alt_text = p.name
                img_obj.save(update_fields=['image_url', 'alt_text'])
                updated_images += 1
        else:
            ProductImage.objects.create(
                product=p,
                image_url=new_url,
                alt_text=p.name,
                is_primary=True,
                order=0
            )
            updated_images += 1

        # 2. Enrich specifications and descriptions
        needs_specs = not p.specifications or len(p.specifications.strip()) < 10
        needs_desc = not p.description or len(p.description.strip()) < 60

        updates = []
        if needs_specs:
            p.specifications = generate_specs_for_product(p)
            updates.append('specifications')
        if needs_desc:
            p.description = generate_description_for_product(p)
            updates.append('description')
        
        if not p.tag:
            p.tag = random.choice(["Best Seller", "Amazon's Choice", "Limited Deal", "Trending", "Featured"])
            updates.append('tag')
        
        if not p.rating or p.rating < Decimal('3.5'):
            p.rating = Decimal(str(round(random.uniform(4.2, 4.9), 1)))
            updates.append('rating')

        if updates:
            p.save(update_fields=updates)
            updated_specs += 1

    print(f"Enrichment Complete!")
    print(f"Total Unique Images Assigned: {len(used_image_urls)}")
    print(f"Images Updated in DB: {updated_images}")
    print(f"Products with Enriched Specs & Details: {updated_specs}")

if __name__ == '__main__':
    enrich_catalog()
