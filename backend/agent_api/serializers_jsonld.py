"""
JSON-LD Serializers for Agent-Readable Catalog.

Exposes product data in Schema.org JSON-LD format so AI buyer agents
(Copilot, ChatGPT Shopping, UAP agents) can discover, compare,
and transact without scraping HTML.
"""
from rest_framework import serializers
from products.models import Product, ProductImage, Inventory


class JsonLdProductSerializer(serializers.ModelSerializer):
    """
    Schema.org Product JSON-LD serializer.
    Output conforms to https://schema.org/Product for agent consumption.
    """

    class Meta:
        model = Product
        fields = []  # We override to_representation entirely

    def to_representation(self, instance):
        # Determine availability
        stock = instance.stock
        if hasattr(instance, 'inventory'):
            stock = instance.inventory.available_quantity

        if stock > 10:
            availability = "https://schema.org/InStock"
        elif stock > 0:
            availability = "https://schema.org/LimitedAvailability"
        else:
            availability = "https://schema.org/OutOfStock"

        # Primary image
        primary_image = None
        if hasattr(instance, '_prefetched_objects_cache') and 'images' in instance._prefetched_objects_cache:
            images = instance._prefetched_objects_cache['images']
            primary = [img for img in images if img.is_primary]
            primary_image = primary[0].image_url if primary else (images[0].image_url if images else None)
        else:
            img = instance.images.filter(is_primary=True).first() or instance.images.first()
            if img:
                primary_image = img.image_url

        # Build JSON-LD
        data = {
            "@context": "https://schema.org",
            "@type": "Product",
            "productID": str(instance.id),
            "name": instance.name,
            "description": instance.description[:500] if instance.description else "",
            "sku": instance.sku or f"RH-{instance.id}",
            "url": f"/products/{instance.slug}/",
            "category": instance.category.name if instance.category else "General",
        }

        if primary_image:
            data["image"] = primary_image

        if instance.brand:
            data["brand"] = {
                "@type": "Brand",
                "name": instance.brand.name,
            }

        # Offer
        offer = {
            "@type": "Offer",
            "price": float(instance.current_price),
            "priceCurrency": instance.currency or "INR",
            "availability": availability,
            "itemCondition": "https://schema.org/NewCondition",
        }

        if instance.store:
            offer["seller"] = {
                "@type": "Organization",
                "name": instance.store.name,
            }

        data["offers"] = offer

        # Rating
        if instance.rating and float(instance.rating) > 0:
            data["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": float(instance.rating),
                "bestRating": 5,
            }

        # Agent-specific extensions
        data["agent_actions"] = ["add_to_cart", "check_stock", "start_checkout", "compare"]
        data["agent_metadata"] = {
            "slug": instance.slug,
            "stock_quantity": stock,
            "delivery_estimate": instance.delivery_time_estimate,
            "delivery_fee": float(instance.base_delivery_fee),
        }

        # Structured attributes for comparison
        if hasattr(instance, 'ai_attributes'):
            attrs = instance.ai_attributes.all() if hasattr(instance.ai_attributes, 'all') else []
            if attrs:
                data["additionalProperty"] = [
                    {
                        "@type": "PropertyValue",
                        "name": attr.key,
                        "value": attr.value,
                    }
                    for attr in attrs
                ]

        return data


class JsonLdCatalogSerializer(serializers.Serializer):
    """
    Wraps a queryset of products into a Schema.org ItemList for the product feed.
    """

    def to_representation(self, queryset):
        product_serializer = JsonLdProductSerializer()
        items = []
        for i, product in enumerate(queryset):
            item = {
                "@type": "ListItem",
                "position": i + 1,
                "item": product_serializer.to_representation(product),
            }
            items.append(item)

        return {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "RazorHub Product Catalog",
            "numberOfItems": len(items),
            "itemListElement": items,
        }
