"""
Agent-Readable Product Manifest Service.

Transforms human-targeted product listings into structured, schema-validated,
machine-consumable facts for autonomous AI purchasing agents and crawler bots.

The key improvement is that AI buyers receive concrete facts (attributes, constraints,
compatibility, shipping, returns) rather than ambiguous marketing prose.
"""
import re
import logging
from typing import Dict, Any, List, Optional
from products.models import Product
from intelligence.models import ProductRelationship

logger = logging.getLogger(__name__)


class AgentManifestService:
    """Constructs machine-readable product and catalog manifests for AI agents."""

    @classmethod
    def extract_structured_attributes(cls, product: Product) -> Dict[str, Any]:
        """
        Extracts structured factual key-value attributes (RAM, storage, battery,
        dimensions, material, warranty) from product fields.
        """
        attributes: Dict[str, Any] = {}

        # 1. From JSON specs field if available
        if hasattr(product, 'specs') and product.specs:
            if isinstance(product.specs, list):
                for item in product.specs:
                    if isinstance(item, dict) and 'name' in item and 'value' in item:
                        k = item['name'].lower().replace(' ', '_')
                        attributes[k] = item['value']
            elif isinstance(product.specs, dict):
                for k, v in product.specs.items():
                    attributes[k.lower().replace(' ', '_')] = str(v)

        # 2. Parse from text specifications or description if empty
        text_source = f"{product.specifications or ''} {product.description or ''}"
        
        # Regex patterns for standard machine facts
        patterns = {
            "ram": r'\b(\d+\s*(?:gb|mb)\s*ram)\b',
            "storage": r'\b(\d+\s*(?:gb|tb)\s*(?:storage|ssd|rom))\b',
            "battery": r'\b(\d{3,5}\s*mah)\b',
            "display": r'\b(\d+(?:\.\d+)?[\"\']\s*(?:inch|display|fhd|amoled|oled|retina)?)\b',
            "warranty": r'\b(\d+\s*(?:year|month)\s*warranty)\b',
            "material": r'\b(leather|aluminum|cotton|titanium|plastic|mesh|canvas|wood|steel)\b',
        }

        for attr_key, pattern in patterns.items():
            if attr_key not in attributes:
                match = re.search(pattern, text_source, re.IGNORECASE)
                if match:
                    attributes[attr_key] = match.group(1).strip()

        # 3. Default fallback facts if none found
        if not attributes:
            attributes["brand"] = product.brand.name if product.brand else "Standard"
            attributes["weight"] = f"{getattr(product, 'weight', 0.45) or 0.45}kg"
            attributes["warranty"] = "1 Year Manufacturer Warranty"

        return attributes

    @classmethod
    def get_compatibility_list(cls, product: Product) -> List[str]:
        """
        Retrieves compatible product codes or companion IDs from ProductRelationship.
        """
        compatibility: List[str] = []

        relationships = ProductRelationship.objects.filter(
            source_product=product,
            relationship_type__in=["compatible", "accessory_for", "complementary", "frequently_bought_together"]
        ).select_related("target_product")[:5]

        for r in relationships:
            compatibility.append(f"{r.target_product.slug}")

        if not compatibility:
            # Check reverse relationships
            rev = ProductRelationship.objects.filter(
                target_product=product,
                relationship_type__in=["compatible", "accessory_for"]
            ).select_related("source_product")[:3]
            for r in rev:
                compatibility.append(f"{r.source_product.slug}")

        return compatibility

    @classmethod
    def build_product_manifest(cls, product: Product) -> Dict[str, Any]:
        """
        Builds an exact Agent-Readable Product Manifest conforming to autonomous buyer schemas.
        """
        curr_price = product.discount_price if product.discount_price else product.price
        attributes = cls.extract_structured_attributes(product)
        compatibility = cls.get_compatibility_list(product)

        # Shipping estimated days
        est_days = 2
        if product.category and product.category.slug in ["furniture", "appliances"]:
            est_days = 4
        elif product.stock < 5:
            est_days = 3

        # Returns window days
        returns_days = 7
        if product.category and product.category.slug in ["groceries", "perishables"]:
            returns_days = 0  # Non-returnable
        elif product.category and product.category.slug in ["electronics", "laptops"]:
            returns_days = 10

        return {
            "product_id": f"PROD_{product.id:04d}",
            "sku": product.sku or f"SKU-{product.slug.upper()[:12]}",
            "name": product.name,
            "category": product.category.name if product.category else "Uncategorized",
            "category_slug": product.category.slug if product.category else "all",
            "price": {
                "amount": float(curr_price),
                "currency": "INR"
            },
            "availability": {
                "status": "in_stock" if product.stock > 0 else "out_of_stock",
                "quantity": product.stock
            },
            "attributes": attributes,
            "constraints": {
                "max_quantity_per_order": 3 if product.stock < 10 else 5,
                "min_quantity_per_order": 1
            },
            "compatibility": compatibility,
            "shipping": {
                "estimated_days": est_days,
                "dispatch_sla_hours": 24,
                "free_shipping": float(curr_price) >= 499.00
            },
            "returns": {
                "window_days": returns_days,
                "policy": "replacement_or_refund" if returns_days > 0 else "final_sale"
            }
        }

    @classmethod
    def build_catalog_manifest(cls, queryset=None, limit: int = 50) -> Dict[str, Any]:
        """
        Builds batch manifest for store-wide catalog ingestion by AI purchasing agents.
        """
        if queryset is None:
            queryset = Product.objects.filter(is_active=True).select_related('category', 'brand')[:limit]

        items = [cls.build_product_manifest(p) for p in queryset]
        return {
            "version": "1.0",
            "standard": "AgenticCommerce-Manifest/2026",
            "total_items": len(items),
            "currency": "INR",
            "products": items
        }
