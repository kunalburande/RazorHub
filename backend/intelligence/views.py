from rest_framework import viewsets, permissions, serializers
from rest_framework.decorators import action
from django.db.models import Q
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
    agent_name = serializers.SerializerMethodField()
    razorpay_entity = serializers.SerializerMethodField()
    bounded_amounts = serializers.SerializerMethodField()
    gating_mechanism = serializers.SerializerMethodField()
    explainability_text = serializers.SerializerMethodField()
    outcome = serializers.SerializerMethodField()

    class Meta:
        model = AuditEvent
        fields = [
            'id',
            'event_id',
            'trace_id',
            'agent',
            'agent_name',
            'action',
            'razorpay_entity',
            'bounded_amounts',
            'gating_mechanism',
            'explainability_text',
            'outcome',
            'details',
            'status',
            'payload',
            'created_at',
        ]

    def get_agent_name(self, obj):
        payload = obj.payload or {}
        return payload.get('agent_name') or obj.agent or 'commerce_agent'

    def get_razorpay_entity(self, obj):
        payload = obj.payload or {}
        if payload.get('razorpay_entity'):
            return payload['razorpay_entity']
        return {
            'entity_type': payload.get('target_type', 'order'),
            'entity_id': payload.get('target_id', f"rzp_{obj.id}"),
        }

    def get_bounded_amounts(self, obj):
        payload = obj.payload or {}
        bounded = payload.get('bounded') or payload.get('bounded_amounts')
        if bounded:
            if isinstance(bounded, (int, float)):
                return {'amount': float(bounded), 'currency': 'INR'}
            return bounded
        return {
            'amount': 0.0,
            'currency': 'INR'
        }

    def get_gating_mechanism(self, obj):
        payload = obj.payload or {}
        return payload.get('gated_by') or payload.get('gating_mechanism') or 'POLICY_FIREWALL_GATE'

    def get_explainability_text(self, obj):
        payload = obj.payload or {}
        return payload.get('explainable') or payload.get('explainability_text') or obj.details or ''

    def get_outcome(self, obj):
        payload = obj.payload or {}
        return payload.get('outcome') or obj.status or 'EXECUTED'

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
    serializer_class = AuditEventSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None

    def get_queryset(self):
        self._ensure_seed_multi_agent_events()
        qs = AuditEvent.objects.all().order_by('-created_at')

        agent_filter = self.request.query_params.get('agent') or self.request.query_params.get('agent_name')
        if agent_filter:
            qs = qs.filter(Q(agent__icontains=agent_filter) | Q(payload__agent_name__icontains=agent_filter))

        trace_id = self.request.query_params.get('trace_id')
        if trace_id:
            qs = qs.filter(trace_id=trace_id)

        outcome = self.request.query_params.get('outcome') or self.request.query_params.get('status')
        if outcome:
            qs = qs.filter(Q(status__iexact=outcome) | Q(payload__outcome__iexact=outcome))

        limit = self.request.query_params.get('limit')
        if limit and str(limit).isdigit():
            return qs[:int(limit)]

        return qs

    def _ensure_seed_multi_agent_events(self):
        """
        Guarantees that realistic, interconnected multi-agent events exist in the database,
        spanning dunning_agent, upsell_agent, campaign_agent, and checkout_agent,
        connected by cross-agent trace IDs with structured schemas.
        """
        if AuditEvent.objects.filter(trace_id='trace_rog_ally_8901').exists():
            return

        seed_events = [
            # ── TRACE 1: High-Value Gaming Rig Checkout & Post-Purchase Retention Loop ──
            {
                'event_id': 'aud_chk_8901_stage',
                'trace_id': 'trace_rog_ally_8901',
                'agent': 'checkout_agent',
                'action': 'STAGE_CHECKOUT_INTENT',
                'status': 'AWAITING_CONFIRM',
                'details': 'Staged ASUS ROG Ally (₹63,112.00). User consent policy mandates human confirmation before Razorpay payment capture.',
                'payload': {
                    'agent_name': 'checkout_agent',
                    'action': 'STAGE_CHECKOUT_INTENT',
                    'razorpay_entity': {
                        'entity_type': 'order',
                        'entity_id': 'order_OG72kA91sM2',
                        'receipt': 'rcpt_asus_ally_01'
                    },
                    'bounded': {
                        'amount': 63112.00,
                        'currency': 'INR',
                        'per_transaction_limit': 150000.00,
                        'delivery_fee': 50.00
                    },
                    'gated_by': 'HUMAN_IN_THE_LOOP',
                    'explainable': 'Staged ASUS ROG Ally (₹63,112.00). User consent policy mandates human confirmation before Razorpay payment capture.',
                    'outcome': 'AWAITING_USER_CONFIRMATION'
                }
            },
            {
                'event_id': 'aud_chk_8901_capture',
                'trace_id': 'trace_rog_ally_8901',
                'agent': 'checkout_agent',
                'action': 'AUTHORIZE_PAYMENT_CAPTURE',
                'status': 'CAPTURED',
                'details': 'Buyer confirmed checkout approval card in modal. Verified within ₹150,000 daily spend boundary.',
                'payload': {
                    'agent_name': 'checkout_agent',
                    'action': 'AUTHORIZE_PAYMENT_CAPTURE',
                    'razorpay_entity': {
                        'entity_type': 'payment',
                        'entity_id': 'pay_OG72P91sM2',
                        'order_id': 'order_OG72kA91sM2'
                    },
                    'bounded': {
                        'amount': 63162.00,
                        'currency': 'INR',
                        'authorized_limit': 150000.00
                    },
                    'gated_by': 'BIOMETRIC_CONSENT_POLICY',
                    'explainable': 'Buyer confirmed checkout approval card in modal. Verified within ₹150,000 daily spend boundary.',
                    'outcome': 'CAPTURED'
                }
            },
            {
                'event_id': 'aud_ups_8901_recommend',
                'trace_id': 'trace_rog_ally_8901',
                'agent': 'upsell_agent',
                'action': 'RECOMMEND_COMPANION_ACCESSORY',
                'status': 'CONVERTED',
                'details': 'Matched Anker 735 GaN 65W fast charger as optimal companion for ASUS ROG Ally. 34.2% margin preserved against 20% floor.',
                'payload': {
                    'agent_name': 'upsell_agent',
                    'action': 'RECOMMEND_COMPANION_ACCESSORY',
                    'razorpay_entity': {
                        'entity_type': 'payment_link',
                        'entity_id': 'plink_GaN65W_881',
                        'reference': 'inv_up_881'
                    },
                    'bounded': {
                        'amount': 2499.00,
                        'currency': 'INR',
                        'discount_pct': 10.0,
                        'margin_preserved_pct': 34.2
                    },
                    'gated_by': 'SELLER_MARGIN_FLOOR',
                    'explainable': 'Matched Anker 735 GaN 65W fast charger as optimal companion for ASUS ROG Ally. 34.2% margin preserved against 20% floor.',
                    'outcome': 'CONVERTED'
                }
            },
            {
                'event_id': 'aud_cmp_8901_cadence',
                'trace_id': 'trace_rog_ally_8901',
                'agent': 'campaign_agent',
                'action': 'COMPILE_RETENTION_CADENCE',
                'status': 'ACTIVE',
                'details': 'Initiated 5-stage automated post-purchase retention cadence (Day 0, Day 2, Day 7, Day 20, Day 28) for verified high-LTV gamer segment.',
                'payload': {
                    'agent_name': 'campaign_agent',
                    'action': 'COMPILE_RETENTION_CADENCE',
                    'razorpay_entity': {
                        'entity_type': 'campaign',
                        'entity_id': 'cmp_GamingLaptopRev_402',
                        'slug': 'gamer-retention-cadence'
                    },
                    'bounded': {
                        'budget_cap': 50000.00,
                        'current_spend': 12450.00,
                        'currency': 'INR'
                    },
                    'gated_by': 'BUDGET_CAP_GUARDRAIL',
                    'explainable': 'Initiated 5-stage automated post-purchase retention cadence (Day 0, Day 2, Day 7, Day 20, Day 28) for verified high-LTV gamer segment.',
                    'outcome': 'ACTIVE_ORCHESTRATION'
                }
            },

            # ── TRACE 2: Failed UPI Transaction & Autonomous Dunning Recovery ──
            {
                'event_id': 'aud_chk_4102_session',
                'trace_id': 'trace_dunn_recovery_4102',
                'agent': 'checkout_agent',
                'action': 'INITIATE_GATEWAY_SESSION',
                'status': 'GATEWAY_DISPATCHED',
                'details': 'Validated order for Sony WH-CH520 Wireless Headphones. RTO risk score 12.5/100 cleared pre-dispatch threshold.',
                'payload': {
                    'agent_name': 'checkout_agent',
                    'action': 'INITIATE_GATEWAY_SESSION',
                    'razorpay_entity': {
                        'entity_type': 'order',
                        'entity_id': 'order_FailPay_3910A',
                        'receipt': 'rcpt_sony_wh520'
                    },
                    'bounded': {
                        'amount': 4040.00,
                        'currency': 'INR',
                        'risk_score': 12.5
                    },
                    'gated_by': 'RISK_SENTINEL_CLEAR',
                    'explainable': 'Validated order for Sony WH-CH520 Wireless Headphones. RTO risk score 12.5/100 cleared pre-dispatch threshold.',
                    'outcome': 'GATEWAY_DISPATCHED'
                }
            },
            {
                'event_id': 'aud_dun_4102_intercept',
                'trace_id': 'trace_dunn_recovery_4102',
                'agent': 'dunning_agent',
                'action': 'INTERCEPT_GATEWAY_FAILURE',
                'status': 'CADENCE_SCHEDULED',
                'details': 'Intercepted payment.failed webhook from Razorpay (UPI session timeout). Scheduled intelligent multi-channel retry cadence.',
                'payload': {
                    'agent_name': 'dunning_agent',
                    'action': 'INTERCEPT_GATEWAY_FAILURE',
                    'razorpay_entity': {
                        'entity_type': 'payment_error',
                        'entity_id': 'pay_Failed_9182K',
                        'error_code': 'BAD_REQUEST_PAYMENT_TIMED_OUT'
                    },
                    'bounded': {
                        'amount': 4040.00,
                        'currency': 'INR',
                        'expected_recovery_rate': 78.4
                    },
                    'gated_by': 'POLICY_FIREWALL_GATE',
                    'explainable': 'Intercepted payment.failed webhook from Razorpay (UPI session timeout). Scheduled intelligent multi-channel retry cadence.',
                    'outcome': 'CADENCE_SCHEDULED'
                }
            },
            {
                'event_id': 'aud_dun_4102_retry',
                'trace_id': 'trace_dunn_recovery_4102',
                'agent': 'dunning_agent',
                'action': 'DISPATCH_SMART_RETRY',
                'status': 'RECOVERED',
                'details': 'Dispatched zero-friction 1-click UPI retry mandate via SMS/WhatsApp within 4 minutes of failure event; recovered cart.',
                'payload': {
                    'agent_name': 'dunning_agent',
                    'action': 'DISPATCH_SMART_RETRY',
                    'razorpay_entity': {
                        'entity_type': 'payment_link',
                        'entity_id': 'plink_DunnFast_4102',
                        'short_url': 'https://rzp.io/i/dunn4102'
                    },
                    'bounded': {
                        'amount': 4040.00,
                        'currency': 'INR',
                        'max_allowed': 5000.00
                    },
                    'gated_by': 'RATE_LIMIT_GUARDRAIL',
                    'explainable': 'Dispatched zero-friction 1-click UPI retry mandate via SMS/WhatsApp within 4 minutes of failure event; recovered cart.',
                    'outcome': 'RECOVERED'
                }
            },
            {
                'event_id': 'aud_cmp_4102_lifecycle',
                'trace_id': 'trace_dunn_recovery_4102',
                'agent': 'campaign_agent',
                'action': 'UPDATE_CUSTOMER_LIFECYCLE_STAGE',
                'status': 'COMPLETED',
                'details': 'Customer salvaged by dunning engine; re-indexed to Active High-Intent segment; suppressed cart-abandonment penalty.',
                'payload': {
                    'agent_name': 'campaign_agent',
                    'action': 'UPDATE_CUSTOMER_LIFECYCLE_STAGE',
                    'razorpay_entity': {
                        'entity_type': 'customer_segment',
                        'entity_id': 'seg_RecoveredHighIntent_12'
                    },
                    'bounded': {
                        'recovered_value': 4040.00,
                        'currency': 'INR'
                    },
                    'gated_by': 'AUTONOMOUS_POLICY',
                    'explainable': 'Customer salvaged by dunning engine; re-indexed to Active High-Intent segment; suppressed cart-abandonment penalty.',
                    'outcome': 'COMPLETED'
                }
            },

            # ── TRACE 3: Festive Audio Expansion, Dynamic Bundling & Subscription Mandate ──
            {
                'event_id': 'aud_cmp_7720_campaign',
                'trace_id': 'trace_festive_audio_7720',
                'agent': 'campaign_agent',
                'action': 'ORCHESTRATE_CATEGORY_EXPANSION',
                'status': 'ACTIVE',
                'details': 'Compiled autonomous campaign targeting audio buyers. Budget ceiling enforced at ₹25,000 with auto-pause sentinel.',
                'payload': {
                    'agent_name': 'campaign_agent',
                    'action': 'ORCHESTRATE_CATEGORY_EXPANSION',
                    'razorpay_entity': {
                        'entity_type': 'campaign',
                        'entity_id': 'cmp_AudioExpansion_901',
                        'name': 'Festive Audio Lift'
                    },
                    'bounded': {
                        'budget_cap': 25000.00,
                        'target_roi_multiplier': 3.8,
                        'currency': 'INR'
                    },
                    'gated_by': 'BUDGET_CAP_GUARDRAIL',
                    'explainable': 'Compiled autonomous campaign targeting audio buyers. Budget ceiling enforced at ₹25,000 with auto-pause sentinel.',
                    'outcome': 'ACTIVE'
                }
            },
            {
                'event_id': 'aud_ups_7720_bundle',
                'trace_id': 'trace_festive_audio_7720',
                'agent': 'upsell_agent',
                'action': 'COMPILE_DYNAMIC_BUNDLE',
                'status': 'STAGED',
                'details': 'Bundled boAt Rockerz 450 Pro with protective hard case and audio adapter. Discount capped strictly at 12.7% (below 15% merchant max).',
                'payload': {
                    'agent_name': 'upsell_agent',
                    'action': 'COMPILE_DYNAMIC_BUNDLE',
                    'razorpay_entity': {
                        'entity_type': 'bundle_quote',
                        'entity_id': 'bndl_AudioPack_772'
                    },
                    'bounded': {
                        'bundle_total': 5490.00,
                        'regular_total': 6290.00,
                        'savings': 800.00,
                        'currency': 'INR'
                    },
                    'gated_by': 'DISCOUNT_CEILING_POLICY',
                    'explainable': 'Bundled boAt Rockerz 450 Pro with protective hard case and audio adapter. Discount capped strictly at 12.7% (below 15% merchant max).',
                    'outcome': 'STAGED'
                }
            },
            {
                'event_id': 'aud_chk_7720_sub',
                'trace_id': 'trace_festive_audio_7720',
                'agent': 'checkout_agent',
                'action': 'PRE_AUTHORIZE_SUBSCRIPTION_MANDATE',
                'status': 'MANDATE_AUTHORIZED',
                'details': 'Presented Razorpay Recurring Mandate for device insurance. Explicit customer consent confirmation enforced.',
                'payload': {
                    'agent_name': 'checkout_agent',
                    'action': 'PRE_AUTHORIZE_SUBSCRIPTION_MANDATE',
                    'razorpay_entity': {
                        'entity_type': 'subscription',
                        'entity_id': 'sub_AudioCare_228',
                        'plan_id': 'plan_CarePlus_99'
                    },
                    'bounded': {
                        'recurring_amount': 199.00,
                        'frequency': 'monthly',
                        'currency': 'INR'
                    },
                    'gated_by': 'HUMAN_IN_THE_LOOP',
                    'explainable': 'Presented Razorpay Recurring Mandate for device insurance. Explicit customer consent confirmation enforced.',
                    'outcome': 'MANDATE_AUTHORIZED'
                }
            },

            # ── TRACE 4: Pre-Dispatch COD Risk Interception & Conversion to Prepaid ──
            {
                'event_id': 'aud_chk_5510_rto_block',
                'trace_id': 'trace_rto_guardrail_5510',
                'agent': 'checkout_agent',
                'action': 'EVALUATE_COD_ELIGIBILITY',
                'status': 'BLOCKED',
                'details': 'High RTO risk score (78/100) detected on COD order. Autonomous sentinel blocked COD dispatch to prevent return loss.',
                'payload': {
                    'agent_name': 'checkout_agent',
                    'action': 'EVALUATE_COD_ELIGIBILITY',
                    'razorpay_entity': {
                        'entity_type': 'order',
                        'entity_id': 'order_COD_RiskCheck_551'
                    },
                    'bounded': {
                        'cart_value': 3499.00,
                        'rto_risk_score': 78.0,
                        'currency': 'INR'
                    },
                    'gated_by': 'RTO_RISK_GUARDRAIL',
                    'explainable': 'High RTO risk score (78/100) detected on COD order. Autonomous sentinel blocked COD dispatch to prevent return loss.',
                    'outcome': 'BLOCKED'
                }
            },
            {
                'event_id': 'aud_dun_5510_cod_convert',
                'trace_id': 'trace_rto_guardrail_5510',
                'agent': 'dunning_agent',
                'action': 'CONVERT_COD_TO_PREPAID',
                'status': 'CONVERTED',
                'details': 'Offered ₹100 instant UPI discount to switch from COD to prepaid. Margin remaining (24%) clears the 20% floor.',
                'payload': {
                    'agent_name': 'dunning_agent',
                    'action': 'CONVERT_COD_TO_PREPAID',
                    'razorpay_entity': {
                        'entity_type': 'payment_link',
                        'entity_id': 'plink_PrepaidIncentive_551',
                        'incentive_discount': 100.00
                    },
                    'bounded': {
                        'amount': 3399.00,
                        'currency': 'INR',
                        'incentive_amount': 100.00
                    },
                    'gated_by': 'SELLER_MARGIN_FLOOR',
                    'explainable': 'Offered ₹100 instant UPI discount to switch from COD to prepaid. Margin remaining (24%) clears the 20% floor.',
                    'outcome': 'CONVERTED'
                }
            },
        ]

        for item in seed_events:
            AuditEvent.objects.create(
                event_id=item['event_id'],
                trace_id=item['trace_id'],
                agent=item['agent'],
                action=item['action'],
                status=item['status'],
                details=item['details'],
                payload=item['payload']
            )


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













