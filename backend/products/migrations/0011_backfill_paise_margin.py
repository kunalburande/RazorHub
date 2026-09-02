"""Data migration: backfill price_paise, cost_paise, margin_pct for all existing products.

This migration runs Python code to compute the paisa-denominated fields and margin
from the existing Decimal price/cost_price fields, ensuring all existing data is
consistent with the new AI-commerce schema from RazorHubSeller.
"""
from django.db import migrations


def backfill_paise_and_margin(apps, schema_editor):
    """Compute paise and margin for every existing product."""
    from decimal import Decimal, ROUND_HALF_UP

    Product = apps.get_model("products", "Product")

    products = Product.objects.all()
    updated = []

    for p in products:
        selling = p.discount_price if p.discount_price else p.price

        # price_paise
        if selling is not None:
            p.price_paise = int((selling * 100).to_integral_value(rounding=ROUND_HALF_UP))
        else:
            p.price_paise = 0

        # cost_paise
        if p.cost_price is not None:
            p.cost_paise = int((p.cost_price * 100).to_integral_value(rounding=ROUND_HALF_UP))
        else:
            p.cost_paise = 0

        # margin_pct
        if selling and p.cost_price is not None and selling > 0:
            margin = ((selling - p.cost_price) / selling) * Decimal("100")
            p.margin_pct = margin.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            p.margin_pct = Decimal("0.00")

        updated.append(p)

    if updated:
        Product.objects.bulk_update(updated, ["price_paise", "cost_paise", "margin_pct"], batch_size=500)
        print(f"\n  [OK] Backfilled {len(updated)} products with paise/margin data")


def reverse_noop(apps, schema_editor):
    """No reverse needed — fields will be dropped if migration is reversed."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("products", "0010_ai_commerce_fields"),
    ]

    operations = [
        migrations.RunPython(backfill_paise_and_margin, reverse_noop),
    ]
