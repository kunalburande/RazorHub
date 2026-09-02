from django.contrib import admin
from .models import (
    ProductRelationship,
    RevenueOpportunity,
    CustomerIntent,
    InventoryInsight,
    Offer,
    OfferDecision,
    Campaign,
    MerchantConfig
)

@admin.register(MerchantConfig)
class MerchantConfigAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'ai_recommendations_enabled', 'ai_checkout_enabled', 'max_ai_order_value']

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign_type', 'discount_type', 'discount_value', 'active', 'start_date', 'end_date']
    list_filter = ['active', 'campaign_type']
    search_fields = ['name']

@admin.register(ProductRelationship)
class ProductRelationshipAdmin(admin.ModelAdmin):
    list_display = ['source_product', 'relationship_type', 'target_product', 'confidence', 'merchant_defined']
    list_filter = ['relationship_type', 'merchant_defined']
    search_fields = ['source_product__name', 'target_product__name']

@admin.register(RevenueOpportunity)
class RevenueOpportunityAdmin(admin.ModelAdmin):
    list_display = ['product', 'opportunity_type', 'score', 'expected_revenue_impact']
    list_filter = ['opportunity_type']

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ['offer_id', 'offer_type', 'price', 'discount', 'status', 'expires_at']
    list_filter = ['status', 'offer_type']
    search_fields = ['offer_id']

admin.site.register(CustomerIntent)
admin.site.register(InventoryInsight)
admin.site.register(OfferDecision)
