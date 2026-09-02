from decimal import Decimal
from django.utils import timezone
from products.models import Product
from intelligence.models import Offer, MerchantConfig, ProductRelationship

class OfferOptimizerService:
    @classmethod
    def generate_offers_for_cart(cls, cart_items, user_intent=None):
        """Generate optimized offers for a cart."""
        config = MerchantConfig.get_solo()
        if not config.ai_recommendations_enabled:
            return []
            
        offers = []
        product_ids = [item.product_id for item in cart_items]
        
        for item in cart_items:
            # Upsell/Cross-sell based on relationships
            relationships = ProductRelationship.objects.filter(
                source_product=item.product
            ).exclude(
                target_product_id__in=product_ids
            ).select_related('target_product')
            
            for rel in relationships:
                # Basic offer creation
                discount = Decimal('0.00')
                target = rel.target_product
                
                # Dynamic discount based on config and relationship confidence
                if config.max_discount_percent > 0:
                    discount_pct = min(Decimal('10.00'), config.max_discount_percent)
                    if rel.confidence > Decimal('0.8'):
                        discount_pct = min(Decimal('15.00'), config.max_discount_percent)
                        
                    discount = target.current_price * (discount_pct / Decimal('100.0'))
                    discount = discount.quantize(Decimal('0.01'))
                    
                offer_price = target.current_price - discount
                
                offer = Offer.objects.create(
                    offer_id=f"OFFER-{target.id}-{timezone.now().timestamp()}",
                    offer_type=rel.relationship_type,
                    price=offer_price,
                    original_price=target.current_price,
                    discount=discount,
                    confidence=rel.confidence,
                    reason_codes=[f"RELATIONSHIP_{rel.relationship_type.upper()}"],
                    expires_at=timezone.now() + timezone.timedelta(hours=1)
                )
                offer.products.add(target)
                offers.append(offer)
                
        return offers
