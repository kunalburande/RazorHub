from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import (
    Agent,
    AgentStatus,
    ApprovalMode,
    RiskLevel,
    AgentTool,
    AgentPolicy,
    AgentTrigger,
    AgentVersion,
    PolicyType,
    ViolationAction,
    ExecutionStatus,
    StepType,
    StepStatus,
    ApprovalStatus,
    AuditEventType,
    AuditSeverity,
    AgentExecution,
    AgentExecutionStep,
    AgentApproval,
    AgentAuditLog,
)
from .runtime import AgentRuntime
from .registry import ToolRegistry

User = get_user_model()


class AgentRuntimeCoreTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="tester_agent",
            email="tester@example.com",
            password="testpassword123",
        )

        # Ensure tools are in database and registry
        self.echo_tool, _ = AgentTool.objects.get_or_create(
            name="echo",
            defaults={
                "description": "Echo tool for testing",
                "category": "system",
                "risk_level": RiskLevel.LOW,
                "parameters_schema": {
                    "type": "object",
                    "properties": {"message": {"type": "string"}},
                    "required": ["message"],
                },
            },
        )

        self.balance_tool, _ = AgentTool.objects.get_or_create(
            name="check_balance",
            defaults={
                "description": "Balance check tool",
                "category": "financial",
                "risk_level": RiskLevel.LOW,
                "parameters_schema": {
                    "type": "object",
                    "properties": {"account_id": {"type": "string"}},
                    "required": ["account_id"],
                },
            },
        )

        self.transfer_tool, _ = AgentTool.objects.get_or_create(
            name="transfer_funds",
            defaults={
                "description": "Fund transfer tool",
                "category": "financial",
                "risk_level": RiskLevel.HIGH,
                "parameters_schema": {
                    "type": "object",
                    "properties": {
                        "recipient_id": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["recipient_id", "amount"],
                },
            },
        )

    # ── TEST 1: AGENT CREATION ────────────────────────────────────────────────
    def test_agent_creation(self):
        agent = Agent.objects.create(
            name="Financial Treasury Agent",
            description="Manages automated treasury allocations",
            system_prompt="You are a treasury assistant. Always verify limits before execution.",
            status=AgentStatus.DRAFT,
            approval_mode=ApprovalMode.AUTO,
            risk_level=RiskLevel.MEDIUM,
            owner=self.user,
        )
        agent.tools.add(self.balance_tool, self.transfer_tool)

        # Attach version and trigger
        version = AgentVersion.objects.create(
            agent=agent,
            version_number=1,
            system_prompt=agent.system_prompt,
            change_summary="Initial version release",
        )
        trigger = AgentTrigger.objects.create(
            agent=agent,
            name="Manual User Prompt",
            trigger_type="USER_REQUEST",
        )

        self.assertIsNotNone(agent.id)
        self.assertEqual(agent.name, "Financial Treasury Agent")
        self.assertEqual(agent.status, AgentStatus.DRAFT)
        self.assertEqual(agent.approval_mode, ApprovalMode.AUTO)
        self.assertEqual(agent.tools.count(), 2)
        self.assertEqual(agent.versions.count(), 1)
        self.assertEqual(agent.triggers.count(), 1)

    # ── TEST 2: AGENT ACTIVATION ──────────────────────────────────────────────
    def test_agent_activation(self):
        agent = Agent.objects.create(
            name="Payment Bot",
            system_prompt="Processes payments",
            status=AgentStatus.DRAFT,
        )
        agent.tools.add(self.balance_tool)

        self.assertEqual(agent.status, AgentStatus.DRAFT)
        agent.activate()
        agent.refresh_from_db()
        self.assertEqual(agent.status, AgentStatus.ACTIVE)

        # Active agent executes request successfully
        execution = AgentRuntime.run("Check balance for acc_test99", agent=agent, user=self.user)
        self.assertEqual(execution.status, ExecutionStatus.COMPLETED)
        self.assertIn("150,000", execution.output_response)

    # ── TEST 3: AGENT PAUSING ─────────────────────────────────────────────────
    def test_agent_pausing(self):
        agent = Agent.objects.create(
            name="Suspended Assistant",
            system_prompt="Under maintenance",
            status=AgentStatus.ACTIVE,
        )
        agent.tools.add(self.balance_tool)

        agent.pause()
        agent.refresh_from_db()
        self.assertEqual(agent.status, AgentStatus.PAUSED)

        # Execution must fail when paused
        execution = AgentRuntime.run("Check balance for acc_123", agent=agent, user=self.user)
        self.assertEqual(execution.status, ExecutionStatus.FAILED)
        self.assertIn("cannot execute requests while in 'PAUSED' state", execution.error_message)

    # ── TEST 4: TOOL PERMISSIONS ──────────────────────────────────────────────
    def test_tool_permissions(self):
        agent = Agent.objects.create(
            name="Read-Only Info Bot",
            system_prompt="Read-only helper",
            status=AgentStatus.ACTIVE,
        )
        # Agent only has 'echo' permission
        agent.tools.add(self.echo_tool)

        # Attempt to run transfer request which requires 'transfer_funds'
        execution = AgentRuntime.run("Transfer 5000 to vendor_xyz", agent=agent, user=self.user)
        self.assertEqual(execution.status, ExecutionStatus.FAILED)
        self.assertIn("is not permitted for agent", execution.error_message.lower())

        # Step record reflects policy failure
        step = execution.steps.filter(step_type=StepType.POLICY_EVALUATION).first()
        self.assertIsNotNone(step)
        self.assertEqual(step.status, StepStatus.FAILED)

    # ── TEST 5: APPROVAL LOGIC ────────────────────────────────────────────────
    def test_approval_logic(self):
        # Scenario A: Agent configured with ALWAYS_CONFIRM
        agent = Agent.objects.create(
            name="Strict Approval Agent",
            system_prompt="Strict actions",
            status=AgentStatus.ACTIVE,
            approval_mode=ApprovalMode.ALWAYS_CONFIRM,
        )
        agent.tools.add(self.echo_tool)

        execution = AgentRuntime.run("Echo hello world", agent=agent, user=self.user)
        self.assertEqual(execution.status, ExecutionStatus.WAITING_APPROVAL)

        # Verify AgentApproval entity created
        approval = AgentApproval.objects.filter(execution=execution).first()
        self.assertIsNotNone(approval)
        self.assertEqual(approval.status, ApprovalStatus.PENDING)
        self.assertIn("ALWAYS_CONFIRM", approval.reason)

        # Approve and resume
        resumed = AgentRuntime.resume_after_approval(
            approval_id=str(approval.approval_id),
            decision="APPROVED",
            approver=self.user,
            notes="Approved by admin",
        )
        self.assertEqual(resumed.status, ExecutionStatus.COMPLETED)
        self.assertIn("hello world", resumed.output_response)

        # Scenario B: Policy requires approval based on threshold limit
        policy_agent = Agent.objects.create(
            name="Policy Guarded Agent",
            system_prompt="Guarded finance",
            status=AgentStatus.ACTIVE,
            approval_mode=ApprovalMode.AUTO,
        )
        policy_agent.tools.add(self.transfer_tool)

        limit_policy = AgentPolicy.objects.create(
            name="High Value Transfer Gate",
            policy_type=PolicyType.SPENDING_LIMIT,
            rules={"max_amount": 1000.0},
            violation_action=ViolationAction.REQUIRE_APPROVAL,
        )
        policy_agent.policies.add(limit_policy)

        # Request exceeding limit (2500 > 1000)
        exec_pol = AgentRuntime.run("Transfer 2500 to vendor_abc", agent=policy_agent, user=self.user)
        self.assertEqual(exec_pol.status, ExecutionStatus.WAITING_APPROVAL)

        appr_pol = AgentApproval.objects.filter(execution=exec_pol).first()
        self.assertIsNotNone(appr_pol)

        # Reject scenario
        cancelled = AgentRuntime.resume_after_approval(
            approval_id=str(appr_pol.approval_id),
            decision="REJECTED",
            approver=self.user,
            notes="Rejected: Too high amount",
        )
        self.assertEqual(cancelled.status, ExecutionStatus.CANCELLED)
        self.assertIn("rejected", cancelled.output_response.lower())

    # ── TEST 6: EXECUTION LOGGING & COMPLETE TRACE ────────────────────────────
    def test_execution_logging(self):
        agent = Agent.objects.create(
            name="Audited Payment Agent",
            system_prompt="Audited agent",
            status=AgentStatus.ACTIVE,
            approval_mode=ApprovalMode.AUTO,
        )
        agent.tools.add(self.balance_tool)

        execution = AgentRuntime.run("Check balance for acc_audit_01", agent=agent, user=self.user)
        self.assertEqual(execution.status, ExecutionStatus.COMPLETED)

        # Verify steps sequence
        steps = list(execution.steps.order_by("step_number").values_list("step_type", flat=True))
        expected_steps = [
            StepType.INTENT_PARSING,
            StepType.CONTEXT_GATHERING,
            StepType.PLAN_GENERATION,
            StepType.POLICY_EVALUATION,
            StepType.APPROVAL_CHECK,
            StepType.TOOL_EXECUTION,
            StepType.RESULT_VALIDATION,
        ]
        self.assertEqual(steps, expected_steps)

        # Verify audit logs created
        logs = AgentAuditLog.objects.filter(execution=execution)
        event_types = list(logs.values_list("event_type", flat=True))
        self.assertIn(AuditEventType.EXECUTION_START, event_types)
        self.assertIn(AuditEventType.INTENT_IDENTIFIED, event_types)
        self.assertIn(AuditEventType.TOOL_SELECTED, event_types)
        self.assertIn(AuditEventType.POLICY_CHECKED, event_types)
        self.assertIn(AuditEventType.TOOL_EXECUTED, event_types)
        self.assertIn(AuditEventType.RESULT_VALIDATED, event_types)
        self.assertIn(AuditEventType.EXECUTION_COMPLETED, event_types)

        # Verify execution trace array
        trace = execution.execution_trace
        self.assertIsInstance(trace, list)
        self.assertTrue(len(trace) >= 6)
        trace_stages = [t["stage"] for t in trace]
        self.assertIn("EXECUTION_START", trace_stages)
        self.assertIn("Intent identified", trace_stages)
        self.assertIn("Tool selected", trace_stages)
        self.assertIn("Policy checked", trace_stages)
        self.assertIn("Tool executed", trace_stages)
        self.assertIn("Result validated", trace_stages)
        self.assertIn("Execution completed", trace_stages)

    # ── TEST 7: FAILED EXECUTION ──────────────────────────────────────────────
    def test_failed_execution(self):
        agent = Agent.objects.create(
            name="Strict Cap Agent",
            system_prompt="Strict cap agent",
            status=AgentStatus.ACTIVE,
            approval_mode=ApprovalMode.AUTO,
        )
        agent.tools.add(self.transfer_tool)

        # Policy that hard-blocks transfers over 100
        hard_block_policy = AgentPolicy.objects.create(
            name="Hard Cap 100",
            policy_type=PolicyType.SPENDING_LIMIT,
            rules={"max_amount": 100.0},
            violation_action=ViolationAction.BLOCK,
        )
        agent.policies.add(hard_block_policy)

        execution = AgentRuntime.run("Transfer 5000 to vendor_hard_block", agent=agent, user=self.user)
        self.assertEqual(execution.status, ExecutionStatus.FAILED)
        self.assertIn("exceeds policy limit", execution.error_message)

        # Verify failure audit log
        err_log = AgentAuditLog.objects.filter(execution=execution, severity=AuditSeverity.ERROR).first()
        self.assertIsNotNone(err_log)
        violation_text = err_log.details.get("violation", "") or err_log.details.get("error", "")
        self.assertIn("exceeds policy limit", violation_text)
