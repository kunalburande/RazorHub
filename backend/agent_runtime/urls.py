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
    BlueprintGenerateView,
    BlueprintActivateView,
    RefundSpikeRunView,
    RefundSpikeLatestView,
    RefundSpikeHistoryView,
    RefundSpikeScheduleView,
    CommerceChatView,
    CommerceConsentView,
    CommerceApproveView,
    CommerceRejectView,
    AgentPaymentAuthorizationViewSet,
    BankingInsightsView,
    BankingReceivablesView,
    BankingPayoutChatView,
    BankingPayoutExecuteView,
    BankingBookkeepingView,
    BankingReportsView,
    BankingReconciliationView,
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
router.register(r"authorizations", AgentPaymentAuthorizationViewSet, basename="agent-payment-authorization")


urlpatterns = [
    path("execute/", ExecuteAgentView.as_view(), name="agent-runtime-execute"),
    path("blueprint/generate/", BlueprintGenerateView.as_view(), name="agent-blueprint-generate"),
    path("blueprint/activate/", BlueprintActivateView.as_view(), name="agent-blueprint-activate"),
    path("refund-spike-analyzer/run/", RefundSpikeRunView.as_view(), name="refund-spike-run"),
    path("refund-spike-analyzer/latest/", RefundSpikeLatestView.as_view(), name="refund-spike-latest"),
    path("refund-spike-analyzer/history/", RefundSpikeHistoryView.as_view(), name="refund-spike-history"),
    path("refund-spike-analyzer/schedule/", RefundSpikeScheduleView.as_view(), name="refund-spike-schedule"),
    path("commerce/chat/", CommerceChatView.as_view(), name="commerce-chat"),
    path("commerce/consent/", CommerceConsentView.as_view(), name="commerce-consent"),
    path("commerce/approve/", CommerceApproveView.as_view(), name="commerce-approve"),
    path("commerce/reject/", CommerceRejectView.as_view(), name="commerce-reject"),
    path("banking/insights/", BankingInsightsView.as_view(), name="banking-insights"),
    path("banking/receivables/", BankingReceivablesView.as_view(), name="banking-receivables"),
    path("banking/payouts/chat/", BankingPayoutChatView.as_view(), name="banking-payouts-chat"),
    path("banking/payouts/execute/", BankingPayoutExecuteView.as_view(), name="banking-payouts-execute"),
    path("banking/bookkeeping/", BankingBookkeepingView.as_view(), name="banking-bookkeeping"),
    path("banking/reports/", BankingReportsView.as_view(), name="banking-reports"),
    path("banking/reconciliation/", BankingReconciliationView.as_view(), name="banking-reconciliation"),
    path("", include(router.urls)),
]




