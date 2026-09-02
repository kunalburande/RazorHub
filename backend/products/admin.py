from django.contrib import admin
from .models import Category, Brand, Inventory, Product, ProductImage, Review, ProductAttribute

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class ProductAttributeInline(admin.TabularInline):
    """Inline editor for structured AI-filterable product attributes."""
    model = ProductAttribute
    extra = 1
    classes = ['collapse']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'order']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'store', 'category', 'brand', 'price', 'discount_price', 'cost_price', 'margin_pct', 'stock', 'is_featured', 'is_active']
    list_filter = ['store', 'category', 'brand', 'is_featured', 'is_active', 'currency']
    search_fields = ['name', 'description', 'store__name', 'sku']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, ProductAttributeInline]
    readonly_fields = ['price_paise', 'cost_paise', 'margin_pct']
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'store', 'category', 'brand', 'description', 'specifications')
        }),
        ('Pricing', {
            'fields': ('price', 'discount_price', 'cost_price', 'currency', 'price_paise', 'cost_paise', 'margin_pct')
        }),
        ('Inventory & Display', {
            'fields': ('stock', 'sku', 'colors', 'tag', 'is_featured', 'is_active', 'rating')
        }),
        ('Delivery', {
            'fields': ('delivery_time_estimate', 'base_delivery_fee')
        }),
        ('AI / RazorHubSeller', {
            'classes': ('collapse',),
            'fields': ('ai_metadata', 'embedding'),
            'description': 'AI-commerce fields ported from RazorHubSeller. Embedding is auto-generated.'
        }),
    )


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ["product", "sku", "quantity", "reserved_quantity", "low_stock_threshold", "location", "updated_at"]
    search_fields = ["product__name", "sku", "location"]
    list_filter = ["location"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "name", "rating", "is_verified_purchase", "created_at"]
    list_filter = ["rating", "is_verified_purchase", "created_at"]
    search_fields = ["product__name", "name", "title", "comment"]


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ["product", "key", "value"]
    list_filter = ["key"]
    search_fields = ["product__name", "key", "value"]
