from decimal import Decimal
from django.db.models import Count, Sum, F, Q, ExpressionWrapper, DecimalField
from products.models import Product
from intelligence.models import RevenueOpportunity, InventoryInsight
from orders.models import OrderItem

class RevenueOpportunityService:
    @classmethod
    def analyze_all_products(cls):
        """Run analysis on all active products to find revenue opportunities."""
        products = Product.objects.filter(is_active=True)
        opportunities = []

        for product in products:
            # 1. High Margin Upsell Opportunity
            if product.cost_price and product.price > product.cost_price:
                margin = product.price - product.cost_price
                margin_percent = margin / product.price
                
                if margin_percent > Decimal('0.4'):  # 40% margin
                    opp, _ = RevenueOpportunity.objects.update_or_create(
                        product=product,
                        opportunity_type='upsell',
                        defaults={
                            'score': margin_percent,
                            'expected_revenue_impact': margin,
                            'reason_codes': ['HIGH_MARGIN', f'MARGIN_{int(margin_percent*100)}PCT'],
                            'explanation': f'High margin product with {int(margin_percent*100)}% margin. Good candidate for upsell.'
                        }
                    )
                    opportunities.append(opp)

            # 2. Stock Clearance Opportunity
            if hasattr(product, 'inventory_insight'):
                insight = product.inventory_insight
                if insight.available > 0 and insight.velocity_per_day < Decimal('0.5') and insight.estimated_days_remaining and insight.estimated_days_remaining > 90:
                    opp, _ = RevenueOpportunity.objects.update_or_create(
                        product=product,
                        opportunity_type='stock_clearance',
                        defaults={
                            'score': Decimal('0.8'),
                            'expected_revenue_impact': product.price * insight.available,
                            'reason_codes': ['LOW_VELOCITY', 'HIGH_STOCK'],
                            'explanation': f'Slow moving inventory with {insight.estimated_days_remaining} days remaining. Consider discount.'
                        }
                    )
                    opportunities.append(opp)

        return opportunities

    @classmethod
    def generate_cross_sell_opportunities(cls):
        """Analyze frequent item pairs to generate cross-sell opportunities."""
        # This will be refined when ProductRelationship is fully populated
        pass
