from rest_framework import viewsets, permissions
from .models import MerchantConfig, Campaign, ProductRelationship, AuditEvent, RecoveryTask
from rest_framework import serializers

class MerchantConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = MerchantConfig
        fields = '__all__'

class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'

class ProductRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductRelationship
        fields = '__all__'

class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = '__all__'

class RecoveryTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecoveryTask
        fields = '__all__'

class IsSellerOrAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.effective_role in ['seller', 'admin'])

class MerchantConfigViewSet(viewsets.ModelViewSet):
    queryset = MerchantConfig.objects.all().order_by('id')
    serializer_class = MerchantConfigSerializer
    permission_classes = [IsSellerOrAdminPermission]
    pagination_class = None

    def get_object(self):
        return MerchantConfig.get_solo()

class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all().order_by('-id')
    serializer_class = CampaignSerializer
    permission_classes = [IsSellerOrAdminPermission]

class ProductRelationshipViewSet(viewsets.ModelViewSet):
    queryset = ProductRelationship.objects.all().order_by('-id')
    serializer_class = ProductRelationshipSerializer
    permission_classes = [IsSellerOrAdminPermission]

class AuditEventViewSet(viewsets.ModelViewSet):
    queryset = AuditEvent.objects.all().order_by('-created_at')
    serializer_class = AuditEventSerializer
    permission_classes = [IsSellerOrAdminPermission]
    pagination_class = None

class RecoveryTaskViewSet(viewsets.ModelViewSet):
    queryset = RecoveryTask.objects.all().order_by('-created_at')
    serializer_class = RecoveryTaskSerializer
    permission_classes = [IsSellerOrAdminPermission]
    pagination_class = None


# ── Unified Agentic Chat Endpoint ─────────────────────────────────────
import logging
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


class AgenticChatView(APIView):
    """
    Unified AI chat endpoint for both RazorHub and Dokkany.
    Routes user messages through the multi-agent orchestration engine.

    POST /api/ai/chat/
    Body: {
        "messages": [{"role": "user"|"assistant", "content": "..."}],
        "context": { "cart": {...}, "catalog": [...], "platform": "razorhub"|"dokkany", ... }
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        messages = request.data.get("messages", [])
        context = request.data.get("context", {})

        if not messages:
            return Response({"error": "No messages provided"}, status=400)

        # Normalize message format
        normalized = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "") or msg.get("text", "")
            if role in ("user", "assistant", "model"):
                normalized.append({"role": role, "content": content})

        if not normalized:
            return Response({"error": "No valid messages"}, status=400)

        platform = context.get("platform", "razorhub")

        try:
            from intelligence.agents.orchestrator import OrchestratorAgent
            from intelligence.agents.search_agent import SearchAgent
            from intelligence.agents.shopping_agent import ShoppingAgent
            from intelligence.agents.checkout_agent import CheckoutAgent
            from intelligence.agents.upsell_agent import UpsellAgent
            from intelligence.agents.campaign_agent import CampaignAgent
            from intelligence.agents.order_agent import OrderAgent
            from intelligence.agents.response_agent import ResponseAgent
            from intelligence.agents.seller_agent import SellerAgent

            user = request.user if request.user.is_authenticated else None
            user_id = str(user.id) if user else context.get("user_id", "anonymous")

            # Enrich context with auth/user metadata
            enriched_context = {
                **context,
                "platform": platform,
                "user": user,
                "user_id": user_id,
            }

            # Step 1: Route via Orchestrator or SellerAgent
            if platform in ["dokkany", "razorhub_seller"]:
                orchestrator = OrchestratorAgent()
                routing = orchestrator.execute(normalized, {"platform": "razorhub_seller"})
                agent_name = routing.get("agent", "seller")
                
                if agent_name == "campaign":
                    agent = CampaignAgent()
                else:
                    agent = SellerAgent()
                    agent_name = "seller"
                result = agent.execute(normalized, enriched_context)
            else:
                from intelligence.services.checkout_state import get_session, IDLE, COMPLETED
                checkout_sess = get_session(user_id, context.get("session_id"))
                is_active_checkout = checkout_sess["state"] not in (IDLE, COMPLETED)


                orchestrator = OrchestratorAgent()
                routing = orchestrator.execute(normalized, {"platform": platform})
                agent_name = routing.get("agent", "general")
                refined_query = routing.get("refined_query", "")

                # Conversational checkout continuity: if buyer is providing address/confirming, stay in checkout
                if is_active_checkout and agent_name in ("general", "search", "order"):
                    last_msg_lower = normalized[-1]["content"].lower()
                    if not any(w in last_msg_lower for w in ["search for", "find me", "show products", "catalog", "browse"]):
                        agent_name = "checkout"

                logger.info(f"[AgenticChat] Routed to '{agent_name}': {routing.get('reasoning', '')}")

                enriched_context["refined_query"] = refined_query
                enriched_context["checkout_state"] = checkout_sess["state"]

                if agent_name == "search":
                    agent = SearchAgent()
                elif agent_name == "shopping":
                    agent = ShoppingAgent()
                elif agent_name == "checkout":
                    agent = CheckoutAgent()
                elif agent_name == "upsell":
                    agent = UpsellAgent()
                elif agent_name == "campaign":
                    agent = CampaignAgent()
                elif agent_name == "order":
                    agent = OrderAgent()
                else:
                    agent = ResponseAgent()

                result = agent.execute(normalized, enriched_context)

            return Response({
                "content": result.get("content", ""),
                "agent": agent_name,
                "toolCalls": result.get("toolCalls"),
                "productCards": result.get("productCards"),
                "chartData": result.get("chartData"),
                "checkout_state": result.get("checkout_state"),
                "suggestedFollowups": result.get("suggestedFollowups"),
            })

        except Exception as e:
            logger.error(f"[AgenticChat] Error: {e}\n{traceback.format_exc()}")
            return Response({
                "content": "I'm having trouble processing your request right now. Please try again in a moment.",
                "agent": "error",
                "error": str(e),
            }, status=500)


class CompileBundleView(APIView):
    """
    POST /api/intelligence/compile-bundle/
    Accepts: { query?: str, product_slug?: str, product_id?: int, budget_limit?: float }
    Returns multi-tier compiled bundle with optimal budget-constrained selection and explainability.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from decimal import Decimal
        from products.models import Product
        from products.serializers import ProductListSerializer
        from intelligence.services.bundle_compiler import BundleCompilerService

        query = request.data.get("query", "")
        product_slug = request.data.get("product_slug")
        product_id = request.data.get("product_id")
        budget_limit = request.data.get("budget_limit")

        primary = None
        if product_slug:
            primary = Product.objects.filter(slug=product_slug, is_active=True).first()
        elif product_id:
            primary = Product.objects.filter(id=product_id, is_active=True).first()

        if not primary and query:
            parsed = BundleCompilerService.parse_intent_and_budget(query)
            if not budget_limit and parsed.get("budget_limit"):
                budget_limit = parsed["budget_limit"]

            cat_slug = parsed.get("category_slug")
            qs = Product.objects.filter(is_active=True)
            if cat_slug:
                qs = qs.filter(category__slug=cat_slug)
            if budget_limit:
                qs = qs.filter(price__lte=Decimal(str(budget_limit)))

            primary = qs.order_by('-price', '-rating').first()
            if not primary:
                primary = Product.objects.filter(is_active=True).order_by('-price').first()

        if not primary:
            return Response({"error": "No matching primary product found for bundle compilation."}, status=404)

        limit_dec = Decimal(str(budget_limit)) if budget_limit else None
        bundle_data = BundleCompilerService.compile_bundle(primary, budget_limit=limit_dec)

        def serialize_tier(t):
            return {
                "tier_name": t["tier_name"],
                "tier_key": t["tier_key"],
                "primary": ProductListSerializer(t["primary"]).data,
                "accessories": ProductListSerializer(t["accessories"], many=True).data,
                "raw_total": t["raw_total"],
                "bundle_price": t["bundle_price"],
                "discount_amount": t["discount_amount"],
                "savings_headroom": t["savings_headroom"],
                "is_within_budget": t["is_within_budget"],
                "exceeded_by": t.get("exceeded_by", 0.0),
                "coverage": t["coverage"],
            }

        return Response({
            "recommended_tier": bundle_data["recommended_tier"],
            "explanation": bundle_data["explanation"],
            "budget_limit": bundle_data["budget_limit"],
            "primary_product": ProductListSerializer(bundle_data["primary_product"]).data,
            "chosen_bundle": serialize_tier(bundle_data["chosen_bundle"]),
            "tiers": {
                k: serialize_tier(v) for k, v in bundle_data["tiers"].items()
            }
        })


class ReadinessScoreView(APIView):
    """
    GET /api/intelligence/readiness-score/
    Computes and returns the 8-pillar AI Commerce Readiness Score (0-100)
    and explainable diagnostics for the seller's store.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from intelligence.services.agent_compatibility import AgentBuyerCompatibilityService
        from sellers.models import SellerProfile

        store = None
        if request.user.is_authenticated:
            try:
                seller_profile = SellerProfile.objects.filter(user=request.user).first()
                if seller_profile and hasattr(seller_profile, 'store'):
                    store = seller_profile.store
            except Exception:
                pass

        readiness = AgentBuyerCompatibilityService.evaluate_store_readiness(store=store)
        return Response(readiness)


class CatalogManifestView(APIView):
    """
    GET /api/intelligence/catalog-manifest/
    Returns batch agent-readable catalog manifest for autonomous AI buyers and crawlers.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from intelligence.services.agent_manifest import AgentManifestService
        limit = int(request.query_params.get("limit", 50))
        category_slug = request.query_params.get("category")
        qs = Product.objects.filter(is_active=True).select_related('category', 'brand')
        if category_slug:
            qs = qs.filter(category__slug=category_slug)
        manifest = AgentManifestService.build_catalog_manifest(qs[:limit], limit=limit)
        return Response(manifest)

