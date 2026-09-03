from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MerchantConfigViewSet, CampaignViewSet, ProductRelationshipViewSet,
    AuditEventViewSet, RecoveryTaskViewSet, CompileBundleView,
    ReadinessScoreView, CatalogManifestView
)

router = DefaultRouter()
router.register(r'config', MerchantConfigViewSet, basename='config')
router.register(r'campaigns', CampaignViewSet, basename='campaign')
router.register(r'relationships', ProductRelationshipViewSet, basename='relationship')
router.register(r'audit', AuditEventViewSet, basename='audit')
router.register(r'recovery', RecoveryTaskViewSet, basename='recovery')

urlpatterns = [
    path('compile-bundle/', CompileBundleView.as_view(), name='compile-bundle'),
    path('readiness-score/', ReadinessScoreView.as_view(), name='readiness-score'),
    path('catalog-manifest/', CatalogManifestView.as_view(), name='catalog-manifest'),
    path('', include(router.urls)),
]
