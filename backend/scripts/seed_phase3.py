#!/usr/bin/env python
"""
RazorHub Database Seeding — Phase 3
Seed products from frontend/dist/product-media/ images.
Deduplicates variants, generates product details from filenames,
maps to categories and seller stores.
"""
import os
import sys
import re
import django
from decimal import Decimal
from pathlib import Path
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User
from sellers.models import Store
from products.models import Product, Category, ProductImage, Inventory

# Base URL for product-media (relative path that frontend serves)
MEDIA_BASE = "/product-media"

# Directory containing product images
MEDIA_DIR = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist" / "product-media"

# ── Category keyword mapping ──
CATEGORY_KEYWORDS = {
    "electronics": ["laptop", "macbook", "dell-xps", "lenovo", "hp-pavilion", "monitor", "keyboard",
                     "mouse", "webcam", "usb-c", "charger", "cable", "ssd", "hard-drive", "hub",
                     "dock", "raspberry-pi", "arduino", "graphic-tablet", "portable-monitor",
                     "smart-bulb", "smart-plug", "power-bank", "cctv", "iphone", "samsung-galaxy",
                     "xiaomi-pad", "xiaomi-smart", "tp-link", "ubiquiti", "caldigit", "anker",
                     "sandisk", "silicon-power", "wd-", "foldable-phone", "screen-protector",
                     "mobile-grip", "phone-case", "phone-ring", "samsung-charger", "iphone-16"],
    "audio-sound": ["headphones", "earbuds", "speaker", "bluetooth-speaker", "soundbar",
                     "podcast-mic", "studio-headphones", "portable-audio", "logitech-g435",
                     "sony-wh", "airpods", "sleek-wireless-headphone"],
    "photography": ["camera", "canon", "nikon", "lens", "tripod", "ring-light", "action-camera",
                     "lens-cleaning"],
    "gaming": ["playstation", "xbox", "gaming-chair", "console", "vr-headset", "arcade",
               "mechanical-keyboard", "rgb-mouse-pad", "corsair", "razer", "psx-retro",
               "game-storage", "trigger-grip"],
    "mens-clothing": ["jacket", "blazer", "hoodie", "t-shirt", "shirt", "jeans", "jogger",
                       "shorts", "cargo", "denim", "kurta", "sweatshirt", "tee", "crew-neck",
                       "pullover", "nepali-hoodie", "puma", "clothing"],
    "womens-clothing": ["womens", "women", "dress", "skirt", "biylaclesen", "danvouy", "mbj",
                         "opna", "rain-jacket-women", "lock-and-love"],
    "sneakers": ["sneaker", "shoes", "nike-court", "goldstar", "cleats", "high-top"],
    "furniture": ["sofa", "chair", "desk", "table", "bed", "credenza", "armchair", "workstation",
                   "bedside", "bathroom-sink", "knoll"],
    "appliances": ["air-fryer", "blender", "rice-cooker", "mixer", "toaster", "kettle",
                    "vacuum-cleaner", "air-purifier", "refrigerator", "kitchen-knife",
                    "kitchen-storage", "hand-blender", "water-filter"],
    "groceries": ["atta", "rice", "oil", "milk", "eggs", "noodles", "wai-wai", "bread",
                   "coffee", "basmati", "fortune", "aashirvaad", "amul", "chicken", "beef",
                   "fish", "apple", "cucumber", "onion", "pizza", "biryani", "momo",
                   "wings", "cooking-oil", "cold-coffee"],
    "books": ["book", "novel", "programming", "atomic-habits", "entrance-exam", "grammar",
              "physics", "history-atlas", "gk-nepal", "javascript", "python-programming",
              "see-prep", "kids-story", "anime-art"],
    "stationery": ["notebook", "pencil", "pen", "eraser", "marker", "highlighter", "calculator",
                    "geometry-box", "clipboard", "clip-board", "sticky-notes", "planner",
                    "diary", "desk-organizer", "desk-tray", "exam-answer", "exam-clipboard",
                    "classmate", "apsara", "nataraj", "gel-pen", "pocket-notebook"],
    "sports-fitness": ["yoga-mat", "dumbbell", "resistance-band", "basketball", "football",
                        "cricket", "jump-rope", "gym-water", "fitness", "training",
                        "bike-helmet", "skate-helmet", "reflective-vest", "training-cone"],
    "automotive": ["car-", "dash-cam", "tire-inflator", "tyre-inflator", "bike-lock",
                    "bike-mirror", "bike-phone", "helmet-visor", "riding-gloves",
                    "led-bike-light", "car-vacuum", "car-audio"],
    "pets": ["dog-food", "cat-food", "dog-collar", "cat-litter", "pet-grooming",
             "pet-toy", "pet-water", "leash"],
    "jewellery-accessories": ["watch", "sunglasses", "bracelet", "necklace", "earring",
                               "ring", "jewelry", "pierced-owl", "solid-gold", "white-gold",
                               "john-hardy", "cap-and-beanie", "scarf", "jute-tote",
                               "laptop-backpack", "laptop-sleeve", "school-bag", "backpack",
                               "school-backpack"],
    "home-kitchen": ["curtain", "bed-sheet", "bedsheet", "storage-basket", "lunch-box",
                      "water-bottle", "led-desk", "study-lamp", "lamp"],
    "eco-sustainable": ["bamboo", "reusable", "compost", "solar", "steel-straw", "jute"],
}

# Store assignment by category slug
STORE_BY_CATEGORY = {
    "electronics": "Ananya Electronics Hub",
    "audio-sound": "Ananya Electronics Hub",
    "photography": "Kavya Photo Studio",
    "gaming": "Ananya Electronics Hub",
    "mens-clothing": "Amit Fashion House",
    "womens-clothing": "Amit Fashion House",
    "sneakers": "Sinha Sports & Sneakers",
    "furniture": "Isha Home & Living",
    "appliances": "Isha Home & Living",
    "groceries": "Deepak Grocery & Books",
    "books": "Deepak Grocery & Books",
    "stationery": "Deepak Grocery & Books",
    "sports-fitness": "Sinha Sports & Sneakers",
    "automotive": "Sinha Sports & Sneakers",
    "pets": "Isha Home & Living",
    "jewellery-accessories": "Joshi Jewels & Accessories",
    "home-kitchen": "Isha Home & Living",
    "eco-sustainable": "Isha Home & Living",
}

# Price ranges by category
PRICE_RANGES = {
    "electronics": (1500, 85000),
    "audio-sound": (800, 25000),
    "photography": (2000, 150000),
    "gaming": (1200, 50000),
    "mens-clothing": (500, 8000),
    "womens-clothing": (500, 8000),
    "sneakers": (1200, 12000),
    "furniture": (3000, 80000),
    "appliances": (800, 30000),
    "groceries": (50, 2000),
    "books": (150, 2500),
    "stationery": (30, 800),
    "sports-fitness": (300, 8000),
    "automotive": (200, 15000),
    "pets": (100, 5000),
    "jewellery-accessories": (300, 25000),
    "home-kitchen": (200, 8000),
    "eco-sustainable": (150, 3000),
}


def filename_to_title(filename: str) -> str:
    """Convert a filename like 'air-fryer.jpg' to 'Air Fryer'."""
    name = Path(filename).stem
    # Remove trailing -2, -3, -4 suffixes (duplicates)
    name = re.sub(r'-\d+$', '', name)
    # Remove store prefixes like 'diversified-pro-', 'dukan-basics-', 'kina-basics-'
    name = re.sub(r'^(diversified-(pro|mini|max)-|dukan-basics-|kina-basics-|bhat-bhateni-)', '', name)
    # Replace hyphens with spaces and title case
    title = name.replace('-', ' ').strip()
    # Title case with special handling
    words = title.split()
    result = []
    for w in words:
        if w.upper() in ('USB', 'LED', 'SSD', 'RGB', 'VR', 'HD', 'TV', 'XPS', 'HP', 'AI', 'OLED'):
            result.append(w.upper())
        elif w.lower() in ('pro', 'max', 'mini', 'ultra'):
            result.append(w.capitalize())
        else:
            result.append(w.capitalize())
    return ' '.join(result)


def categorize_file(filename: str) -> str:
    """Determine category slug from filename."""
    name = filename.lower()
    for cat_slug, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw in name:
                return cat_slug
    return "electronics"  # fallback


def generate_description(title: str, category: str) -> str:
    """Generate a product description based on title and category."""
    templates = {
        "electronics": f"Premium {title} with advanced features and cutting-edge technology. Designed for performance, reliability, and seamless connectivity in your daily workflow.",
        "audio-sound": f"{title} delivering exceptional sound quality with deep bass and crystal-clear highs. Perfect for music enthusiasts and professionals alike.",
        "photography": f"Professional-grade {title} for photographers and content creators. Exceptional build quality with precision optics and reliable performance.",
        "gaming": f"{title} engineered for the ultimate gaming experience. High performance, responsive controls, and immersive design for competitive and casual gamers.",
        "mens-clothing": f"Stylish {title} crafted from premium materials for the modern man. Comfortable fit with attention to detail and contemporary design.",
        "womens-clothing": f"Elegant {title} designed for comfort and style. Premium fabric with a flattering fit perfect for any occasion.",
        "sneakers": f"{title} combining style and performance. Premium materials, cushioned sole, and modern design for everyday comfort.",
        "furniture": f"Beautifully designed {title} that combines form and function. Quality craftsmanship with durable materials for lasting elegance.",
        "appliances": f"Efficient {title} designed to make your daily tasks easier. Energy-efficient with modern features and reliable performance.",
        "groceries": f"High-quality {title} sourced from trusted suppliers. Fresh, nutritious, and perfect for your daily needs.",
        "books": f"{title} — an essential addition to your collection. Comprehensive content with clear explanations and engaging material.",
        "stationery": f"Premium {title} for students and professionals. High quality materials with practical design for everyday use.",
        "sports-fitness": f"Professional {title} for your fitness journey. Durable construction with ergonomic design for effective training.",
        "automotive": f"High-quality {title} for your vehicle. Precision engineered for safety, performance, and long-lasting durability.",
        "pets": f"Premium {title} for your beloved pets. Made with safe, high-quality ingredients/materials for health and happiness.",
        "jewellery-accessories": f"Exquisite {title} crafted with attention to detail. Premium materials with elegant design for a sophisticated look.",
        "home-kitchen": f"Practical {title} for your home. Quality materials with thoughtful design to enhance your living space.",
        "eco-sustainable": f"Eco-friendly {title} made from sustainable materials. Reduce your environmental footprint without compromising quality.",
    }
    return templates.get(category, f"Premium quality {title}. Designed with care for exceptional performance and lasting value.")


def deduplicate_images(media_dir: Path) -> dict:
    """
    Scan media dir, group by base product name, pick highest quality variant.
    Returns: {base_name: best_file_path}
    """
    # Group files by base name
    groups = {}
    valid_extensions = {'.jpg', '.jpeg', '.png', '.webp'}

    for f in media_dir.iterdir():
        if not f.is_file():
            continue
        if f.suffix.lower() not in valid_extensions:
            continue

        stem = f.stem.lower()
        # Remove -2, -3, -4 suffixes to get base name
        base = re.sub(r'-\d+$', '', stem)
        # Remove store-specific prefixes
        base = re.sub(r'^(diversified-(pro|mini|max)-|dukan-basics-|kina-basics-|bhat-bhateni-)', '', base)

        if base not in groups:
            groups[base] = []
        groups[base].append(f)

    # Pick best file per group (largest = highest quality)
    best = {}
    for base, files in groups.items():
        # Sort by size descending, pick largest
        files.sort(key=lambda x: x.stat().st_size, reverse=True)
        best[base] = files[0]

    return best


def main():
    print("\n" + "=" * 60)
    print("  RazorHub Database Seeding — Phase 3")
    print("  Seeding products from product-media/")
    print("=" * 60)

    if not MEDIA_DIR.exists():
        print(f"  ERROR: Media directory not found: {MEDIA_DIR}")
        return

    # Build lookups
    cat_lookup = {c.slug: c for c in Category.objects.all()}
    store_lookup = {s.name: s for s in Store.objects.all()}

    # Deduplicate images
    print(f"\n  Scanning {MEDIA_DIR}...")
    best_images = deduplicate_images(MEDIA_DIR)
    print(f"  Found {len(best_images)} unique products (after deduplication)")

    # Track existing product names/SKUs to avoid duplicates
    existing_names = set(Product.objects.values_list('name', flat=True))
    existing_skus = set(Product.objects.filter(sku__isnull=False).values_list('sku', flat=True))

    created = 0
    skipped = 0

    for base_name, image_file in sorted(best_images.items()):
        # Generate title
        title = filename_to_title(image_file.name)

        # Skip if product with very similar name exists
        if title in existing_names:
            skipped += 1
            continue

        # Determine category
        cat_slug = categorize_file(base_name)
        category = cat_lookup.get(cat_slug)
        if not category:
            cat_slug = "electronics"
            category = cat_lookup.get(cat_slug)

        # Determine store
        store_name = STORE_BY_CATEGORY.get(cat_slug, "Ananya Electronics Hub")
        store = store_lookup.get(store_name)

        # Generate SKU
        sku_prefix = cat_slug[:4].upper()
        sku = f"SKU-PM-{sku_prefix}-{created + 1:03d}"
        while sku in existing_skus:
            created_alt = random.randint(100, 999)
            sku = f"SKU-PM-{sku_prefix}-{created_alt}"

        # Generate price
        price_range = PRICE_RANGES.get(cat_slug, (500, 10000))
        price = Decimal(str(random.randint(price_range[0], price_range[1])))

        # Generate description
        description = generate_description(title, cat_slug)

        # Generate stock
        stock = random.randint(5, 100)

        # Image URL (relative path for local serving, or we can use the filename)
        # Since these are local files, we use a relative path
        image_url = f"{MEDIA_BASE}/{image_file.name}"

        # Create product
        try:
            product = Product(
                name=title,
                description=description,
                price=price,
                stock=stock,
                sku=sku,
                colors=["#121212", "#C0C0C0"],
                rating=Decimal(str(round(random.uniform(3.8, 4.9), 1))),
                category=category,
                store=store,
                is_active=True,
                is_featured=random.random() > 0.7,
                delivery_time_estimate="3-7 business days",
                base_delivery_fee=Decimal("150.00"),
            )
            product.save()

            ProductImage.objects.create(
                product=product,
                image_url=image_url,
                alt_text=title,
                is_primary=True,
                order=0,
            )

            Inventory.objects.create(
                product=product,
                sku=sku,
                quantity=stock,
                low_stock_threshold=5,
            )

            existing_names.add(title)
            existing_skus.add(sku)
            created += 1

        except Exception as e:
            print(f"  ! Error creating '{title}': {e}")
            skipped += 1

    print(f"\n  Products created: {created}")
    print(f"  Products skipped: {skipped}")
    print(f"\n  Total products in DB: {Product.objects.count()}")
    print(f"  Total images in DB: {ProductImage.objects.count()}")
    print(f"\n  Phase 3 COMPLETE!")


if __name__ == "__main__":
    main()
