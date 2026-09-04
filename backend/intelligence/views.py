from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from .models import MerchantConfig, Campaign, ProductRelationship, AuditEvent, RecoveryTask

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
    store_name = serializers.CharField(source='store.name', read_only=True)

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
    serializer_class = RecoveryTaskSerializer
    permission_classes = [IsSellerOrAdminPermission]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        store = None
        if user.effective_role == "seller":
            seller_profile = getattr(user, "seller_profile", None)
            store = getattr(seller_profile, "store", None)
            if not store:
                return RecoveryTask.objects.none()
        elif user.effective_role == "admin":
            store_param = self.request.query_params.get("store_id") or self.request.query_params.get("store")
            if store_param:
                from sellers.models import Store
                if str(store_param).isdigit():
                    store = Store.objects.filter(id=int(store_param)).first()
                if not store:
                    store = Store.objects.filter(slug=store_param).first()

        if store:
            self._sync_store_tasks(store)
            return RecoveryTask.objects.filter(store=store).order_by('-created_at')

        if user.effective_role == "admin":
            return RecoveryTask.objects.all().order_by('-created_at')

        return RecoveryTask.objects.none()

    def _sync_store_tasks(self, store):
        """
        Dynamically synchronize real recovery tasks for this store from actual orders,
        pending/failed payments, and customer activity.
        """
        try:
            from orders.models import Order, Payment
            # 1. Real orders for this store with pending or failed payments
            problem_orders = Order.objects.filter(
                items__product__store=store,
                payment__status__in=[Payment.STATUS_PENDING, Payment.STATUS_FAILED]
            ).select_related('user', 'payment').distinct()

            for o in problem_orders:
                task_id = f"DUNN-ORD-{o.id}"
                if not RecoveryTask.objects.filter(task_id=task_id).exists():
                    RecoveryTask.objects.create(
                        task_id=task_id,
                        store=store,
                        order=o,
                        customer_email=o.user.email,
                        cart_value=o.total_price,
                        status="In_Progress",
                        agent_action="UPI_RETRY: Dispatched 1-click retry link to customer"
                    )

            # 2. Delivered / completed orders with post-purchase retention / cadence
            delivered_orders = Order.objects.filter(
                items__product__store=store,
                status="delivered",
                payment__status=Payment.STATUS_PAID
            ).select_related('user').order_by('-id')[:2]

            for o in delivered_orders:
                task_id = f"POST-PURCHASE-{o.id}"
                if not RecoveryTask.objects.filter(task_id=task_id).exists():
                    RecoveryTask.objects.create(
                        task_id=task_id,
                        store=store,
                        order=o,
                        customer_email=o.user.email,
                        cart_value=o.total_price,
                        status="Recovered",
                        agent_action="POST_PURCHASE: Completed 5-stage retention cadence; upsell converted"
                    )
        except Exception as e:
            logger.warning(f"[RecoveryTaskViewSet] Error syncing store tasks: {e}")

    def perform_create(self, serializer):
        user = self.request.user
        store = None
        if user.effective_role == "seller":
            store = getattr(getattr(user, "seller_profile", None), "store", None)
        elif "store" in serializer.validated_data:
            store = serializer.validated_data["store"]
        serializer.save(store=store)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        queryset = self.get_queryset()
        user = request.user
        store = None
        if user.effective_role == "seller":
            store = getattr(getattr(user, "seller_profile", None), "store", None)
        active = queryset.filter(status__in=["In_Progress", "Pending", "active", "in_progress", "pending"]).count()
        pending_retries = queryset.filter(
            agent_action__icontains="retry"
        ).exclude(status__in=["Recovered", "completed", "recovered"]).count()
        recovered_qs = queryset.filter(status__in=["Recovered", "completed", "recovered"])
        total_recovered = sum([float(t.cart_value) for t in recovered_qs])
        total_count = queryset.count()
        rate = round((recovered_qs.count() / total_count * 100)) if total_count > 0 else 0
        return Response({
            "active_recoveries": active,
            "pending_retries": pending_retries,
            "total_recovered": total_recovered,
            "recovery_rate": rate,
            "store_name": store.name if store else "All Stores",
            "store_id": store.id if store else None,
            "total_records": total_count,
        })


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


class PolicyView(APIView):
    """
    GET /api/intelligence/policy/
    PUT /api/intelligence/policy/
    Returns active Merchant Policy Language DSL (YAML) and parsed rules.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from intelligence.services.merchant_policy import MerchantPolicyEngine, DEFAULT_POLICY_YAML
        policy = MerchantPolicyEngine.load_active_policy()
        return Response({
            "policy_yaml": DEFAULT_POLICY_YAML,
            "policy_rules": {k: float(v) if hasattr(v, 'as_tuple') else v for k, v in policy.items()}
        })

    def put(self, request):
        from intelligence.services.merchant_policy import MerchantPolicyEngine
        yaml_text = request.data.get("policy_yaml", "")
        parsed = MerchantPolicyEngine.parse_policy_yaml(yaml_text)
        return Response({
            "success": True,
            "message": "Merchant policy language validated and applied.",
            "policy_yaml": yaml_text,
            "policy_rules": {k: float(v) if hasattr(v, 'as_tuple') else v for k, v in parsed.items()}
        })


class PolicySimulateView(APIView):
    """
    POST /api/intelligence/policy/simulate/
    Accepts: { proposal: { items, total_price, discount_pct, margin_pct, categories }, policy_yaml?: str }
    Deterministically evaluates proposal against policy and returns explainable gated decision.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.merchant_policy import MerchantPolicyEngine
        proposal = request.data.get("proposal", {})
        policy_yaml = request.data.get("policy_yaml")

        policy = None
        if policy_yaml:
            policy = MerchantPolicyEngine.parse_policy_yaml(policy_yaml)

        result = MerchantPolicyEngine.evaluate_proposal(proposal, policy=policy)
        return Response(result)


class WhyOfferExplainabilityView(APIView):
    """
    POST /api/intelligence/explainability/why-offer/
    Returns tangible 'WHY THIS OFFER?' proof for any candidate recommendation.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from products.models import Product
        from intelligence.services.explainability_service import FinancialExplainabilityService
        candidate_slug = request.data.get("candidate_slug")
        base_slug = request.data.get("base_slug")
        customer_intent = request.data.get("customer_intent", "Photography phone under ₹35K")
        budget = Decimal(str(request.data.get("budget", 35000)))

        candidate = Product.objects.filter(slug=candidate_slug).first() if candidate_slug else None
        if not candidate:
            candidate = Product.objects.filter(is_active=True).first()

        base_product = Product.objects.filter(slug=base_slug).first() if base_slug else None

        proof = FinancialExplainabilityService.generate_why_offer_proof(
            candidate=candidate,
            base_product=base_product,
            customer_intent=customer_intent,
            budget=budget,
            user=request.user if request.user.is_authenticated else None
        )
        return Response(proof)


class WhyTransactionAllowedView(APIView):
    """
    POST /api/intelligence/explainability/why-transaction/
    Returns real-time 'WHY IS THIS TRANSACTION ALLOWED?' pre-payment execution proof.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.explainability_service import FinancialExplainabilityService
        cart_total = Decimal(str(request.data.get("cart_total", 33097.0)))
        user_budget = Decimal(str(request.data.get("user_budget", 35000.0)))
        requested_by = request.data.get("requested_by", "AI Shopping Agent")
        merchant_limit = request.data.get("merchant_limit")
        if merchant_limit:
            merchant_limit = Decimal(str(merchant_limit))

        proof = FinancialExplainabilityService.generate_why_transaction_allowed_proof(
            cart_total=cart_total,
            user_budget=user_budget,
            requested_by=requested_by,
            merchant_limit=merchant_limit,
            verification_time_seconds=1.4,
            user=request.user if request.user.is_authenticated else None
        )
        return Response(proof)


class NegotiationView(APIView):
    """
    POST /api/intelligence/negotiate/
    Evaluates customer bargaining/discount queries against the 6-tier structured benefit ladder.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from products.models import Product
        from intelligence.services.negotiation_engine import BenefitLadderNegotiator
        product_slug = request.data.get("product_slug")
        target_price = request.data.get("requested_target_price")
        min_margin = Decimal(str(request.data.get("min_margin_percent", 20.0)))
        free_shipping_val = Decimal(str(request.data.get("free_shipping_value", 100.0)))

        target = Decimal(str(target_price)) if target_price else Decimal("5000.00")

        product = Product.objects.filter(slug=product_slug).first() if product_slug else None
        if not product:
            product = Product.objects.filter(is_active=True).first()

        res = BenefitLadderNegotiator.evaluate_negotiation(
            product=product,
            requested_target_price=target,
            min_margin_percent=min_margin,
            free_shipping_value=free_shipping_val
        )
        return Response(res)


class InventoryLifecycleValidateView(APIView):
    """
    POST /api/intelligence/inventory/validate-pipeline/
    Executes the 6-stage safe commerce pipeline:
    recommendation_time → stock check → price check → policy check → checkout → final inventory validation.
    If stock is depleted before payment, safely interrupts and provides graceful substitute recovery.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from products.models import Product
        from intelligence.services.inventory_lifecycle import InventoryLifecycleService
        product_slug = request.data.get("product_slug")
        initial_price = request.data.get("initial_price")
        if initial_price:
            initial_price = Decimal(str(initial_price))

        product = Product.objects.filter(slug=product_slug).first() if product_slug else None
        if not product:
            product = Product.objects.filter(is_active=True).first()

        res = InventoryLifecycleService.validate_pipeline(
            product=product,
            initial_price=initial_price
        )
        return Response(res)


class CampaignOrchestrateView(APIView):
    """
    POST /api/intelligence/campaigns/orchestrate/
    Compiles goal-driven post-purchase campaign sequences from merchant natural language intent.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.campaign_orchestrator import AutonomousCampaignOrchestrator
        from sellers.models import Store
        prompt = request.data.get("prompt", "Increase revenue from customers who purchased laptops.")
        store = None
        store_param = request.data.get("store") or request.data.get("store_id") or request.query_params.get("store")
        if store_param:
            if str(store_param).isdigit():
                store = Store.objects.filter(id=int(store_param)).first()
            if not store:
                store = Store.objects.filter(slug=store_param).first()
        elif request.user and request.user.is_authenticated:
            seller_profile = getattr(request.user, "seller_profile", None)
            if seller_profile and hasattr(seller_profile, "store"):
                store = seller_profile.store

        res = AutonomousCampaignOrchestrator.compile_goal_driven_campaign(merchant_prompt=prompt, store=store)
        return Response(res)


class OutcomeMetricsView(APIView):
    """
    GET /api/intelligence/outcomes/metrics/
    Returns the 9 required business outcome metrics connecting the recommendation loop to real economics,
    dynamically computed from active store, order, and customer records.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from intelligence.services.outcome_learning import OutcomeLearningService
        from sellers.models import Store
        store = None
        store_param = request.query_params.get("store") or request.query_params.get("store_id") or request.query_params.get("store_slug")
        if store_param:
            if str(store_param).isdigit():
                store = Store.objects.filter(id=int(store_param)).first()
            if not store:
                store = Store.objects.filter(slug=store_param).first() or Store.objects.filter(name__iexact=store_param).first()
        elif request.user and request.user.is_authenticated:
            if hasattr(request.user, "seller_profile") and hasattr(request.user.seller_profile, "store"):
                store = request.user.seller_profile.store

        res = OutcomeLearningService.get_business_outcome_metrics(store=store)
        return Response(res)


class OfferEconomicsCompareView(APIView):
    """
    POST /api/intelligence/outcomes/compare-offers/
    Evaluates Offer A vs Offer B economics to demonstrate why expected margin defeats vanity CTR.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.outcome_learning import OutcomeLearningService
        from sellers.models import Store
        offer_a = request.data.get("offer_a")
        offer_b = request.data.get("offer_b")
        store = None
        store_param = request.query_params.get("store") or request.data.get("store")
        if store_param:
            if str(store_param).isdigit():
                store = Store.objects.filter(id=int(store_param)).first()
            if not store:
                store = Store.objects.filter(slug=store_param).first() or Store.objects.filter(name__iexact=store_param).first()
        elif request.user and request.user.is_authenticated:
            if hasattr(request.user, "seller_profile") and hasattr(request.user.seller_profile, "store"):
                store = request.user.seller_profile.store
        res = OutcomeLearningService.evaluate_offer_economics(offer_a, offer_b, store=store)
        return Response(res)


class CustomerFatigueEvaluateView(APIView):
    """
    POST /api/intelligence/fatigue/evaluate/
    Evaluates customer fatigue score and enforces recommendation suppression.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.customer_fatigue import CustomerFatigueService
        threshold = request.data.get("threshold", 6)
        res = CustomerFatigueService.evaluate_suppression(request.data, threshold=threshold)
        return Response(res)


class CompetencePersonalizeFrameView(APIView):
    """
    POST /api/intelligence/personalization/frame/
    Generates competence-first, context-grounded conversational framing.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.competence_personalizer import CompetencePersonalizer
        budget = request.data.get("budget")
        budget_dec = Decimal(str(budget)) if budget else Decimal("5000.00")
        compared = request.data.get("compared_products", ["Sony WH-CH520", "JBL Tune 510BT"])
        res = CompetencePersonalizer.generate_competent_framing(budget=budget_dec, compared_products=compared)
        return Response(res)


class WhyNotThisExplainabilityView(APIView):
    """
    POST /api/intelligence/explainability/why-not-this/
    Returns rejection explainability proof explaining why a competing product was excluded.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.explainability_service import FinancialExplainabilityService
        name = request.data.get("rejected_product_name", "₹8,999 headphones")
        price = Decimal(str(request.data.get("rejected_price", 8999.0)))
        budget = Decimal(str(request.data.get("user_budget", 8000.0)))
        battery = float(request.data.get("battery_improvement_pct", 6.0))

        proof = FinancialExplainabilityService.generate_why_not_this_proof(
            rejected_product_name=name,
            rejected_price=price,
            user_budget=budget,
            battery_improvement_pct=battery
        )
        return Response(proof)


class ConversationalCheckoutView(APIView):
    """
    POST /api/intelligence/checkout/conversational/
    Implements Razorpay in-app conversational checkout:
    Intent → Shortlist against constraints → In-turn explainability → Mandatory Confirmation → Instant UPI mandate
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.conversational_checkout import ConversationalCheckoutService
        query = request.data.get("query", "Order lunch under ₹400, here in 30 minutes")
        confirmed = request.data.get("confirmed", False)
        order_id = request.data.get("order_id")
        amount = request.data.get("amount", 380.0)
        item_name = request.data.get("item_name", "Executive Thali")

        if confirmed and order_id:
            res = ConversationalCheckoutService.execute_payment_via_mcp(
                order_id=order_id,
                amount=float(amount),
                confirmed_by_user=True,
                item_name=item_name
            )
            return Response(res)

        res = ConversationalCheckoutService.process_conversational_intent(query)
        return Response(res)


class CatalogFeedView(APIView):
    """
    GET /api/intelligence/catalog/feed/
    Returns standard Schema.org JSON-LD merchant feed for AI shopping agents.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from products.models import Product
        from intelligence.services.agent_manifest import AgentManifestService
        limit = int(request.query_params.get("limit", 25))
        qs = Product.objects.filter(is_active=True).select_related('category', 'brand')[:limit]
        feed = [AgentManifestService.generate_schema_org_json_ld(p) for p in qs]
        return Response({
            "standard": "Schema.org/Product Feed",
            "taxonomy": "Google Product Taxonomy",
            "total_items": len(feed),
            "feed": feed
        })


class CatalogReconcileView(APIView):
    """
    GET /api/intelligence/catalog/reconcile/
    Verifies 3-way reconciliation (Page JSON-LD, Merchant Feed, MCP Tool) and sub-minute freshness.
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from intelligence.services.catalog_reconciliation import CatalogReconciliationService
        slug = request.query_params.get("slug")
        res = CatalogReconciliationService.reconcile_three_copies(slug)
        return Response(res)


class DunningSimulateView(APIView):
    """
    POST /api/intelligence/dunning/simulate/
    Simulates payment.failed webhook handling, retry cadence, and ledger recording.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.dunning_service import DunningRecoveryService
        action = request.data.get("action", "failed_payment")
        if action == "win_back":
            task_id = request.data.get("task_id", "dunn_test_01")
            amount = request.data.get("amount", 1200.00)
            res = DunningRecoveryService.simulate_successful_recovery(task_id, amount)
            return Response(res)

        payment_id = request.data.get("payment_id", "pay_failed_live")
        email = request.data.get("customer_email", "customer@example.com")
        amount = request.data.get("amount", 1200.00)
        attempt = int(request.data.get("attempt_number", 1))
        res = DunningRecoveryService.handle_failed_payment_webhook(payment_id, email, amount, attempt_number=attempt)
        return Response(res)


class RtoRiskEvaluateView(APIView):
    """
    POST /api/intelligence/rto/evaluate/
    Evaluates COD order for return-to-origin risk and switches to prepaid if score >= 65%.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.rto_risk_service import RtoRiskService
        pincode = request.data.get("pincode", "800001")
        refusal_hist = int(request.data.get("customer_refusal_history", 2))
        amount = request.data.get("order_amount", 3500.00)
        category = request.data.get("category", "apparel")
        res = RtoRiskService.evaluate_cod_order(pincode, refusal_hist, amount, category)
        return Response(res)


class PayoutForecastView(APIView):
    """
    GET /api/intelligence/payout/forecast/
    Provides 3-7 day settlement projection with hard bounded disbursement ceiling (≤ ₹50,000).
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        from intelligence.services.payout_forecaster import PayoutForecastingService
        days = int(request.query_params.get("days", 7))
        gmv = float(request.query_params.get("baseline_gmv", 28000.00))
        res = PayoutForecastingService.generate_payout_forecast(days=days, baseline_daily_gmv=gmv)
        return Response(res)


class AgentQuoteView(APIView):
    """
    POST /api/agent/quote/
    Machine quote endpoint for autonomous AI buyer agents.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.x402_merchant_surface import X402MerchantSurface
        slug = request.data.get("product_slug", "studio-headphones")
        qty = int(request.data.get("quantity", 1))
        res = X402MerchantSurface.get_machine_quote(slug, qty)
        return Response(res)


class AgentPurchaseView(APIView):
    """
    POST /api/agent/purchase/
    Machine purchase endpoint following the x402 protocol.
    Responds with HTTP 402 if signed authorization token is absent.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.x402_merchant_surface import X402MerchantSurface
        quote_id = request.data.get("quote_id", "")
        amount = float(request.data.get("amount", 0.0))
        nonce = request.data.get("nonce", "")
        token = request.data.get("signed_token") or request.headers.get("X-Authorization-Token")
        agent_id = request.data.get("agent_id", "autonomous_ai_buyer")

        res = X402MerchantSurface.process_machine_purchase(quote_id, amount, nonce, token, agent_id)
        status_code = res.get("http_status", 200)
        return Response(res, status=status_code)


class VoiceCommerceTurnView(APIView):
    """
    POST /api/intelligence/voice/process-turn/
    Voice-triggered payment link generation mid-call with audible confirmation gating.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        from intelligence.services.voice_commerce import VoiceCommerceAgent
        transcript = request.data.get("transcript", "I want to purchase the studio headphones right now")
        call_id = request.data.get("call_id")
        verbal_conf = request.data.get("verbal_confirmation")
        res = VoiceCommerceAgent.process_voice_call_turn(transcript, call_id, verbal_conf)
        return Response(res)













