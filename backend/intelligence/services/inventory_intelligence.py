from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from products.models import Product
from intelligence.models import InventoryInsight
from orders.models import OrderItem

class InventoryIntelligenceService:
    @classmethod
    def analyze_inventory(cls):
        """Analyze all product inventory to determine velocity and risk."""
        products = Product.objects.filter(is_active=True).select_related('inventory')
        
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        for product in products:
            if not hasattr(product, 'inventory'):
                continue
                
            available = product.inventory.available_quantity
            
            # Calculate velocity (items sold per day over last 30 days)
            recent_sales = OrderItem.objects.filter(
                product=product, 
                order__created_at__gte=thirty_days_ago,
                order__status__in=['pending', 'processing', 'shipped', 'delivered']
            ).aggregate(total=Sum('quantity'))['total'] or 0
            
            velocity = Decimal(recent_sales) / Decimal('30.0')
            
            estimated_days = None
            risk_level = 'low'
            
            if velocity > 0:
                estimated_days = int(Decimal(available) / velocity)
                
                if estimated_days < 3:
                    risk_level = 'high'
                elif estimated_days < 7:
                    risk_level = 'medium'
            elif available == 0:
                estimated_days = 0
                risk_level = 'high'
                
            InventoryInsight.objects.update_or_create(
                product=product,
                defaults={
                    'available': available,
                    'velocity_per_day': velocity,
                    'estimated_days_remaining': estimated_days,
                    'risk_level': risk_level
                }
            )
