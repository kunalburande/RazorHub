from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MerchantConfigViewSet, CampaignViewSet, ProductRelationshipViewSet,
    AuditEventViewSet, RecoveryTaskViewSet, CompileBundleView,
    ReadinessScoreView, CatalogManifestView, PolicyView, PolicySimulateView,
    WhyOfferExplainabilityView, WhyTransactionAllowedView, NegotiationView,
    InventoryLifecycleValidateView, CampaignOrchestrateView,
    OutcomeMetricsView, OfferEconomicsCompareView, CustomerFatigueEvaluateView,
    CompetencePersonalizeFrameView, WhyNotThisExplainabilityView,
    ConversationalCheckoutView, CatalogFeedView, CatalogReconcileView,
    DunningSimulateView, RtoRiskEvaluateView, PayoutForecastView,
    AgentQuoteView, AgentPurchaseView, VoiceCommerceTurnView
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
    path('catalog/feed/', CatalogFeedView.as_view(), name='catalog-feed'),
    path('catalog/reconcile/', CatalogReconcileView.as_view(), name='catalog-reconcile'),
    path('dunning/simulate/', DunningSimulateView.as_view(), name='dunning-simulate'),
    path('rto/evaluate/', RtoRiskEvaluateView.as_view(), name='rto-evaluate'),
    path('payout/forecast/', PayoutForecastView.as_view(), name='payout-forecast'),
    path('agent/quote/', AgentQuoteView.as_view(), name='agent-quote'),
    path('agent/purchase/', AgentPurchaseView.as_view(), name='agent-purchase'),
    path('voice/process-turn/', VoiceCommerceTurnView.as_view(), name='voice-process-turn'),
    path('policy/', PolicyView.as_view(), name='policy'),
    path('policy/simulate/', PolicySimulateView.as_view(), name='policy-simulate'),
    path('explainability/why-offer/', WhyOfferExplainabilityView.as_view(), name='why-offer'),
    path('explainability/why-transaction/', WhyTransactionAllowedView.as_view(), name='why-transaction'),
    path('explainability/why-not-this/', WhyNotThisExplainabilityView.as_view(), name='why-not-this'),
    path('negotiate/', NegotiationView.as_view(), name='negotiate'),
    path('inventory/validate-pipeline/', InventoryLifecycleValidateView.as_view(), name='inventory-validate-pipeline'),
    path('campaigns/orchestrate/', CampaignOrchestrateView.as_view(), name='campaign-orchestrate'),
    path('outcomes/metrics/', OutcomeMetricsView.as_view(), name='outcome-metrics'),
    path('outcomes/compare-offers/', OfferEconomicsCompareView.as_view(), name='offer-economics-compare'),
    path('fatigue/evaluate/', CustomerFatigueEvaluateView.as_view(), name='customer-fatigue-evaluate'),
    path('personalization/frame/', CompetencePersonalizeFrameView.as_view(), name='competence-personalize-frame'),
    path('checkout/conversational/', ConversationalCheckoutView.as_view(), name='conversational-checkout'),
    path('', include(router.urls)),
]
