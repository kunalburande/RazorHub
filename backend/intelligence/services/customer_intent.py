from decimal import Decimal
from intelligence.models import CustomerIntent
from orders.models import Order

class CustomerIntentService:
    @classmethod
    def infer_intent(cls, user, cart_items=None):
        """Infer customer intent based on cart and order history."""
        if not user or not user.is_authenticated:
            return None
            
        # Basic deterministic intent inference
        intent_type = 'browsing'
        confidence = Decimal('0.5')
        budget_min = Decimal('0.0')
        budget_max = Decimal('1000.0')
        
        # Check order history
        recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
        if recent_orders.exists():
            avg_order_value = sum(order.total_price for order in recent_orders) / len(recent_orders)
            budget_max = avg_order_value * Decimal('1.5')
            budget_min = avg_order_value * Decimal('0.5')
            
        if cart_items and len(cart_items) > 0:
            intent_type = 'purchasing'
            confidence = Decimal('0.9')
            cart_total = sum(item.product.current_price * item.quantity for item in cart_items)
            if cart_total > budget_max:
                budget_max = cart_total * Decimal('1.2')
                
        intent, _ = CustomerIntent.objects.update_or_create(
            user=user,
            defaults={
                'intent': intent_type,
                'confidence': confidence,
                'budget_min': budget_min,
                'budget_max': budget_max,
                'preferences': {},
                'constraints': []
            }
        )
        
        return intent
