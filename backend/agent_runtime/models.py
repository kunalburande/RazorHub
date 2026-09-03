import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError


class AgentStatus(models.TextChoices):
    DRAFT = "DRAFT", "Draft"
    ACTIVE = "ACTIVE", "Active"
    PAUSED = "PAUSED", "Paused"
    DISABLED = "DISABLED", "Disabled"
    FAILED = "FAILED", "Failed"


class ApprovalMode(models.TextChoices):
    AUTO = "AUTO", "Automatic Execution"
    REVIEW_REQUIRED = "REVIEW_REQUIRED", "Review Required on Risk/Policy"
    ALWAYS_CONFIRM = "ALWAYS_CONFIRM", "Always Require User Confirmation"
    BLOCKED = "BLOCKED", "Execution Prohibited"


class RiskLevel(models.TextChoices):
    LOW = "LOW", "Low Risk"
    MEDIUM = "MEDIUM", "Medium Risk"
    HIGH = "HIGH", "High Risk"
    CRITICAL = "CRITICAL", "Critical Risk"


class TriggerType(models.TextChoices):
    USER_REQUEST = "USER_REQUEST", "Direct User Prompt"
    EVENT = "EVENT", "System Event"
    SCHEDULE = "SCHEDULE", "Cron / Periodic Schedule"
    WEBHOOK = "WEBHOOK", "External Webhook"
    THRESHOLD = "THRESHOLD", "Metric Threshold Trigger"


class PolicyType(models.TextChoices):
    SPENDING_LIMIT = "SPENDING_LIMIT", "Financial Spending Limit"
    RATE_LIMIT = "RATE_LIMIT", "Execution Rate Limit"
    TOOL_ALLOWLIST = "TOOL_ALLOWLIST", "Allowed Tool Restraint"
    DATA_ACCESS = "DATA_ACCESS", "Data Boundary Policy"
    APPROVAL_RULE = "APPROVAL_RULE", "Mandatory Approval Condition"


class ViolationAction(models.TextChoices):
    BLOCK = "BLOCK", "Block Execution Immediately"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL", "Halt and Require User Approval"
    WARN_AND_LOG = "WARN_AND_LOG", "Permit Action but Log Warning"


class ExecutionStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    RUNNING = "RUNNING", "Running"
    WAITING_APPROVAL = "WAITING_APPROVAL", "Paused Waiting for Approval"
    COMPLETED = "COMPLETED", "Completed Successfully"
    FAILED = "FAILED", "Failed"
    CANCELLED = "CANCELLED", "Cancelled"


class StepType(models.TextChoices):
    INTENT_PARSING = "INTENT_PARSING", "Intent Identified"
    CONTEXT_GATHERING = "CONTEXT_GATHERING", "Context Gathered"
    PLAN_GENERATION = "PLAN_GENERATION", "Tool Selected / Plan Created"
    POLICY_EVALUATION = "POLICY_EVALUATION", "Policy Checked"
    APPROVAL_CHECK = "APPROVAL_CHECK", "Approval Required / Handled"
    TOOL_EXECUTION = "TOOL_EXECUTION", "Tool Executed"
    RESULT_VALIDATION = "RESULT_VALIDATION", "Result Validated"
    RESPONSE_GENERATION = "RESPONSE_GENERATION", "Response Generated"


class StepStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    SUCCESS = "SUCCESS", "Success"
    FAILED = "FAILED", "Failed"
    WAITING_APPROVAL = "WAITING_APPROVAL", "Waiting Approval"
    SKIPPED = "SKIPPED", "Skipped"


class ApprovalStatus(models.TextChoices):
    PENDING = "PENDING", "Pending Decision"
    APPROVED = "APPROVED", "Approved by User"
    REJECTED = "REJECTED", "Rejected by User"
    EXPIRED = "EXPIRED", "Approval Window Expired"


class AuditEventType(models.TextChoices):
    EXECUTION_START = "EXECUTION_START", "Execution Start"
    INTENT_IDENTIFIED = "INTENT_IDENTIFIED", "Intent Identified"
    TOOL_SELECTED = "TOOL_SELECTED", "Tool Selected"
    POLICY_CHECKED = "POLICY_CHECKED", "Policy Checked"
    APPROVAL_REQUIRED = "APPROVAL_REQUIRED", "Approval Required"
    USER_APPROVED = "USER_APPROVED", "User Approved"
    USER_REJECTED = "USER_REJECTED", "User Rejected"
    TOOL_EXECUTED = "TOOL_EXECUTED", "Tool Executed"
    RESULT_VALIDATED = "RESULT_VALIDATED", "Result Validated"
    EXECUTION_COMPLETED = "EXECUTION_COMPLETED", "Execution Completed"
    EXECUTION_FAILED = "EXECUTION_FAILED", "Execution Failed"


class AuditSeverity(models.TextChoices):
    INFO = "INFO", "Informational"
    WARNING = "WARNING", "Warning"
    ERROR = "ERROR", "Error"
    CRITICAL = "CRITICAL", "Critical Alert"


class MemoryType(models.TextChoices):
    CONVERSATION = "CONVERSATION", "Conversational Dialog"
    CONTEXT = "CONTEXT", "Session Working Context"
    PREFERENCE = "PREFERENCE", "User Preference"
    ENTITY = "ENTITY", "Discovered Entity"
    WORKING_STATE = "WORKING_STATE", "Runtime Scratchpad"


# ── 1. AGENT TOOL ─────────────────────────────────────────────────────────────
class AgentTool(models.Model):
    """
    Registered capability available to agents.
    All external mutations/API calls must go through registered tools.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, db_index=True)
    description = models.TextField()
    category = models.CharField(max_length=64, default="general", db_index=True)
    parameters_schema = models.JSONField(default=dict, help_text="JSON Schema for input parameters")
    required_permissions = models.JSONField(default=list, blank=True)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW)
    handler_path = models.CharField(max_length=255, blank=True, help_text="Dot-path to registered Python tool function")
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.category}]"


# ── 2. AGENT POLICY ───────────────────────────────────────────────────────────
class AgentPolicy(models.Model):
    """
    Governance and safety guardrails evaluated prior to tool execution.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150)
    policy_type = models.CharField(max_length=40, choices=PolicyType.choices, db_index=True)
    rules = models.JSONField(default=dict, help_text="JSON rule definitions e.g. max_amount, allowed_tools")
    violation_action = models.CharField(max_length=30, choices=ViolationAction.choices, default=ViolationAction.BLOCK)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Agent Policies"

    def __str__(self):
        return f"{self.name} ({self.get_policy_type_display()} -> {self.violation_action})"


# ── 3. AGENT DEFINITION ───────────────────────────────────────────────────────
class Agent(models.Model):
    """
    First-class generic agent configuration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=150, unique=True, db_index=True)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=AgentStatus.choices, default=AgentStatus.DRAFT, db_index=True)
    system_prompt = models.TextField(help_text="Core instructions, constraints, and identity for the agent")
    approval_mode = models.CharField(max_length=30, choices=ApprovalMode.choices, default=ApprovalMode.AUTO, db_index=True)
    risk_level = models.CharField(max_length=20, choices=RiskLevel.choices, default=RiskLevel.LOW)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="owned_agents")
    tools = models.ManyToManyField(AgentTool, blank=True, related_name="agents")
    policies = models.ManyToManyField(AgentPolicy, blank=True, related_name="agents")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.name} [{self.status}]"

    def activate(self):
        self.status = AgentStatus.ACTIVE
        self.save(update_fields=["status", "updated_at"])

    def pause(self):
        self.status = AgentStatus.PAUSED
        self.save(update_fields=["status", "updated_at"])

    def disable(self):
        self.status = AgentStatus.DISABLED
        self.save(update_fields=["status", "updated_at"])

    def fail(self, reason: str = ""):
        self.status = AgentStatus.FAILED
        if reason:
            self.metadata["failure_reason"] = reason
        self.save(update_fields=["status", "metadata", "updated_at"])

    # ── CamelCase Property Aliases for Universal API/Frontend Support ──
    @property
    def systemPrompt(self):
        return self.system_prompt

    @systemPrompt.setter
    def systemPrompt(self, value):
        self.system_prompt = value

    @property
    def approvalMode(self):
        return self.approval_mode

    @approvalMode.setter
    def approvalMode(self, value):
        self.approval_mode = value

    @property
    def riskLevel(self):
        return self.risk_level

    @riskLevel.setter
    def riskLevel(self, value):
        self.risk_level = value

    @property
    def createdAt(self):
        return self.created_at

    @property
    def updatedAt(self):
        return self.updated_at


# ── 4. AGENT VERSION ──────────────────────────────────────────────────────────
class AgentVersion(models.Model):
    """
    Immutable version snapshot of an agent prompt & configuration.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="versions")
    version_number = models.PositiveIntegerField(default=1)
    system_prompt = models.TextField()
    configuration = models.JSONField(default=dict, blank=True)
    change_summary = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("agent", "version_number")
        ordering = ["-version_number"]

    def __str__(self):
        return f"{self.agent.name} v{self.version_number}"


# ── 5. AGENT TRIGGER ──────────────────────────────────────────────────────────
class AgentTrigger(models.Model):
    """
    Invocation triggers mapped to an agent (prompts, webhooks, cron, events).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="triggers")
    name = models.CharField(max_length=120)
    trigger_type = models.CharField(max_length=30, choices=TriggerType.choices, default=TriggerType.USER_REQUEST)
    configuration = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.trigger_type}) -> {self.agent.name}"


# ── 6. AGENT EXECUTION ────────────────────────────────────────────────────────
class AgentExecution(models.Model):
    """
    A single end-to-end execution of an agent against a user request.
    Stores the full execution trace and outcome.
    """
    execution_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="executions")
    agent_version = models.ForeignKey(AgentVersion, on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    trigger = models.ForeignKey(AgentTrigger, on_delete=models.SET_NULL, null=True, blank=True)
    initial_request = models.TextField()
    status = models.CharField(max_length=30, choices=ExecutionStatus.choices, default=ExecutionStatus.PENDING, db_index=True)
    current_step = models.CharField(max_length=100, blank=True)
    output_response = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    execution_trace = models.JSONField(default=list, blank=True, help_text="Chronological trace of runtime stages")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"Exec {str(self.execution_id)[:8]} - {self.agent.name} [{self.status}]"

    def append_trace(self, stage: str, message: str, meta: dict = None):
        """Append an immutable trace entry to execution_trace."""
        import datetime
        entry = {
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "stage": stage,
            "message": message,
            "meta": meta or {},
        }
        self.execution_trace.append(entry)
        self.current_step = stage
        self.save(update_fields=["execution_trace", "current_step"])


# ── 7. AGENT EXECUTION STEP ───────────────────────────────────────────────────
class AgentExecutionStep(models.Model):
    """
    Granular discrete step within an agent execution.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    execution = models.ForeignKey(AgentExecution, on_delete=models.CASCADE, related_name="steps")
    step_number = models.PositiveIntegerField()
    step_type = models.CharField(max_length=40, choices=StepType.choices)
    status = models.CharField(max_length=30, choices=StepStatus.choices, default=StepStatus.PENDING)
    input_payload = models.JSONField(default=dict, blank=True)
    output_payload = models.JSONField(default=dict, blank=True)
    duration_ms = models.PositiveIntegerField(default=0)
    error_detail = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["step_number"]
        unique_together = ("execution", "step_number")

    def __str__(self):
        return f"Step {self.step_number}: {self.step_type} ({self.status})"


class GovernanceDecision(models.TextChoices):
    ALLOW = "ALLOW", "Allow"
    ALLOW_WITH_CONFIRMATION = "ALLOW_WITH_CONFIRMATION", "Allow with Human Confirmation"
    DENY = "DENY", "Deny"
    ESCALATE = "ESCALATE", "Escalate to Management"


# ── 8. AGENT APPROVAL ─────────────────────────────────────────────────────────
class AgentApproval(models.Model):
    """
    Human-in-the-loop approval record for actions requiring user confirmation.
    """
    approval_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="approvals", null=True, blank=True)
    execution = models.ForeignKey(AgentExecution, on_delete=models.CASCADE, related_name="approvals", null=True, blank=True)
    step = models.ForeignKey(AgentExecutionStep, on_delete=models.SET_NULL, null=True, blank=True, related_name="approvals")
    requested_action = models.CharField(max_length=150)
    action_payload = models.JSONField(default=dict)
    reason = models.TextField(help_text="Policy justification or risk explanation for approval")
    status = models.CharField(max_length=30, choices=ApprovalStatus.choices, default=ApprovalStatus.PENDING, db_index=True)
    approver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    merchant = models.CharField(max_length=150, blank=True)
    risk_score = models.FloatField(default=0.0)
    policy_triggered = models.CharField(max_length=150, blank=True)
    requires_double_confirmation = models.BooleanField(default=False)
    is_double_confirmed = models.BooleanField(default=False)
    decision_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Approval {str(self.approval_id)[:8]}: {self.requested_action} [{self.status}]"


# ── 8B. AGENT GOVERNANCE POLICY ───────────────────────────────────────────────
class AgentGovernancePolicy(models.Model):
    """
    Configurable spending policies, velocity limits, merchant/category allow/blocklists,
    and double confirmation requirements for agents.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.OneToOneField(Agent, on_delete=models.CASCADE, related_name="governance_policy", null=True, blank=True)
    name = models.CharField(max_length=150, default="Standard Agent Governance Policy")
    max_transaction_amount = models.DecimalField(max_digits=12, decimal_places=2, default=5000.00)
    daily_spend_limit = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)
    weekly_spend_limit = models.DecimalField(max_digits=12, decimal_places=2, default=40000.00)
    monthly_spend_limit = models.DecimalField(max_digits=12, decimal_places=2, default=150000.00)
    require_approval_above = models.DecimalField(max_digits=12, decimal_places=2, default=2000.00)
    allowed_categories = models.JSONField(default=list, blank=True, help_text="Allowed categories, empty allows all non-blocked")
    blocked_categories = models.JSONField(default=list, blank=True, help_text="Blocked categories e.g. electronics, cash, unknown")
    allowed_merchants = models.JSONField(default=list, blank=True, help_text="Allowed merchants, empty allows all non-blocked")
    blocked_merchants = models.JSONField(default=list, blank=True)
    allowed_payment_methods = models.JSONField(default=list, blank=True)
    allowed_hours = models.JSONField(default=dict, blank=True, help_text="e.g. {'start': '00:00', 'end': '23:59'}")
    require_human_approval = models.BooleanField(default=False)
    require_double_confirmation = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Max: ₹{self.max_transaction_amount})"

    # ── CamelCase Property Aliases for Policy Attributes ──
    @property
    def maxTransactionAmount(self):
        return self.max_transaction_amount

    @maxTransactionAmount.setter
    def maxTransactionAmount(self, value):
        self.max_transaction_amount = value

    @property
    def dailySpendLimit(self):
        return self.daily_spend_limit

    @dailySpendLimit.setter
    def dailySpendLimit(self, value):
        self.daily_spend_limit = value

    @property
    def weeklySpendLimit(self):
        return self.weekly_spend_limit

    @weeklySpendLimit.setter
    def weeklySpendLimit(self, value):
        self.weekly_spend_limit = value

    @property
    def monthlySpendLimit(self):
        return self.monthly_spend_limit

    @monthlySpendLimit.setter
    def monthlySpendLimit(self, value):
        self.monthly_spend_limit = value

    @property
    def requireApprovalAbove(self):
        return self.require_approval_above

    @requireApprovalAbove.setter
    def requireApprovalAbove(self, value):
        self.require_approval_above = value

    @property
    def automaticApprovalBelow(self):
        return self.require_approval_above

    @property
    def humanApprovalAbove(self):
        return self.require_approval_above

    @property
    def allowedCategories(self):
        return self.allowed_categories

    @allowedCategories.setter
    def allowedCategories(self, value):
        self.allowed_categories = value

    @property
    def blockedCategories(self):
        return self.blocked_categories

    @blockedCategories.setter
    def blockedCategories(self, value):
        self.blocked_categories = value

    @property
    def allowedMerchants(self):
        return self.allowed_merchants

    @allowedMerchants.setter
    def allowedMerchants(self, value):
        self.allowed_merchants = value

    @property
    def blockedMerchants(self):
        return self.blocked_merchants

    @blockedMerchants.setter
    def blockedMerchants(self, value):
        self.blocked_merchants = value

    @property
    def allowedPaymentMethods(self):
        return self.allowed_payment_methods

    @allowedPaymentMethods.setter
    def allowedPaymentMethods(self, value):
        self.allowed_payment_methods = value

    @property
    def allowedHours(self):
        return self.allowed_hours

    @allowedHours.setter
    def allowedHours(self, value):
        self.allowed_hours = value

    @property
    def requireHumanApproval(self):
        return self.require_human_approval

    @requireHumanApproval.setter
    def requireHumanApproval(self, value):
        self.require_human_approval = value

    @property
    def requireDoubleConfirmation(self):
        return self.require_double_confirmation

    @requireDoubleConfirmation.setter
    def requireDoubleConfirmation(self, value):
        self.require_double_confirmation = value



# ── 8C. GOVERNANCE DECISION RECORD ────────────────────────────────────────────
class GovernanceDecisionRecord(models.Model):
    """
    Forensic record of all governance decisions (ALLOW, ALLOW_WITH_CONFIRMATION, DENY, ESCALATE).
    Every DENY and ESCALATE decision is permanently preserved here.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="governance_records")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    decision = models.CharField(max_length=40, choices=GovernanceDecision.choices, db_index=True)
    action = models.CharField(max_length=150)
    amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=10, default="INR")
    merchant = models.CharField(max_length=150, blank=True)
    reason = models.TextField()
    risk_score = models.FloatField(default=0.0)
    policy_triggered = models.CharField(max_length=150, blank=True)
    raw_prompt = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.decision}] {self.action} (₹{self.amount or 0}) - {self.reason[:50]}"


# ── 9. AGENT AUDIT LOG ────────────────────────────────────────────────────────
class AgentAuditLog(models.Model):
    """
    Comprehensive immutable audit trail of all runtime decisions, security checks, and tool calls.
    """
    audit_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    execution = models.ForeignKey(AgentExecution, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    event_type = models.CharField(max_length=50, choices=AuditEventType.choices, db_index=True)
    severity = models.CharField(max_length=20, choices=AuditSeverity.choices, default=AuditSeverity.INFO)
    actor_type = models.CharField(max_length=30, default="SYSTEM")
    actor_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(default=dict, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.severity}] {self.event_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"


# ── 10. AGENT MEMORY ──────────────────────────────────────────────────────────
class AgentMemory(models.Model):
    """
    Persistent contextual memory for agent recall across sessions and interactions.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="memories")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_id = models.CharField(max_length=128, blank=True, db_index=True)
    memory_type = models.CharField(max_length=30, choices=MemoryType.choices, default=MemoryType.CONVERSATION)
    key = models.CharField(max_length=150, db_index=True)
    value = models.JSONField(default=dict)
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["agent", "session_id", "key"]),
            models.Index(fields=["agent", "user", "key"]),
        ]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.agent.name}: {self.key} ({self.memory_type})"
