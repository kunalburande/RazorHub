from django.contrib import admin
from .models import Order, OrderItem, Payment, Refund, Payout, Settlement


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "status",
        "payment_method",
        "delivery_eta",
        "promo_code",
        "total_price",
        "created_at",
    ]
    list_filter = ["status", "payment_method", "delivery_eta"]
    search_fields = ["user__email", "shipping_address", "promo_code"]
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "method", "status", "amount", "provider_reference", "created_at"]
    list_filter = ["method", "status"]
    search_fields = ["provider_reference", "order__id", "order__user__email"]


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ["refund_id", "order", "amount", "reason", "status", "created_at"]
    list_filter = ["status", "reason"]
    search_fields = ["refund_id", "order__id", "order__user__email"]


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ["payout_id", "recipient_name", "store", "amount", "mode", "status", "created_at"]
    list_filter = ["status", "mode", "store"]
    search_fields = ["payout_id", "recipient_name", "utr"]


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ["settlement_id", "store", "amount", "net_amount", "status", "is_delayed", "settlement_date"]
    list_filter = ["status", "is_delayed", "store"]
    search_fields = ["settlement_id", "utr"]
