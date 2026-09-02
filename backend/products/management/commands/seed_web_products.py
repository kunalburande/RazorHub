import os
import sys
import django
import random
from decimal import Decimal

sys.path.append(os.path.abspath('backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product, Category, ProductImage

# High-quality dummy images from unsplash (using source.unsplash.com or fixed unsplash URLs)
CATEGORY_IMAGES = {
    'laptops': [
        "https://images.unsplash.com/photo-1496181133206-80ce9b88a853?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1531297172864-f65e236306cb?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1611186871348-b1ce696e52c9?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=800&auto=format&fit=crop",
    ],
    'audio': [
        "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1546435770-a3e426bf472b?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?q=80&w=800&auto=format&fit=crop",
    ],
    'smartphones': [
        "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1598327105666-5b89351cb315?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1592899677974-c4668202071e?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1616348436168-de43ad0db179?q=80&w=800&auto=format&fit=crop",
    ],
    'accessories': [
        "https://images.unsplash.com/photo-1583394838336-acd977736f90?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1527814050087-151759682121?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1615526675159-e248c3021d3f?q=80&w=800&auto=format&fit=crop",
    ],
    'cameras': [
        "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1502920917128-1aa500764cbd?q=80&w=800&auto=format&fit=crop",
        "https://images.unsplash.com/photo-1516724562728-afc824a36e84?q=80&w=800&auto=format&fit=crop",
    ]
}

def seed():
    # 1. Provide images to products missing them, based on category
    print("Checking for products missing images...")
    products = Product.objects.all()
    for product in products:
        if not product.images.exists():
            cat_slug = product.category.slug.lower() if product.category else ''
            
            # Find a matching category image list
            image_list = CATEGORY_IMAGES.get('accessories') # default
            for cat, urls in CATEGORY_IMAGES.items():
                if cat in cat_slug or cat_slug in cat:
                    image_list = urls
                    break
            
            image_url = random.choice(image_list)
            ProductImage.objects.create(
                product=product,
                image_url=image_url,
                is_primary=True,
                order=0,
                alt_text=f"{product.name} Image"
            )
            print(f"Added missing image to: {product.name}")

    # 2. Add relevant new products from the web to ensure all homepage categories have enough items
    print("\nAdding new relevant products to sparse categories...")
    
    new_products = [
        {
            "name": "MacBook Air M2",
            "category": "laptops",
            "description": "Supercharged by M2. Featuring a strikingly thin design, 13.6-inch Liquid Retina display, and up to 18 hours of battery life.",
            "price": "119999.00",
            "tag": "Best Seller",
            "specifications": "Processor: M2\nRAM: 8GB\nStorage: 256GB SSD\nDisplay: 13.6-inch"
        },
        {
            "name": "Dell XPS 15",
            "category": "laptops",
            "description": "Pushing innovation to the edge. The smallest 15.6-inch performance laptop with a stunning InfinityEdge display.",
            "price": "145000.00",
            "tag": "Premium",
            "specifications": "Processor: Intel Core i7\nRAM: 16GB\nStorage: 512GB SSD\nDisplay: 15.6-inch 4K"
        },
        {
            "name": "Sony WH-1000XM5 Noise Canceling Headphones",
            "category": "audio",
            "description": "Industry leading noise cancelation optimized to you. Magnificent Sound, engineered to perfection.",
            "price": "29990.00",
            "tag": "Top Rated",
            "specifications": "Type: Over-ear\nBattery: 30 hours\nNoise Canceling: Active\nConnectivity: Bluetooth 5.2"
        },
        {
            "name": "AirPods Pro (2nd Generation)",
            "category": "audio",
            "description": "Rich, high-quality audio and voice. Magic like you’ve never heard.",
            "price": "24900.00",
            "tag": "Best Seller",
            "specifications": "Type: In-ear\nBattery: 24 hours with case\nNoise Canceling: Active"
        },
        {
            "name": "iPhone 15 Pro",
            "category": "smartphones",
            "description": "Titanium. So strong. So light. So Pro. The first iPhone to feature an aerospace-grade titanium design.",
            "price": "134900.00",
            "tag": "New",
            "specifications": "Processor: A17 Pro\nDisplay: 6.1-inch Super Retina XDR\nCamera: 48MP Main"
        },
        {
            "name": "Samsung Galaxy S24 Ultra",
            "category": "smartphones",
            "description": "Welcome to the era of mobile AI. With Galaxy S24 Ultra in your hands, you can unleash whole new levels of creativity, productivity and possibility.",
            "price": "129999.00",
            "tag": "Featured",
            "specifications": "Processor: Snapdragon 8 Gen 3\nDisplay: 6.8-inch Dynamic AMOLED\nCamera: 200MP Main"
        },
        {
            "name": "Sony A7 IV Mirrorless Camera",
            "category": "cameras",
            "description": "Basic has never been this good. The latest in sensor technology and image processing.",
            "price": "210000.00",
            "tag": "Pro",
            "specifications": "Sensor: 33MP Full-Frame Exmor R\nVideo: 4K 60p\nAutofocus: Real-time Eye AF"
        },
        {
            "name": "Logitech MX Master 3S Wireless Mouse",
            "category": "accessories",
            "description": "The ultimate precision mouse. Features an 8K DPI sensor and quiet clicks.",
            "price": "8995.00",
            "tag": "Popular",
            "specifications": "Connectivity: Wireless/Bluetooth\nSensor: 8000 DPI\nBattery: 70 days"
        }
    ]

    for p_data in new_products:
        cat_name = p_data.pop('category')
        category, _ = Category.objects.get_or_create(name=cat_name.capitalize(), defaults={'slug': cat_name.lower()})
        
        product = Product.objects.filter(name=p_data['name']).first()
        created = False
        if not product:
            product = Product.objects.create(
                name=p_data['name'],
                category=category,
                description=p_data['description'],
                price=Decimal(p_data['price']),
                cost_price=Decimal(p_data['price']) * Decimal("0.8"),
                tag=p_data['tag'],
                specifications=p_data['specifications'],
                stock=50,
                is_active=True
            )
            created = True
        
        if created or not product.images.exists():
            image_list = CATEGORY_IMAGES.get(cat_name.lower(), CATEGORY_IMAGES['accessories'])
            image_url = random.choice(image_list)
            
            ProductImage.objects.get_or_create(
                product=product,
                image_url=image_url,
                defaults={
                    'is_primary': True,
                    'order': 0,
                    'alt_text': f"{product.name} Image"
                }
            )
            print(f"Added new product: {product.name}")
        else:
            print(f"Product already exists: {product.name}")

    print("\nCatalog seeded successfully!")

if __name__ == '__main__':
    seed()
