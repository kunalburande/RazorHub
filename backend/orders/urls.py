from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, RazorpayWebhookView

router = DefaultRouter()
router.register("orders", OrderViewSet, basename="order")

urlpatterns = [
    path("payments/webhook/", RazorpayWebhookView.as_view(), name="razorpay-webhook"),
    path("", include(router.urls)),
]
