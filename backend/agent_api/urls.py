from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgentProductViewSet, AgentAvailabilityViewSet, AgentOfferViewSet,
    AgentCartViewSet, AgentCheckoutViewSet, AgentPolicyViewSet,
    AgentCatalogViewSet,
)

router = DefaultRouter()
router.register(r'products', AgentProductViewSet, basename='agent-product')
router.register(r'availability', AgentAvailabilityViewSet, basename='agent-availability')
router.register(r'offers', AgentOfferViewSet, basename='agent-offer')
router.register(r'cart', AgentCartViewSet, basename='agent-cart')
router.register(r'checkout', AgentCheckoutViewSet, basename='agent-checkout')
router.register(r'policies', AgentPolicyViewSet, basename='agent-policy')
router.register(r'catalog', AgentCatalogViewSet, basename='agent-catalog')

urlpatterns = [
    path('', include(router.urls)),
]

