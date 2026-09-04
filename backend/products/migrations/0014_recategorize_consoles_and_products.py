from django.db import migrations


def recategorize_products(apps, schema_editor):
    Category = apps.get_model('products', 'Category')
    Product = apps.get_model('products', 'Product')

    # 1. Ensure Gaming category exists
    gaming_cat = Category.objects.filter(slug='gaming').first()
    if not gaming_cat:
        gaming_cat = Category.objects.create(name='Gaming', slug='gaming')

    # Reclassify consoles & handhelds from Laptops to Gaming
    console_names = [
        'Sony PlayStation 5',
        'Xbox Series X',
        'Nintendo Switch OLED',
        'Steam Deck OLED',
        'ASUS ROG Ally',
        'Playstation 5 Digital Edition',
        'Psx Retro Console',
    ]
    for name in console_names:
        Product.objects.filter(name__iexact=name).update(category=gaming_cat)

    # 2. Reclassify Jewellery item placed in Women's Clothing
    jewellery_cat = (
        Category.objects.filter(slug='jewellery-accessories').first()
        or Category.objects.filter(slug='jewelery').first()
    )
    if jewellery_cat:
        Product.objects.filter(name__icontains='Dragon Station Chain Bracelet').update(category=jewellery_cat)
        Product.objects.filter(name__icontains='Solid Gold Petite Micropave').update(category=jewellery_cat)

    # 3. Reclassify Home & Kitchen items
    home_cat = Category.objects.filter(slug='home-kitchen').first()
    if home_cat:
        Product.objects.filter(name__iexact='Steel Straw Set').update(category=home_cat)


def reverse_recategorize(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0013_fix_country_currency_defaults'),
    ]

    operations = [
        migrations.RunPython(recategorize_products, reverse_recategorize),
    ]
