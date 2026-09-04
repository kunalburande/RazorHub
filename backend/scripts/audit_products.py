import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from products.models import Product, ProductImage, Category
from django.db.models import Count

pub_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../frontend/public/product-media'))
pub_files = set(os.listdir(pub_dir)) if os.path.exists(pub_dir) else set()

total_prods = Product.objects.count()
missing_file = []
no_image = []
valid_file = []
http_urls = []
duplicate_urls = []

url_counts = ProductImage.objects.values('image_url').annotate(c=Count('id')).filter(c__gt=1)
dup_url_set = {item['image_url']: item['c'] for item in url_counts}

for p in Product.objects.select_related('category').prefetch_related('images').all():
    img = p.images.first()
    if not img or not img.image_url:
        no_image.append((p.id, p.name, p.category.name if p.category else 'None'))
        continue
    url = img.image_url
    if url in dup_url_set:
        duplicate_urls.append((p.id, p.name, url, dup_url_set[url]))
    
    if url.startswith('/product-media/'):
        fname = url.replace('/product-media/', '')
        if fname not in pub_files:
            missing_file.append((p.id, p.name, p.category.name if p.category else 'None', url))
        else:
            valid_file.append(p.id)
    elif url.startswith('http'):
        http_urls.append((p.id, p.name, url))

print(f"Total Products: {total_prods}")
print(f"Valid Local Files: {len(valid_file)}")
print(f"Missing/Truncated Local Files: {len(missing_file)}")
print(f"HTTP URL Images: {len(http_urls)}")
print(f"No Image: {len(no_image)}")
print(f"Products with Duplicate URLs: {len(duplicate_urls)}")

print("\n--- Missing/Truncated Files (First 20) ---")
for item in missing_file[:20]:
    print(item)

print("\n--- Duplicate URLs (First 15) ---")
for item in duplicate_urls[:15]:
    print(item)

# Check description quality
empty_desc = Product.objects.filter(description='').count()
short_desc = Product.objects.filter(description__isnull=False).extra(where=["char_length(description) < 40"]).count()
print(f"\nEmpty Descriptions: {empty_desc}")
print(f"Short Descriptions (<40 chars): {short_desc}")
