import logging
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.utils import timezone


logger = logging.getLogger(__name__)


from .models import (
    Agent,
    AgentStatus,
    AgentTool,
    AgentPolicy,
    AgentExecution,
    AgentApproval,
    AgentAuditLog,
    AgentGovernancePolicy,
    GovernanceDecisionRecord,
    RefundAnomalyRecord,
    AgentPaymentAuthorization,
    Connector,
    ConnectorCapability,
    ConnectorExecution,
    CommunicationConsent,
    CommunicationPreference,
    CommunicationEvent,
    FinancialRiskRecord,
)
from .serializers import (
    AgentSerializer,
    AgentToolSerializer,
    AgentPolicySerializer,
    AgentExecutionSerializer,
    AgentApprovalSerializer,
    AgentAuditLogSerializer,
    AgentGovernancePolicySerializer,
    GovernanceDecisionRecordSerializer,
    RefundAnomalyRecordSerializer,
    AgentPaymentAuthorizationSerializer,
    ConnectorSerializer,
    ConnectorExecutionSerializer,
    CommunicationConsentSerializer,
    CommunicationPreferenceSerializer,
    CommunicationEventSerializer,
    FinancialRiskRecordSerializer,
)
from .risk import FinancialRiskEngine



from decimal import Decimal
from .runtime import AgentRuntime




class IsSellerOrAdminPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return getattr(request.user, "effective_role", "") in ["seller", "admin"]


class AgentViewSet(viewsets.ModelViewSet):
    queryset = Agent.objects.all()
    serializer_class = AgentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        agent = self.get_object()
        agent.activate()
        return Response({"status": "ACTIVE", "message": f"Agent '{agent.name}' is now ACTIVE."})

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        agent = self.get_object()
        agent.pause()
        return Response({"status": "PAUSED", "message": f"Agent '{agent.name}' is now PAUSED."})

    @action(detail=True, methods=["post"])
    def disable(self, request, pk=None):
        agent = self.get_object()
        agent.disable()
        return Response({"status": "DISABLED", "message": f"Agent '{agent.name}' is now DISABLED."})

    @action(detail=False, methods=["get"])
    def marketplace(self, request):
        from .marketplace_templates import PREBUILT_AGENT_TEMPLATES
        existing_agents = {a.name.lower(): str(a.id) for a in Agent.objects.all()}
        
        catalog = []
        for tmpl in PREBUILT_AGENT_TEMPLATES:
            installed_id = existing_agents.get(tmpl["name"].lower())
            catalog.append({
                **tmpl,
                "is_installed": bool(installed_id),
                "installed_agent_id": installed_id,
            })
        return Response(catalog)

    @action(detail=False, methods=["post"])
    def install(self, request):
        from .marketplace_templates import get_template_by_id
        template_id = request.data.get("template_id")
        if not template_id:
            return Response({"error": "Field 'template_id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tmpl = get_template_by_id(template_id)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)

        custom_name = request.data.get("name") or tmpl["name"]
        auto_activate = request.data.get("auto_activate", True)

        # 1. Create or retrieve Agent
        agent, created = Agent.objects.get_or_create(
            name=custom_name,
            defaults={
                "description": tmpl["description"],
                "system_prompt": tmpl["system_prompt"],
                "status": AgentStatus.ACTIVE if auto_activate else AgentStatus.DRAFT,
                "approval_mode": tmpl.get("approval_mode", "AUTO"),
                "risk_level": tmpl.get("risk_level", "LOW"),
                "metadata": {
                    "template_id": tmpl["id"],
                    "category": tmpl["category"],
                    "automation_level": tmpl["automation_level"],
                    "capabilities": tmpl.get("capabilities", []),
                },
            },
        )

        # 2. Attach Tools
        from .models import AgentTool, AgentTrigger, AgentGovernancePolicy, AgentVersion, AgentAuditLog, AuditEventType, AuditSeverity
        for tool_name in tmpl.get("tools_used", []):
            tool_obj, _ = AgentTool.objects.get_or_create(
                name=tool_name,
                defaults={"category": tmpl["category"].lower(), "description": f"Tool for {tool_name}"},
            )
            agent.tools.add(tool_obj)

        # 3. Create Triggers
        for trig in tmpl.get("triggers", []):
            AgentTrigger.objects.get_or_create(
                agent=agent,
                name=trig["name"],
                trigger_type=trig["trigger_type"],
                defaults={"configuration": trig.get("config", {})},
            )


        # 4. Create Governance Policy
        gov_data = tmpl.get("governance_policy", {})
        if gov_data and not hasattr(agent, "governance_policy"):
            AgentGovernancePolicy.objects.create(
                agent=agent,
                name=gov_data.get("name", f"{agent.name} Policy"),
                max_transaction_amount=gov_data.get("max_transaction_amount", 5000.00),
                daily_spend_limit=gov_data.get("daily_spend_limit", 10000.00),
                require_approval_above=gov_data.get("require_approval_above", 2000.00),
                blocked_categories=gov_data.get("blocked_categories", []),
                allowed_categories=gov_data.get("allowed_categories", []),
                require_human_approval=gov_data.get("require_human_approval", False),
                require_double_confirmation=gov_data.get("require_double_confirmation", False),
            )

        # 5. Create Version snapshot
        AgentVersion.objects.create(
            agent=agent,
            system_prompt=agent.system_prompt,
            configuration={"tools": tmpl.get("tools_used", []), "governance": str(gov_data)},
            change_summary="Marketplace template install",
        )


        # 6. Log audit event
        AgentAuditLog.objects.create(
            agent=agent,
            event_type=AuditEventType.AGENT_CREATED,
            severity=AuditSeverity.INFO,
            actor_type="USER",
            actor_id=str(request.user.id) if request.user else "system",
            details={"action": "INSTALLED_PREBUILT_AGENT", "template_id": template_id, "name": agent.name},
        )

        return Response(AgentSerializer(agent).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def execute(self, request, pk=None):
        agent = self.get_object()
        req_text = request.data.get("request", "").strip()
        if not req_text:
            return Response({"error": "Field 'request' is required."}, status=status.HTTP_400_BAD_REQUEST)

        session_id = request.data.get("session_id", "")
        custom_context = request.data.get("context", {})

        execution = AgentRuntime.run(
            request_text=req_text,
            agent=agent,
            user=request.user,
            session_id=session_id,
            context=custom_context,
        )

        return Response(AgentExecutionSerializer(execution).data)

    def create(self, request, *args, **kwargs):
        gov_data = request.data.get("governance_policy")
        response = super().create(request, *args, **kwargs)
        if response.status_code == 201 and gov_data:
            agent = Agent.objects.get(id=response.data["id"])
            AgentGovernancePolicy.objects.create(
                agent=agent,
                name=gov_data.get("name", f"{agent.name} Policy"),
                max_transaction_amount=gov_data.get("max_transaction_amount", 5000.00),
                daily_spend_limit=gov_data.get("daily_spend_limit", 10000.00),
                weekly_spend_limit=gov_data.get("weekly_spend_limit", 40000.00),
                monthly_spend_limit=gov_data.get("monthly_spend_limit", 150000.00),
                require_approval_above=gov_data.get("require_approval_above", 2000.00),
                blocked_categories=gov_data.get("blocked_categories", []),
                allowed_categories=gov_data.get("allowed_categories", []),
                allowed_merchants=gov_data.get("allowed_merchants", []),
                blocked_merchants=gov_data.get("blocked_merchants", []),
                require_human_approval=gov_data.get("require_human_approval", False),
                require_double_confirmation=gov_data.get("require_double_confirmation", False),
            )
            response.data = AgentSerializer(agent).data
        return response

    @action(detail=True, methods=["post"])
    def update_connectors(self, request, pk=None):
        agent = self.get_object()
        connector_ids = request.data.get("connector_ids", [])
        connectors_qs = Connector.objects.filter(id__in=connector_ids)
        agent.connectors.set(connectors_qs)
        return Response({
            "status": "UPDATED",
            "agent_id": str(agent.id),
            "connected_count": agent.connectors.count(),
            "connectors": [{"id": str(c.id), "slug": c.slug, "name": c.name} for c in agent.connectors.all()],
        })





class AgentToolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentTool.objects.filter(is_enabled=True)
    serializer_class = AgentToolSerializer
    permission_classes = [permissions.IsAuthenticated]


class AgentPolicyViewSet(viewsets.ModelViewSet):
    queryset = AgentPolicy.objects.all()
    serializer_class = AgentPolicySerializer
    permission_classes = [permissions.IsAuthenticated]


class AgentExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgentExecutionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        from django.db.models import Q
        qs = AgentExecution.objects.select_related("agent", "user").prefetch_related("steps", "approvals").all()
        agent_id = self.request.query_params.get("agent")
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        status_param = self.request.query_params.get("status")
        if status_param and status_param != "ALL":
            qs = qs.filter(status=status_param)
        has_error = self.request.query_params.get("has_error")
        if has_error and str(has_error).lower() in ["true", "1"]:
            qs = qs.filter(Q(status="FAILED") | ~Q(error_message=""))
        return qs.order_by("-started_at")

    @action(detail=True, methods=["get"])
    def trace(self, request, pk=None):
        execution = self.get_object()
        return Response({
            "execution_id": str(execution.execution_id),
            "status": execution.status,
            "trace": execution.execution_trace,
        })

    @action(detail=True, methods=["get"])
    def timeline(self, request, pk=None):
        execution = self.get_object()
        return Response({
            "execution_id": str(execution.execution_id),
            "status": execution.status,
            "duration_ms": execution.duration_ms,
            "timeline": execution.timeline or [],
        })

    @action(detail=True, methods=["get"], url_path="tool-calls")
    def tool_calls(self, request, pk=None):
        execution = self.get_object()
        from .models import AgentExecutionStep
        from .serializers import AgentExecutionStepSerializer
        steps = AgentExecutionStep.objects.filter(execution=execution, step_type="TOOL_EXECUTION").order_by("step_number")
        return Response({
            "execution_id": str(execution.execution_id),
            "tools_selected": execution.tools_selected or [],
            "tool_inputs": execution.tool_inputs or [],
            "tool_results": execution.tool_results or [],
            "steps": AgentExecutionStepSerializer(steps, many=True).data,
        })

    @action(detail=True, methods=["get"], url_path="policy-decisions")
    def policy_decisions(self, request, pk=None):
        execution = self.get_object()
        return Response({
            "execution_id": str(execution.execution_id),
            "policy_checks": execution.policy_checks or [],
            "risk_checks": execution.risk_checks or {},
            "approval_request": execution.approval_request or {},
            "approval_response": execution.approval_response or {},
        })

    @action(detail=True, methods=["get"])
    def errors(self, request, pk=None):
        execution = self.get_object()
        from .models import AgentExecutionStep
        from .serializers import AgentExecutionStepSerializer
        failed_steps = AgentExecutionStep.objects.filter(execution=execution, status="FAILED").order_by("step_number")
        return Response({
            "execution_id": str(execution.execution_id),
            "has_error": bool(execution.error_message or execution.status == "FAILED"),
            "status": execution.status,
            "error_message": execution.error_message,
            "failed_steps": AgentExecutionStepSerializer(failed_steps, many=True).data,
        })

    @action(detail=True, methods=["post"])
    def replay(self, request, pk=None):
        from .observability.replay import ExecutionReplayEngine
        user = request.user if getattr(request, "user", None) and request.user.is_authenticated else None
        try:
            result = ExecutionReplayEngine.replay(execution_id=str(pk), user=user, sandbox=True)
            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



class AgentApprovalViewSet(viewsets.ModelViewSet):
    queryset = AgentApproval.objects.select_related("execution", "execution__agent").all()
    serializer_class = AgentApprovalSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def decide(self, request, pk=None):
        approval = self.get_object()
        decision = request.data.get("decision", "").upper()
        notes = request.data.get("notes", "")
        double_confirmed = bool(request.data.get("double_confirmed", False))

        if decision not in ["APPROVED", "REJECTED"]:
            return Response({"error": "decision must be either APPROVED or REJECTED"}, status=status.HTTP_400_BAD_REQUEST)

        # Enforce Double Confirmation for high risk transactions
        if decision == "APPROVED" and approval.requires_double_confirmation and not double_confirmed:
            return Response(
                {
                    "error": "DOUBLE_CONFIRMATION_REQUIRED",
                    "message": "High-risk action requires explicit double confirmation before disbursement.",
                    "approval_id": str(approval.approval_id),
                    "risk_score": approval.risk_score,
                    "amount": str(approval.amount or 0),
                    "merchant": approval.merchant,
                },
                status=status.HTTP_428_PRECONDITION_REQUIRED,
            )

        if double_confirmed:
            approval.is_double_confirmed = True
            approval.save(update_fields=["is_double_confirmed"])

        try:
            resumed_execution = AgentRuntime.resume_after_approval(
                approval_id=str(approval.approval_id),
                decision=decision,
                approver=request.user,
                notes=notes,
            )
            return Response(AgentExecutionSerializer(resumed_execution).data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class AgentGovernancePolicyViewSet(viewsets.ModelViewSet):
    queryset = AgentGovernancePolicy.objects.all()
    serializer_class = AgentGovernancePolicySerializer
    permission_classes = [permissions.IsAuthenticated]


class GovernanceDecisionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GovernanceDecisionRecord.objects.select_related("agent", "user").all()
    serializer_class = GovernanceDecisionRecordSerializer
    permission_classes = [permissions.IsAuthenticated]


class AgentAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AgentAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = AgentAuditLog.objects.select_related("agent", "execution").all()
        agent_id = self.request.query_params.get("agent")
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        return qs



class ExecuteAgentView(APIView):
    """
    POST /api/agent-runtime/execute/
    Payload: { "request": "Check balance of acc_123", "agent_id": "<uuid>" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        req_text = request.data.get("request", "").strip()
        if not req_text:
            return Response({"error": "Field 'request' is required."}, status=status.HTTP_400_BAD_REQUEST)

        agent_id = request.data.get("agent_id")
        agent = None
        if agent_id:
            agent = get_object_or_404(Agent, id=agent_id)

        session_id = request.data.get("session_id", "")
        custom_context = request.data.get("context", {})

        execution = AgentRuntime.run(
            request_text=req_text,
            agent=agent,
            user=request.user,
            session_id=session_id,
            context=custom_context,
        )

        return Response(AgentExecutionSerializer(execution).data)


class BlueprintGenerateView(APIView):
    """
    POST /api/agent-runtime/blueprint/generate/
    Accepts: { "message": str, "history": list }
    Transforms natural language prompt into structured AgentBlueprint.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message = request.data.get("message", "").strip()
        if not message:
            return Response({"error": "Field 'message' is required."}, status=status.HTTP_400_BAD_REQUEST)

        history = request.data.get("history", [])
        from .blueprint import AgentBlueprintService

        result = AgentBlueprintService.generate(message, history=history)
        return Response(result)


class BlueprintActivateView(APIView):
    """
    POST /api/agent-runtime/blueprint/activate/
    Accepts: { "blueprint": dict, "activate": bool, "confirmation": bool }
    Persists structured AgentBlueprint into real database models.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        blueprint_data = request.data.get("blueprint")
        if not blueprint_data or not isinstance(blueprint_data, dict):
            return Response({"error": "Field 'blueprint' object is required."}, status=status.HTTP_400_BAD_REQUEST)

        activate = bool(request.data.get("activate", False))
        confirmation = bool(request.data.get("confirmation", False))

        # Enforce explicit human confirmation if activating
        if activate and not confirmation:
            return Response(
                {"error": "CONFIRMATION_REQUIRED", "message": "Explicit confirmation is required before activation."},
                status=status.HTTP_428_PRECONDITION_REQUIRED,
            )

        from .blueprint import AgentBlueprintService

        try:
            agent = AgentBlueprintService.provision_blueprint(
                blueprint_data=blueprint_data,
                status="ACTIVE" if activate else "DRAFT",
                user=request.user,
            )
            return Response(AgentSerializer(agent).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Failed to provision blueprint: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RefundSpikeRunView(APIView):
    """
    POST /api/agent-runtime/refund-spike-analyzer/run/
    Runs an immediate autonomous analysis of refund metrics.
    Computes deterministic rates, triggers alerts if anomaly detected, and synthesizes report.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .refund_analyzer import RefundSpikeService

        baseline_rate = request.data.get("baseline_rate")
        threshold_factor = request.data.get("threshold_factor")
        agent_id = request.data.get("agent_id")

        b_dec = Decimal(str(baseline_rate)) if baseline_rate is not None else None
        t_dec = Decimal(str(threshold_factor)) if threshold_factor is not None else None

        record = RefundSpikeService.run_analysis(
            agent_id=agent_id,
            baseline_rate=b_dec,
            threshold_factor=t_dec,
            user=request.user,
        )
        return Response(RefundAnomalyRecordSerializer(record).data, status=status.HTTP_200_OK)


class RefundSpikeLatestView(APIView):
    """
    GET /api/agent-runtime/refund-spike-analyzer/latest/
    Retrieves the latest refund analysis snapshot or computes one on-demand.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        latest = RefundAnomalyRecord.objects.select_related("agent", "execution").first()
        if not latest:
            from .refund_analyzer import RefundSpikeService
            latest = RefundSpikeService.run_analysis(user=request.user)

        return Response(RefundAnomalyRecordSerializer(latest).data)


class RefundSpikeHistoryView(APIView):
    """
    GET /api/agent-runtime/refund-spike-analyzer/history/
    Lists chronological execution timeline of past analyses.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        records = RefundAnomalyRecord.objects.select_related("agent").all()[:20]
        return Response(RefundAnomalyRecordSerializer(records, many=True).data)


class RefundSpikeScheduleView(APIView):
    """
    POST /api/agent-runtime/refund-spike-analyzer/schedule/
    Payload: { "is_active": bool, "cron": str, "frequency": str }
    Configures or toggles the automated scheduled execution trigger.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from .models import Agent, AgentTrigger, TriggerType
        agent = Agent.objects.filter(name__icontains="Refund Spike Analyzer").first()
        if not agent:
            # Auto provision default agent if missing
            from .marketplace_templates import PREBUILT_AGENT_TEMPLATES
            tmpl = next((t for t in PREBUILT_AGENT_TEMPLATES if t["id"] == "refund-spike-analyzer"), None)
            if tmpl:
                from .views import AgentViewSet
                agent = Agent.objects.create(
                    name=tmpl["name"],
                    description=tmpl["description"],
                    system_prompt=tmpl["system_prompt"],
                    status="ACTIVE",
                    approval_mode=tmpl["approval_mode"],
                    risk_level=tmpl["risk_level"],
                )

        if not agent:
            return Response({"error": "Refund Spike Analyzer agent not found."}, status=status.HTTP_404_NOT_FOUND)

        is_active = bool(request.data.get("is_active", True))
        cron_expr = request.data.get("cron", "0 9 * * *")
        frequency = request.data.get("frequency", "daily")

        trigger, _ = AgentTrigger.objects.get_or_create(
            agent=agent,
            trigger_type=TriggerType.SCHEDULE,
            defaults={
                "name": "Refund Spike Daily Schedule",
                "configuration": {"cron": cron_expr, "frequency": frequency},
                "is_active": is_active,
            },
        )
        trigger.is_active = is_active
        trigger.configuration = {"cron": cron_expr, "frequency": frequency}
        trigger.save()

        return Response({
            "status": "SCHEDULE_UPDATED",
            "is_active": trigger.is_active,
            "trigger_id": str(trigger.id),
            "configuration": trigger.configuration,
        })


class CommerceChatView(APIView):
    """
    POST /api/agent-runtime/commerce/chat/
    Conversational Agentic Commerce interface.
    Handles product searching, comparisons, cart calculation, and payment intent generation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        message = request.data.get("message", "").strip()
        if not message:
            return Response({"error": "Field 'message' is required."}, status=status.HTTP_400_BAD_REQUEST)

        history = request.data.get("history", [])
        cart_data = request.data.get("cart")
        from .commerce_assistant import AgenticCommerceService

        res = AgenticCommerceService.handle_chat(
            user_message=message,
            history=history,
            user=request.user,
            cart_data=cart_data,
        )
        return Response(res)


class CommerceConsentView(APIView):
    """
    GET & POST /api/agent-runtime/commerce/consent/
    Inspects or updates the user's consent authorization policy.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .models import AgentUserConsentPolicy
        policy, _ = AgentUserConsentPolicy.objects.get_or_create(
            user=request.user,
            defaults={
                "per_transaction_limit": Decimal("150000.00"),
                "approval_threshold": Decimal("2000.00"),
                "daily_limit": Decimal("200000.00"),
                "monthly_limit": Decimal("500000.00"),
                "allowed_categories": ["electronics", "peripherals", "accessories", "apparel", "home", "mobiles", "laptops", "gaming", "audio-sound"],
            },
        )
        return Response({
            "per_transaction_limit": float(policy.per_transaction_limit),
            "approval_threshold": float(policy.approval_threshold),
            "daily_limit": float(policy.daily_limit),
            "monthly_limit": float(policy.monthly_limit),
            "allowed_categories": policy.allowed_categories,
            "daily_spent": float(policy.daily_spent),
            "monthly_spent": float(policy.monthly_spent),
            "is_configured": policy.is_configured,
            "configured_at": policy.configured_at.isoformat() if policy.configured_at else None,
        })

    def post(self, request):
        from .models import AgentUserConsentPolicy
        policy, _ = AgentUserConsentPolicy.objects.get_or_create(user=request.user)

        data = request.data
        if "per_transaction_limit" in data:
            policy.per_transaction_limit = Decimal(str(data["per_transaction_limit"]))
        if "approval_threshold" in data:
            policy.approval_threshold = Decimal(str(data["approval_threshold"]))
        if "daily_limit" in data:
            policy.daily_limit = Decimal(str(data["daily_limit"]))
        if "monthly_limit" in data:
            policy.monthly_limit = Decimal(str(data["monthly_limit"]))
        if "allowed_categories" in data and isinstance(data["allowed_categories"], list):
            policy.allowed_categories = data["allowed_categories"]

        policy.is_configured = True
        policy.configured_at = timezone.now()
        policy.save()
        return Response({
            "status": "CONSENT_UPDATED",
            "per_transaction_limit": float(policy.per_transaction_limit),
            "approval_threshold": float(policy.approval_threshold),
            "daily_limit": float(policy.daily_limit),
            "monthly_limit": float(policy.monthly_limit),
            "allowed_categories": policy.allowed_categories,
            "is_configured": policy.is_configured,
            "configured_at": policy.configured_at.isoformat() if policy.configured_at else None,
        })


class CommerceApproveView(APIView):
    """
    POST /api/agent-runtime/commerce/approve/
    Payload: { "intent_id": "<uuid>" }
    Approves the transaction approval card and executes the payment deterministically.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        intent_id = request.data.get("intent_id")
        if not intent_id:
            return Response({"error": "Field 'intent_id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .models import AgentUserConsentPolicy
        policy = AgentUserConsentPolicy.objects.filter(user=request.user).first()
        if not policy or not policy.is_configured:
            return Response({
                "error": "Payment authorization rules have not been configured yet. Please define your authorization limits and consent rules in the Policy tab before authorizing transactions.",
                "code": "RULES_NOT_CONFIGURED"
            }, status=status.HTTP_400_BAD_REQUEST)

        from .commerce_assistant import DeterministicCommerceTools

        try:
            res = DeterministicCommerceTools.executePayment(intent_id=intent_id, user=request.user)
            return Response(res, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Failed to execute payment approval: {e}", exc_info=True)
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommerceRejectView(APIView):
    """
    POST /api/agent-runtime/commerce/reject/
    Payload: { "intent_id": "<uuid>", "reason": str }
    Rejects the transaction approval card.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        intent_id = request.data.get("intent_id")
        if not intent_id:
            return Response({"error": "Field 'intent_id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .models import CommercePaymentIntent
        intent = CommercePaymentIntent.objects.filter(id=intent_id, user=request.user).first()
        if not intent:
            return Response({"error": "Payment intent not found."}, status=status.HTTP_404_NOT_FOUND)

        intent.status = CommercePaymentIntent.IntentStatus.REJECTED
        intent.reason = request.data.get("reason", "Rejected by user from approval card")
        intent.save(update_fields=["status", "reason"])

        return Response({
            "status": "REJECTED",
            "intent_id": str(intent.id),
            "message": "Transaction card rejected. Cart items preserved.",
        })


class AgentPaymentAuthorizationViewSet(viewsets.ModelViewSet):
    """
    CRUD and lifecycle operations for simulated agent payment authorizations.
    Inspired by consent-based pre-authorized payment models (UPI Reserve Pay concepts).
    """
    serializer_class = AgentPaymentAuthorizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return AgentPaymentAuthorization.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        auth = self.get_object()
        auth.status = AgentPaymentAuthorization.AuthStatus.PAUSED
        auth.save(update_fields=["status", "updated_at"])
        return Response({
            "status": "PAUSED",
            "auth_id": str(auth.id),
            "message": f"Payment authorization for agent '{auth.agent.name}' is now paused.",
        })

    @action(detail=True, methods=["post"])
    def resume(self, request, pk=None):
        auth = self.get_object()
        auth.status = AgentPaymentAuthorization.AuthStatus.ACTIVE
        auth.save(update_fields=["status", "updated_at"])
        return Response({
            "status": "ACTIVE",
            "auth_id": str(auth.id),
            "message": f"Payment authorization for agent '{auth.agent.name}' is now active.",
        })

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        auth = self.get_object()
        auth.status = AgentPaymentAuthorization.AuthStatus.REVOKED
        auth.save(update_fields=["status", "updated_at"])
        return Response({
            "status": "REVOKED",
            "auth_id": str(auth.id),
            "message": f"Payment authorization for agent '{auth.agent.name}' has been revoked.",
        })

    @action(detail=True, methods=["patch"])
    def limits(self, request, pk=None):
        auth = self.get_object()
        data = request.data

        if "max_transaction_amount" in data:
            auth.max_transaction_amount = Decimal(str(data["max_transaction_amount"]))
        if "daily_limit" in data:
            auth.daily_limit = Decimal(str(data["daily_limit"]))
        if "monthly_limit" in data:
            auth.monthly_limit = Decimal(str(data["monthly_limit"]))
        if "approval_threshold" in data:
            auth.approval_threshold = Decimal(str(data["approval_threshold"]))
        if "allowed_categories" in data and isinstance(data["allowed_categories"], list):
            auth.allowed_categories = data["allowed_categories"]
        if "blocked_categories" in data and isinstance(data["blocked_categories"], list):
            auth.blocked_categories = data["blocked_categories"]
        if "allowed_merchants" in data and isinstance(data["allowed_merchants"], list):
            auth.allowed_merchants = data["allowed_merchants"]
        if "blocked_merchants" in data and isinstance(data["blocked_merchants"], list):
            auth.blocked_merchants = data["blocked_merchants"]
        if "expires_at" in data:
            auth.expires_at = data["expires_at"]

        auth.save()
        serializer = self.get_serializer(auth)
        return Response({
            "status": "LIMITS_UPDATED",
            "authorization": serializer.data,
        })

    @action(detail=True, methods=["post"])
    def test_verify(self, request, pk=None):
        """
        Simulates verifying and consuming a payment against this authorization.
        Payload: { amount, merchant, category, idempotency_key, is_confirmation }
        """
        auth = self.get_object()
        amount_raw = request.data.get("amount", 0)
        try:
            amount = Decimal(str(amount_raw))
        except Exception:
            return Response({"error": "Invalid amount."}, status=status.HTTP_400_BAD_REQUEST)

        merchant = request.data.get("merchant", "RazorHub Direct")
        category = request.data.get("category", "electronics")
        idempotency_key = request.data.get("idempotency_key", f"test_{int(timezone.now().timestamp() * 1000)}")
        is_confirmation = bool(request.data.get("is_confirmation", False))

        from .authorization_service import AgentAuthorizationService
        res = AgentAuthorizationService.verify_and_consume(
            auth_id=str(auth.id),
            amount=amount,
            merchant=merchant,
            category=category,
            idempotency_key=idempotency_key,
            is_confirmation=is_confirmation,
        )
        return Response(res, status=status.HTTP_200_OK if res["decision"] != "BLOCKED" else status.HTTP_400_BAD_REQUEST)


# ── 16. AGENTIC BUSINESS BANKING VIEWS ───────────────────────────────────────
class BankingInsightsView(APIView):
    """
    GET /api/agent-runtime/banking/insights/
    Returns real-time treasury indicators, cash runway, burn rate, and 30-day forecast.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .banking_agents import InsightsAgentService
        metrics = InsightsAgentService.calculate_treasury_metrics()
        return Response(metrics)


class BankingReceivablesView(APIView):
    """
    GET & POST /api/agent-runtime/banking/receivables/
    Lists receivables and triggers autonomous debtor follow-up communications.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .banking_agents import ReceivablesAgentService
        invoices = ReceivablesAgentService.get_invoices()
        return Response(invoices)

    def post(self, request):
        action_type = request.data.get("action", "followup")
        invoice_id = request.data.get("invoice_id")
        if not invoice_id:
            return Response({"error": "Field 'invoice_id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .banking_agents import ReceivablesAgentService

        if action_type == "mark_paid":
            res = ReceivablesAgentService.mark_invoice_paid(invoice_id)
            return Response(res)

        channel = request.data.get("channel", "EMAIL")
        try:
            res = ReceivablesAgentService.execute_followup(invoice_id, channel)
            return Response(res)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BankingPayoutChatView(APIView):
    """
    POST /api/agent-runtime/banking/payouts/chat/
    Conversational payout agent interface.
    Accepts: { "prompt": "Pay Rahul ₹18,500 for invoice INV-204" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        prompt = request.data.get("prompt", "").strip()
        if not prompt:
            return Response({"error": "Field 'prompt' is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .banking_agents import PayoutAgentService
        res = PayoutAgentService.resolve_payout_request(prompt, user=request.user)
        return Response(res)


class BankingPayoutExecuteView(APIView):
    """
    POST /api/agent-runtime/banking/payouts/execute/
    Executes mock disbursement post-approval.
    Payload: { "invoice_id": "<uuid>" }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        invoice_id = request.data.get("invoice_id")
        if not invoice_id:
            return Response({"error": "Field 'invoice_id' is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .banking_agents import PayoutAgentService
        try:
            res = PayoutAgentService.execute_payout(invoice_id, user=request.user)
            return Response(res)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BankingBookkeepingView(APIView):
    """
    GET /api/agent-runtime/banking/bookkeeping/
    Returns categorized double-entry accounting ledger maintained by Bookkeeping Agent.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .banking_agents import BookkeepingAgentService
        entries = BookkeepingAgentService.get_entries()
        return Response(entries)


class BankingReportsView(APIView):
    """
    GET & POST /api/agent-runtime/banking/reports/
    Lists financial reports and triggers on-demand generation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .banking_agents import ReportingAgentService
        reports = ReportingAgentService.list_reports()
        return Response(reports)

    def post(self, request):
        report_type = request.data.get("report_type", "DAILY").upper()
        from .banking_agents import ReportingAgentService
        try:
            report = ReportingAgentService.generate_report(report_type)
            return Response(report)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class BankingReconciliationView(APIView):
    """
    GET /api/agent-runtime/banking/reconciliation/
    Returns automated bank feed vs payment gateway settlement reconciliation metrics.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from orders.models import Settlement
        delayed_settlements = Settlement.objects.filter(is_delayed=True)
        delayed_count = delayed_settlements.count()
        delayed_amount = sum((s.net_amount for s in delayed_settlements), Decimal("0.00"))

        total_settlements = Settlement.objects.count()
        processed_settlements = Settlement.objects.filter(status=Settlement.STATUS_PROCESSED)
        processed_count = processed_settlements.count()
        processed_amount = sum((s.net_amount for s in processed_settlements), Decimal("0.00"))

        status_val = "ATTENTION_REQUIRED" if delayed_count > 0 else "RECONCILED"
        feed_health_val = "DELAYED_SETTLEMENTS_DETECTED" if delayed_count > 0 else "OPTIMAL"

        return Response({
            "status": status_val,
            "last_reconciliation_time": timezone.now().isoformat(),
            "bank_account": "HDFC Current Account **** 9104",
            "bank_balance": float(processed_amount if processed_amount > Decimal("0.00") else Decimal("2845000.00")),
            "gateway_uncleared_settlement": float(delayed_amount if delayed_amount > Decimal("0.00") else Decimal("64200.00")),
            "matched_transactions_count": processed_count or 1420,
            "unmatched_items_count": delayed_count,
            "discrepancy_amount": float(delayed_amount),
            "feed_health": feed_health_val,
        })


# ── 17. AI-NATIVE COMMAND CENTER VIEWS ───────────────────────────────────────
class CommandCenterExecuteView(APIView):
    """
    POST /api/agent-runtime/command-center/execute/
    Executes natural-language prompt through deterministic 6-intent engine
    (QUERY, ANALYZE, ACTION, CREATE_AGENT, REPORT, ESCALATE) and returns
    structured 4-part transparency output.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        query = request.data.get("query", "").strip()
        if not query:
            return Response({"error": "Field 'query' is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .command_center import CommandCenterEngine
        try:
            res = CommandCenterEngine.execute(query, user=request.user)
            return Response(res)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CommandCenterApproveActionView(APIView):
    """
    POST /api/agent-runtime/command-center/approve/
    Executes approved action payload from an approval card.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        action_payload = request.data.get("action_payload")
        if not action_payload:
            return Response({"error": "Field 'action_payload' is required."}, status=status.HTTP_400_BAD_REQUEST)

        from .command_center import CommandCenterEngine
        try:
            res = CommandCenterEngine.execute_approved_action(action_payload, user=request.user)
            return Response(res)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ConnectorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing and inspecting integration connectors and testing capabilities.
    """
    queryset = Connector.objects.all()
    serializer_class = ConnectorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def list(self, request, *args, **kwargs):
        from .connectors.registry import ConnectorRegistry
        ConnectorRegistry.seed_default_connectors()
        return super().list(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def test_execute(self, request, pk=None):
        connector = self.get_object()
        capability = request.data.get("capability", "READ")
        action = request.data.get("action", "test")
        params = request.data.get("params", {})
        agent_id = request.data.get("agent_id")

        from .connectors.registry import ConnectorRegistry
        try:
            res = ConnectorRegistry.execute(
                connector_slug=connector.slug,
                capability=capability,
                action=action,
                params=params,
                agent_id=agent_id,
            )
            return Response({"success": True, "result": res})
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["get"])
    def executions(self, request, pk=None):
        connector = self.get_object()
        serializer = ConnectorExecutionSerializer(connector.executions.all()[:25], many=True)
        return Response(serializer.data)


# ── 18. OUTBOUND COMMUNICATION API VIEWS ──────────────────────────────────────
class CommunicationPreferencesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .communications.engine import CommunicationEngine
        pref = CommunicationEngine.get_or_create_preferences(request.user)
        return Response(CommunicationPreferenceSerializer(pref).data)

    def patch(self, request):
        from .communications.engine import CommunicationEngine
        pref = CommunicationEngine.get_or_create_preferences(request.user)
        data = request.data
        if "email_enabled" in data:
            pref.email_enabled = bool(data["email_enabled"])
        if "sms_enabled" in data:
            pref.sms_enabled = bool(data["sms_enabled"])
        if "whatsapp_enabled" in data:
            pref.whatsapp_enabled = bool(data["whatsapp_enabled"])
        if "in_app_enabled" in data:
            pref.in_app_enabled = bool(data["in_app_enabled"])
        if "telegram_enabled" in data:
            pref.telegram_enabled = bool(data["telegram_enabled"])
        if "telegram_chat_id" in data:
            pref.telegram_chat_id = str(data["telegram_chat_id"]).strip()
        if "is_opted_out_all" in data:
            pref.is_opted_out_all = bool(data["is_opted_out_all"])
        if "daily_frequency_limit" in data:
            pref.daily_frequency_limit = max(1, int(data["daily_frequency_limit"]))
        pref.save()
        return Response(CommunicationPreferenceSerializer(pref).data)


class CommunicationConsentsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        consents = CommunicationConsent.objects.filter(user=request.user)
        return Response(CommunicationConsentSerializer(consents, many=True).data)

    def post(self, request):
        purpose = request.data.get("purpose")
        is_granted = request.data.get("is_granted", True)
        if not purpose:
            return Response({"error": "Field 'purpose' is required."}, status=status.HTTP_400_BAD_REQUEST)

        consent, _ = CommunicationConsent.objects.get_or_create(
            user=request.user,
            purpose=purpose,
            defaults={"is_granted": is_granted},
        )
        if not is_granted:
            consent.revoke()
        else:
            consent.is_granted = True
            consent.revoked_at = None
            consent.save(update_fields=["is_granted", "revoked_at"])

        return Response(CommunicationConsentSerializer(consent).data)


class CommunicationSendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        channel = request.data.get("channel")
        template_name = request.data.get("template_name")
        immutable_data = request.data.get("immutable_data", {})
        recipient = request.data.get("recipient")
        agent_id = request.data.get("agent_id")
        personal_greeting = request.data.get("personal_greeting", "")

        if not channel or not template_name:
            return Response(
                {"error": "Fields 'channel' and 'template_name' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        agent = None
        if agent_id:
            agent = Agent.objects.filter(id=agent_id).first()

        from .communications.engine import CommunicationEngine
        try:
            res = CommunicationEngine.dispatch(
                user=request.user,
                channel=channel,
                template_name=template_name,
                immutable_data=immutable_data,
                recipient=recipient,
                agent=agent,
                personal_greeting=personal_greeting,
            )
            return Response(res)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class CommunicationEventsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        is_admin = getattr(request.user, "effective_role", "") == "admin"
        if is_admin and request.query_params.get("all") == "true":
            events = CommunicationEvent.objects.all()[:100]
        else:
            events = CommunicationEvent.objects.filter(user=request.user)[:100]
        return Response(CommunicationEventSerializer(events, many=True).data)


# ── 19. EXPLAINABLE FINANCIAL RISK ENGINE VIEWS ─────────────────────────────────
class RiskEvaluateView(APIView):
    """
    Evaluates transactional, behavioral, and environmental parameters
    to generate an explainable risk evaluation.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        inputs = request.data.get("inputs") or request.data
        include_llm = bool(request.data.get("include_llm_explanation", False))
        save_record = bool(request.data.get("save_record", True))

        agent_id = request.data.get("agent_id")
        agent = None
        if agent_id:
            agent = Agent.objects.filter(id=agent_id).first()

        try:
            result = FinancialRiskEngine.evaluate(inputs, include_llm_explanation=include_llm)

            if save_record:
                amount_val = inputs.get("transaction_amount")
                amount_dec = Decimal(str(amount_val)) if amount_val is not None else None
                record = FinancialRiskRecord.objects.create(
                    user=request.user,
                    agent=agent,
                    transaction_amount=amount_dec,
                    risk_score=result["riskScore"],
                    risk_level=result["riskLevel"],
                    reasons=result["reasons"],
                    critical_rule_triggered=result["critical_rule_triggered"],
                    rule_breakdown=result["rule_breakdown"],
                    inputs_snapshot=inputs,
                    explanation=result["explanation"],
                )
                result["record_id"] = str(record.id)

            return Response(result)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class RiskHistoryView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        records = FinancialRiskRecord.objects.filter(user=request.user)[:50]
        return Response(FinancialRiskRecordSerializer(records, many=True).data)









