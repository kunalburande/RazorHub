import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import models
from django.utils.text import slugify
from products.models import Product, ProductImage, Category, Brand

# Realistic Unsplash image fallbacks based on categories
CATEGORY_IMAGES = {
    "electronics": [
        "https://images.unsplash.com/photo-1498049794561-7780e7231661?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1550009158-9effb6e973eb?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1525547719571-a2d4ac8945e2?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1542487354-feaf93476caa?auto=format&fit=crop&w=900&q=80",
        "https://images.unsplash.com/photo-1531297172864-f65e236312a0?auto=format&fit=crop&w=900&q=80"
    ],
    "mobiles": ["https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?auto=format&fit=crop&w=900&q=80"],
    "laptops": ["https://images.unsplash.com/photo-1496181133206-80ce9b88a853?auto=format&fit=crop&w=900&q=80"],
    "accessories": ["https://images.unsplash.com/photo-1625961332771-3f40b0e2bdcf?auto=format&fit=crop&w=900&q=80"],
    "audio": ["https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80"],
    "fashion": ["https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80"],
    "home": ["https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=900&q=80"],
    "beauty": ["https://images.unsplash.com/photo-1596462502278-27bfdc403348?auto=format&fit=crop&w=900&q=80"],
    "groceries": ["https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&w=900&q=80"],
    "gaming": ["https://images.unsplash.com/photo-1598550476439-6847785fcea6?auto=format&fit=crop&w=900&q=80"],
    "appliances": ["https://images.unsplash.com/photo-1556911220-bff31c812dba?auto=format&fit=crop&w=900&q=80"],
    "sports": ["https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=900&q=80"],
    "books": ["https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80"],
    "cameras": ["https://images.unsplash.com/photo-1516035069371-29a1b244cc32?auto=format&fit=crop&w=900&q=80"],
    "networking": ["https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=900&q=80"],
}
DEFAULT_IMAGE = "https://images.unsplash.com/photo-1472851294608-062f824d29cc?auto=format&fit=crop&w=900&q=80"

ELECTRONICS_MOCK = [
    {
        "name": "Sony 55-inch 4K Ultra HD Smart LED TV",
        "description": "Experience stunning 4K detail and vivid colors. This smart TV features seamless streaming and immersive audio for a cinematic home experience.",
        "specs": "Screen Size: 55 inches\nResolution: 4K Ultra HD\nRefresh Rate: 60Hz\nConnectivity: 3 HDMI, 2 USB",
        "price": 85000,
        "discount_price": 79999,
        "stock": 12
    },
    {
        "name": "Samsung 32-inch HD Ready Smart LED TV",
        "description": "Perfect for smaller spaces. Enjoy your favorite shows and movies with brilliant HD picture quality and built-in smart features.",
        "specs": "Screen Size: 32 inches\nResolution: HD Ready\nRefresh Rate: 60Hz\nConnectivity: 2 HDMI, 1 USB",
        "price": 18500,
        "discount_price": 16999,
        "stock": 30
    },
    {
        "name": "LG 24-inch Full HD Monitor",
        "description": "Crisp Full HD resolution for work and play. AMD FreeSync technology ensures smooth, tear-free gaming.",
        "specs": "Screen Size: 24 inches\nResolution: Full HD 1080p\nPanel: IPS\nRefresh Rate: 75Hz",
        "price": 14000,
        "discount_price": 11500,
        "stock": 45
    },
    {
        "name": "Epson EcoTank L3250 A4 Wi-Fi All-in-One Ink Tank Printer",
        "description": "High-yield, low-cost printing. Features Wi-Fi connectivity so you can print directly from your smartphone or tablet.",
        "specs": "Function: Print, Scan, Copy\nConnectivity: Wi-Fi, USB\nPrint Speed: Up to 33 ppm\nInk Type: Ink Tank",
        "price": 16000,
        "discount_price": 14999,
        "stock": 18
    },
    {
        "name": "Anker PowerCore 10000 Portable Charger",
        "description": "Compact and powerful. One of the smallest and lightest 10000mAh portable chargers available.",
        "specs": "Capacity: 10000mAh\nOutput: 2.4A\nPorts: 1 USB-A, 1 Micro-USB\nWeight: 180g",
        "price": 2500,
        "discount_price": 1999,
        "stock": 120
    }
]

class Command(BaseCommand):
    help = "Enrich the catalog by fixing missing images, enhancing details, and adding mock products to empty categories."

    def handle(self, *args, **options):
        # 1. Fill empty categories
        self.stdout.write("--- Filling Empty Categories ---")
        empty_categories = Category.objects.annotate(prod_count=models.Count('products')).filter(prod_count=0)
        
        for category in empty_categories:
            if category.slug == "electronics":
                self.stdout.write(f"Populating 'Electronics' category...")
                # Create a generic brand if not exists
                brand, _ = Brand.objects.get_or_create(name="TechBrand", slug="techbrand")
                
                for idx, item in enumerate(ELECTRONICS_MOCK):
                    product, created = Product.objects.get_or_create(
                        slug=slugify(item["name"]),
                        defaults={
                            "name": item["name"],
                            "category": category,
                            "brand": brand,
                            "description": item["description"],
                            "specifications": item["specs"],
                            "price": Decimal(str(item["price"])),
                            "discount_price": Decimal(str(item["discount_price"])),
                            "cost_price": Decimal(str(item["price"] * 0.7)), # 30% margin
                            "stock": item["stock"],
                            "is_active": True,
                            "rating": Decimal(str(round(random.uniform(4.0, 5.0), 1)))
                        }
                    )
                    
                    if created:
                        # Add image
                        img_urls = CATEGORY_IMAGES.get("electronics", [DEFAULT_IMAGE])
                        img_url = img_urls[idx % len(img_urls)]
                        ProductImage.objects.create(
                            product=product,
                            image_url=img_url,
                            alt_text=product.name,
                            is_primary=True,
                            order=0
                        )
                        self.stdout.write(f" Created: {product.name}")
            else:
                self.stdout.write(f"Skipping empty category: {category.name}")

        # 2. Add images to products missing them
        self.stdout.write("\n--- Adding Missing Images ---")
        products_missing_images = Product.objects.filter(images__isnull=True)
        missing_count = products_missing_images.count()
        self.stdout.write(f"Found {missing_count} products missing images.")
        
        for product in products_missing_images:
            cat_slug = product.category.slug if product.category else ''
            img_list = CATEGORY_IMAGES.get(cat_slug, [DEFAULT_IMAGE])
            img_url = random.choice(img_list)
            
            ProductImage.objects.create(
                product=product,
                image_url=img_url,
                alt_text=product.name,
                is_primary=True,
                order=0
            )
        self.stdout.write(f"Added images for {missing_count} products.")

        # 3. Enhance missing descriptions and specs
        self.stdout.write("\n--- Enhancing Product Details ---")
        needs_enhancement = Product.objects.filter(description="").count()
        
        for product in Product.objects.filter(description=""):
            product.description = f"Experience top quality with the {product.name}. Built with care and designed to deliver excellent performance, this is an essential addition for your needs."
            if not product.specifications:
                product.specifications = f"Brand: {product.brand.name if product.brand else 'Generic'}\nCondition: New\nQuality: Premium"
            product.save(update_fields=["description", "specifications"])
        
        self.stdout.write(f"Enhanced {needs_enhancement} products with descriptions and specs.")
        
        self.stdout.write(self.style.SUCCESS("\nCatalog enrichment complete!"))
