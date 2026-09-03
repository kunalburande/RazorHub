from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404

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
)
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


class AgentToolViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentTool.objects.filter(is_enabled=True)
    serializer_class = AgentToolSerializer
    permission_classes = [permissions.IsAuthenticated]


class AgentPolicyViewSet(viewsets.ModelViewSet):
    queryset = AgentPolicy.objects.all()
    serializer_class = AgentPolicySerializer
    permission_classes = [permissions.IsAuthenticated]


class AgentExecutionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AgentExecution.objects.select_related("agent").prefetch_related("steps", "approvals").all()
    serializer_class = AgentExecutionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["get"])
    def trace(self, request, pk=None):
        execution = self.get_object()
        return Response({
            "execution_id": execution.execution_id,
            "status": execution.status,
            "trace": execution.execution_trace,
        })


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
    queryset = AgentAuditLog.objects.select_related("agent", "execution").all()
    serializer_class = AgentAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]


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
