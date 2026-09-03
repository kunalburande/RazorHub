from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AgentViewSet,
    AgentToolViewSet,
    AgentPolicyViewSet,
    AgentExecutionViewSet,
    AgentApprovalViewSet,
    AgentAuditLogViewSet,
    AgentGovernancePolicyViewSet,
    GovernanceDecisionViewSet,
    ExecuteAgentView,
)

router = DefaultRouter()
router.register(r"agents", AgentViewSet, basename="agent")
router.register(r"tools", AgentToolViewSet, basename="agent-tool")
router.register(r"policies", AgentPolicyViewSet, basename="agent-policy")
router.register(r"governance-policies", AgentGovernancePolicyViewSet, basename="agent-governance-policy")
router.register(r"governance-decisions", GovernanceDecisionViewSet, basename="governance-decision")
router.register(r"executions", AgentExecutionViewSet, basename="agent-execution")
router.register(r"approvals", AgentApprovalViewSet, basename="agent-approval")
router.register(r"audit-logs", AgentAuditLogViewSet, basename="agent-audit-log")

urlpatterns = [
    path("execute/", ExecuteAgentView.as_view(), name="agent-runtime-execute"),
    path("", include(router.urls)),
]
