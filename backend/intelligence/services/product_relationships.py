from decimal import Decimal
from collections import defaultdict
from django.db.models import Count
from products.models import Product
from intelligence.models import ProductRelationship
from orders.models import OrderItem

class ProductRelationshipService:
    @classmethod
    def generate_frequently_bought_together(cls):
        """Generate frequently bought together relationships from OrderItems."""
        # Find orders with multiple items
        orders_with_items = OrderItem.objects.values('order_id').annotate(item_count=Count('id')).filter(item_count__gt=1)
        order_ids = [o['order_id'] for o in orders_with_items]
        
        # Get all items in these orders
        items = OrderItem.objects.filter(order_id__in=order_ids).select_related('product')
        
        # Group by order
        order_products = defaultdict(set)
        for item in items:
            order_products[item.order_id].add(item.product)
            
        # Count co-occurrences
        co_occurrences = defaultdict(int)
        for products in order_products.values():
            product_list = list(products)
            for i in range(len(product_list)):
                for j in range(i + 1, len(product_list)):
                    p1 = product_list[i]
                    p2 = product_list[j]
                    co_occurrences[(p1, p2)] += 1
                    co_occurrences[(p2, p1)] += 1
                    
        # Create relationships for co-occurrences > 2
        for (p1, p2), count in co_occurrences.items():
            if count >= 2:
                # Calculate simple confidence based on frequency
                confidence = min(Decimal('1.0'), Decimal(count) / Decimal('10.0'))
                
                # Only update if not merchant defined
                if not ProductRelationship.objects.filter(source_product=p1, target_product=p2, relationship_type='frequently_bought_with', merchant_defined=True).exists():
                    ProductRelationship.objects.update_or_create(
                        source_product=p1,
                        target_product=p2,
                        relationship_type='frequently_bought_with',
                        defaults={
                            'source': 'system_generated',
                            'confidence': confidence
                        }
                    )
