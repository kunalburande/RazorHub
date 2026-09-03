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
)


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
    triggers = AgentTriggerSerializer(many=True, read_only=True)

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
            "triggers",
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



class AgentGovernancePolicySerializer(serializers.ModelSerializer):
    class Meta:
        model = AgentGovernancePolicy
        fields = "__all__"


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
