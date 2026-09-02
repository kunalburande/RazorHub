from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MerchantConfigViewSet, CampaignViewSet, ProductRelationshipViewSet, AuditEventViewSet, RecoveryTaskViewSet

router = DefaultRouter()
router.register(r'config', MerchantConfigViewSet, basename='config')
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'relationships', ProductRelationshipViewSet, basename='relationship')
router.register(r'audit', AuditEventViewSet, basename='audit')
router.register(r'recovery', RecoveryTaskViewSet, basename='recovery')

urlpatterns = [
    path('', include(router.urls)),
]
