from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, RazorpayWebhookView, CartView, RefundViewSet, PayoutViewSet, SettlementViewSet

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")
router.register("refunds", RefundViewSet, basename="refund")
router.register("payouts", PayoutViewSet, basename="payout")
router.register("settlements", SettlementViewSet, basename="settlement")

urlpatterns = [
    path("cart/", CartView.as_view(), name="cart"),
    path("payments/webhook/", RazorpayWebhookView.as_view(), name="razorpay-webhook"),
    path("", include(router.urls)),
]
