from rest_framework import serializers
from .models import (
    Agent,
    AgentVersion,
    AgentTool,
    AgentTrigger,
    AgentPolicy,
    AgentExecution,
    AgentExecutionStep,
    AgentApproval,
    AgentAuditLog,
    AgentMemory,
    AgentGovernancePolicy,
    GovernanceDecisionRecord,
    RefundAnomalyRecord,
    AgentPaymentAuthorization,
    AgentAuthorizationLedger,
    Connector,
    ConnectorCapability,
    ConnectorCredential,
    ConnectorExecution,
    CommunicationConsent,
    CommunicationPreference,
    CommunicationEvent,
    FinancialRiskRecord,
)
from decimal import Decimal







class AgentToolSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTool
        fields = "__all__"


class AgentPolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentPolicy
        fields = "__all__"


class AgentTriggerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentTrigger
        fields = "__all__"


class AgentVersionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentVersion
        fields = "__all__"


class AgentGovernancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentGovernancePolicy
        fields = "__all__"


class ConnectorCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorCapability
        fields = "__all__"


class ConnectorCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConnectorCredential
        fields = ["id", "connector", "name", "auth_type", "is_valid", "last_verified_at", "created_at"]


class ConnectorExecutionSerializer(serializers.ModelSerializer):
    connector_name = serializers.CharField(source="connector.name", read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)

    class Meta:
        model = ConnectorExecution
        fields = "__all__"


class ConnectorSerializer(serializers.ModelSerializer):
    capabilities = ConnectorCapabilitySerializer(many=True, read_only=True)
    active_agents_count = serializers.SerializerMethodField()

    class Meta:
        model = Connector
        fields = "__all__"

    def get_active_agents_count(self, obj):
        return obj.agents.count()


class AgentSerializer(serializers.ModelSerializer):
    tools = AgentToolSerializer(many=True, read_only=True)
    tool_ids = serializers.PrimaryKeyRelatedField(
        queryset=AgentTool.objects.all(),
        many=True,
        write_only=True,
        source="tools",
        required=False,
    )
    policies = AgentPolicySerializer(many=True, read_only=True)
    policy_ids = serializers.PrimaryKeyRelatedField(
        queryset=AgentPolicy.objects.all(),
        many=True,
        write_only=True,
        source="policies",
        required=False,
    )
    connectors = ConnectorSerializer(many=True, read_only=True)
    connector_ids = serializers.PrimaryKeyRelatedField(
        queryset=Connector.objects.all(),
        many=True,
        write_only=True,
        source="connectors",
        required=False,
    )
    triggers = AgentTriggerSerializer(many=True, read_only=True)
    governance_policy = AgentGovernancePolicySerializer(read_only=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "name",
            "description",
            "status",
            "system_prompt",
            "approval_mode",
            "risk_level",
            "tools",
            "tool_ids",
            "policies",
            "policy_ids",
            "connectors",
            "connector_ids",
            "triggers",
            "governance_policy",
            "metadata",
            "created_at",
            "updated_at",
        ]




class AgentExecutionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentExecutionStep
        fields = "__all__"


class AgentApprovalSerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()
    agent_id = serializers.SerializerMethodField()
    action = serializers.CharField(source="requested_action", read_only=True)

    class Meta:
        model = AgentApproval
        fields = [
            "approval_id",
            "execution",
            "step",
            "agent_id",
            "agent_name",
            "action",
            "requested_action",
            "action_payload",
            "reason",
            "status",
            "approver",
            "amount",
            "merchant",
            "risk_score",
            "policy_triggered",
            "requires_double_confirmation",
            "is_double_confirmed",
            "decision_notes",
            "created_at",
            "decided_at",
            "expires_at",
        ]

    def get_agent_name(self, obj):
        if obj.agent:
            return obj.agent.name
        if obj.execution and obj.execution.agent:
            return obj.execution.agent.name
        return "Autonomous Agent"

    def get_agent_id(self, obj):
        if obj.agent:
            return str(obj.agent.id)
        if obj.execution and obj.execution.agent:
            return str(obj.execution.agent.id)
        return None





class GovernanceDecisionRecordSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.name", read_only=True)

    class Meta:
        model = GovernanceDecisionRecord
        fields = "__all__"


class AgentExecutionSerializer(serializers.ModelSerializer):
    steps = AgentExecutionStepSerializer(many=True, read_only=True)
    approvals = AgentApprovalSerializer(many=True, read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)

    class Meta:
        model = AgentExecution
        fields = [
            "execution_id",
            "agent",
            "agent_name",
            "initial_request",
            "status",
            "current_step",
            "output_response",
            "error_message",
            "execution_trace",
            "steps",
            "approvals",
            "started_at",
            "completed_at",
        ]


class AgentAuditLogSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.name", read_only=True)

    class Meta:
        model = AgentAuditLog
        fields = "__all__"


class AgentMemorySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentMemory
        fields = "__all__"


class RefundAnomalyRecordSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.name", read_only=True)

    class Meta:
        model = RefundAnomalyRecord
        fields = "__all__"


class AgentAuthorizationLedgerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentAuthorizationLedger
        fields = "__all__"


class AgentPaymentAuthorizationSerializer(serializers.ModelSerializer):
    agent_name = serializers.CharField(source="agent.name", read_only=True)
    user_email = serializers.CharField(source="user.email", read_only=True)
    remaining_today = serializers.SerializerMethodField()
    remaining_month = serializers.SerializerMethodField()

    class Meta:
        model = AgentPaymentAuthorization
        fields = [
            "id",
            "user",
            "user_email",
            "agent",
            "agent_name",
            "max_transaction_amount",
            "daily_limit",
            "monthly_limit",
            "used_today",
            "used_this_month",
            "remaining_today",
            "remaining_month",
            "allowed_categories",
            "blocked_categories",
            "allowed_merchants",
            "blocked_merchants",
            "approval_threshold",
            "status",
            "expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["user", "used_today", "used_this_month", "created_at", "updated_at"]

    def get_remaining_today(self, obj):
        return float(max(Decimal("0.00"), obj.daily_limit - obj.used_today))

    def get_remaining_month(self, obj):
        return float(max(Decimal("0.00"), obj.monthly_limit - obj.used_this_month))


class CommunicationConsentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = CommunicationConsent
        fields = "__all__"
        read_only_fields = ["user", "granted_at"]


class CommunicationPreferenceSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = CommunicationPreference
        fields = "__all__"
        read_only_fields = ["user", "updated_at"]


class CommunicationEventSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)

    class Meta:
        model = CommunicationEvent
        fields = "__all__"


class FinancialRiskRecordSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)

    class Meta:
        model = FinancialRiskRecord
        fields = "__all__"


class AgentExecutionStepSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentExecutionStep
        fields = [
            "id",
            "step_number",
            "step_type",
            "status",
            "input_payload",
            "output_payload",
            "duration_ms",
            "error_detail",
            "created_at",
        ]


class AgentExecutionSerializer(serializers.ModelSerializer):
    executionId = serializers.UUIDField(source="execution_id", read_only=True)
    agentId = serializers.PrimaryKeyRelatedField(source="agent", read_only=True)
    agent_name = serializers.CharField(source="agent.name", read_only=True)
    userId = serializers.CharField(source="user_id", read_only=True)
    timestamp = serializers.DateTimeField(source="started_at", read_only=True)
    input = serializers.JSONField(source="input_payload", read_only=True)
    context = serializers.JSONField(source="context_data", read_only=True)
    toolsSelected = serializers.JSONField(source="tools_selected", read_only=True)
    toolInputs = serializers.JSONField(source="tool_inputs", read_only=True)
    policyChecks = serializers.JSONField(source="policy_checks", read_only=True)
    riskChecks = serializers.JSONField(source="risk_checks", read_only=True)
    approvalRequest = serializers.JSONField(source="approval_request", read_only=True)
    approvalResponse = serializers.JSONField(source="approval_response", read_only=True)
    toolResults = serializers.JSONField(source="tool_results", read_only=True)
    finalAction = serializers.CharField(source="final_action", read_only=True)
    error = serializers.CharField(source="error_message", read_only=True)
    duration = serializers.IntegerField(source="duration_ms", read_only=True)
    model = serializers.CharField(source="model_name", read_only=True)
    tokenUsage = serializers.JSONField(source="token_usage", read_only=True)
    timeline = serializers.JSONField(read_only=True)
    steps = AgentExecutionStepSerializer(many=True, read_only=True)

    class Meta:
        model = AgentExecution
        fields = [
            "execution_id",
            "executionId",
            "agent",
            "agentId",
            "agent_name",
            "user",
            "userId",
            "initial_request",
            "intent",
            "input",
            "context",
            "toolsSelected",
            "toolInputs",
            "policyChecks",
            "riskChecks",
            "approvalRequest",
            "approvalResponse",
            "toolResults",
            "finalAction",
            "status",
            "error",
            "duration",
            "duration_ms",
            "model",
            "model_name",
            "tokenUsage",
            "token_usage",
            "timeline",
            "output_response",
            "error_message",
            "steps",
            "timestamp",
            "started_at",
            "completed_at",
        ]





