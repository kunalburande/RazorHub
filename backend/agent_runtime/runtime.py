import time
import logging
from typing import Optional, Dict, Any
from django.utils import timezone

from .models import (
    Agent,
    AgentStatus,
    ApprovalMode,
    ExecutionStatus,
    StepType,
    StepStatus,
    ApprovalStatus,
    AuditEventType,
    AuditSeverity,
    AgentExecution,
    AgentExecutionStep,
    AgentAuditLog,
    AgentMemory,
)
from .registry import ToolRegistry
from .policies import PolicyEngine
from .approvals import ApprovalManager

logger = logging.getLogger(__name__)


class AgentRuntime:
    """
    Foundational deterministic Agent Runtime.
    Implements the standard pipeline:
    user request
    → intent parsing
    → agent selection
    → context gathering
    → plan generation
    → policy evaluation
    → approval check
    → tool execution
    → result validation
    → audit logging
    → response
    """

    @classmethod
    def run(
        cls,
        request_text: str,
        agent: Optional[Agent] = None,
        user=None,
        session_id: str = "",
        context: Optional[Dict[str, Any]] = None,
        trigger=None,
    ) -> AgentExecution:
        """
        Execute an agent against a user request.
        Produces full execution trace and discrete execution steps.
        """
        context = context or {}

        # ── STAGE 1: EXECUTION START ──
        # If no agent provided, get or create a default active agent
        if not agent:
            agent = Agent.objects.filter(status=AgentStatus.ACTIVE).first()
            if not agent:
                agent = Agent.objects.create(
                    name="Default Commerce Assistant",
                    description="Autonomous standard assistant",
                    system_prompt="You are a helpful commerce assistant. Use registered tools to assist users.",
                    status=AgentStatus.ACTIVE,
                    approval_mode=ApprovalMode.AUTO,
                )

        execution = AgentExecution.objects.create(
            agent=agent,
            user=user if getattr(user, "is_authenticated", False) else None,
            trigger=trigger,
            initial_request=request_text,
            status=ExecutionStatus.RUNNING,
            current_step="EXECUTION_START",
        )

        cls._log_audit(
            event_type=AuditEventType.EXECUTION_START,
            agent=agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details={"request": request_text, "session_id": session_id},
        )
        execution.append_trace("EXECUTION_START", "Execution initialized")

        # ── STAGE 2: AGENT STATUS CHECK ──
        if agent.status != AgentStatus.ACTIVE:
            err = f"Agent '{agent.name}' cannot execute requests while in '{agent.status}' state."
            return cls._fail_execution(execution, err, stage="AGENT_INACTIVE")

        # ── STAGE 3: INTENT PARSING ──
        step_num = 1
        t0 = time.time()
        intent_info = cls._parse_intent(request_text, agent)
        duration_ms = int((time.time() - t0) * 1000)

        step_intent = AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.INTENT_PARSING,
            status=StepStatus.SUCCESS,
            input_payload={"request": request_text},
            output_payload=intent_info,
            duration_ms=duration_ms,
        )
        cls._log_audit(
            event_type=AuditEventType.INTENT_IDENTIFIED,
            agent=agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details=intent_info,
        )
        execution.append_trace("Intent identified", f"Identified intent '{intent_info.get('intent')}'", intent_info)

        # ── STAGE 4: CONTEXT GATHERING ──
        step_num += 1
        t0 = time.time()
        working_context = cls._gather_context(agent, user, session_id, context)
        working_context["execution_id"] = str(execution.execution_id)
        duration_ms = int((time.time() - t0) * 1000)

        AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.CONTEXT_GATHERING,
            status=StepStatus.SUCCESS,
            input_payload={"session_id": session_id},
            output_payload=working_context,
            duration_ms=duration_ms,
        )
        execution.append_trace("Context gathered", "Gathered session and memory context")

        # ── STAGE 5: PLAN GENERATION & TOOL SELECTION ──
        step_num += 1
        t0 = time.time()
        plan = cls._generate_plan(request_text, intent_info, agent, working_context)
        duration_ms = int((time.time() - t0) * 1000)

        step_plan = AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.PLAN_GENERATION,
            status=StepStatus.SUCCESS,
            input_payload={"intent": intent_info},
            output_payload=plan,
            duration_ms=duration_ms,
        )

        tool_name = plan.get("tool_name")
        arguments = plan.get("arguments", {})

        cls._log_audit(
            event_type=AuditEventType.TOOL_SELECTED,
            agent=agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details={"tool_name": tool_name, "arguments": arguments},
        )
        execution.append_trace("Tool selected", f"Selected tool '{tool_name}'", {"tool": tool_name, "args": arguments})

        # If conversational or no tool needed, complete directly
        if not tool_name:
            final_res = plan.get("direct_response", "Request processed.")
            return cls._complete_execution(execution, final_res)

        # ── STAGE 6: POLICY EVALUATION & GOVERNANCE FIREWALL ──
        step_num += 1
        t0 = time.time()
        
        # 1. Base Policy Engine check
        policy_res = PolicyEngine.evaluate(agent, tool_name, arguments, working_context)
        
        # 2. Transaction Governance & Firewall Layer evaluation
        from .governance import TransactionGovernanceFirewall, GovernanceDecision
        gov_res = TransactionGovernanceFirewall.evaluate(
            agent=agent,
            tool_name=tool_name,
            arguments=arguments,
            raw_prompt=request_text,
            user=user,
            context={"execution": execution, **working_context},
        )

        duration_ms = int((time.time() - t0) * 1000)

        is_allowed = policy_res.allowed and (gov_res.decision in [GovernanceDecision.ALLOW, GovernanceDecision.ALLOW_WITH_CONFIRMATION])

        step_policy = AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.POLICY_EVALUATION,
            status=StepStatus.SUCCESS if is_allowed else StepStatus.FAILED,
            input_payload={"tool": tool_name, "arguments": arguments},
            output_payload={
                "allowed": is_allowed,
                "governance_decision": gov_res.decision,
                "risk_score": gov_res.risk_score,
                "reason": gov_res.reason or policy_res.reason,
            },
            duration_ms=duration_ms,
            error_detail=gov_res.reason if not is_allowed else "",
        )

        if not is_allowed:
            failure_reason = policy_res.reason if not policy_res.allowed else gov_res.reason
            execution.append_trace("Firewall blocked", failure_reason, {"decision": gov_res.decision, "policy": gov_res.policy_triggered})
            return cls._fail_execution(
                execution,
                f"Firewall policy violation: {failure_reason}",
                stage="GOVERNANCE_BLOCKED",
                details={"violation": failure_reason, "policy": gov_res.policy_triggered, "decision": gov_res.decision},
            )

        cls._log_audit(
            event_type=AuditEventType.POLICY_CHECKED,
            agent=agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details={"decision": gov_res.decision, "reason": gov_res.reason or policy_res.reason},
        )
        execution.append_trace("Policy checked", f"Firewall passed: {gov_res.decision}", {"risk_score": gov_res.risk_score})

        # Check if Governance Firewall required confirmation
        if gov_res.decision == GovernanceDecision.ALLOW_WITH_CONFIRMATION:
            step_num += 1
            step_approval = AgentExecutionStep.objects.create(
                execution=execution,
                step_number=step_num,
                step_type=StepType.APPROVAL_CHECK,
                status=StepStatus.WAITING_APPROVAL,
                input_payload={"decision": gov_res.decision, "requires_double": gov_res.requires_double_confirmation},
                output_payload={"needs_approval": True, "reason": gov_res.reason},
                duration_ms=duration_ms,
            )
            if gov_res.approval_id:
                try:
                    from .models import AgentApproval
                    appr_obj = AgentApproval.objects.get(approval_id=gov_res.approval_id)
                    appr_obj.execution = execution
                    appr_obj.step = step_approval
                    appr_obj.save(update_fields=["execution", "step"])
                except Exception:
                    pass

            execution.status = ExecutionStatus.WAITING_APPROVAL
            execution.output_response = f"Action requires confirmation: {gov_res.reason}"
            execution.save(update_fields=["status", "output_response"])
            execution.append_trace(
                "Approval required",
                f"Execution paused awaiting approval: {gov_res.reason}",
                {"approval_id": gov_res.approval_id, "double_confirmation": gov_res.requires_double_confirmation},
            )
            return execution

        # ── STAGE 7: APPROVAL CHECK ──
        step_num += 1
        t0 = time.time()
        needs_approval, approval_reason = ApprovalManager.requires_approval(agent, tool_name, arguments, policy_res)
        duration_ms = int((time.time() - t0) * 1000)

        step_approval = AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.APPROVAL_CHECK,
            status=StepStatus.WAITING_APPROVAL if needs_approval else StepStatus.SUCCESS,
            input_payload={"approval_mode": agent.approval_mode},
            output_payload={"needs_approval": needs_approval, "reason": approval_reason},
            duration_ms=duration_ms,
        )

        if needs_approval:
            approval = ApprovalManager.create_approval_request(
                execution=execution,
                step=step_approval,
                tool_name=tool_name,
                arguments=arguments,
                reason=approval_reason,
            )
            execution.status = ExecutionStatus.WAITING_APPROVAL
            execution.output_response = f"Action requires confirmation: {approval_reason}"
            execution.save(update_fields=["status", "output_response"])

            cls._log_audit(
                event_type=AuditEventType.APPROVAL_REQUIRED,
                agent=agent,
                execution=execution,
                severity=AuditSeverity.WARNING,
                details={"approval_id": str(approval.approval_id), "reason": approval_reason},
            )
            execution.append_trace("Approval required", f"Execution paused awaiting approval: {approval_reason}", {"approval_id": str(approval.approval_id)})
            return execution

        # ── STAGE 8: TOOL EXECUTION ──
        return cls._execute_tool_and_finalize(
            execution=execution,
            agent=agent,
            tool_name=tool_name,
            arguments=arguments,
            step_num=step_num,
            working_context=working_context,
        )

    @classmethod
    def resume_after_approval(
        cls,
        approval_id: str,
        decision: str, # "APPROVED" or "REJECTED"
        approver=None,
        notes: str = "",
    ) -> AgentExecution:
        """
        Resumes a paused execution after a user approval or rejection.
        """
        approval = ApprovalManager.decide(approval_id, decision, approver=approver, notes=notes)
        execution = approval.execution
        agent = approval.agent or (execution.agent if execution else None)

        if not execution:
            if agent:
                execution = AgentExecution.objects.create(
                    agent=agent,
                    request_text=approval.requested_action,
                    status=ExecutionStatus.CANCELLED if approval.status == ApprovalStatus.REJECTED else ExecutionStatus.RUNNING,
                )
                approval.execution = execution
                approval.save(update_fields=["execution"])
            else:
                return None


        if approval.status == ApprovalStatus.REJECTED:
            cls._log_audit(
                event_type=AuditEventType.USER_REJECTED,
                agent=agent,
                execution=execution,
                severity=AuditSeverity.WARNING,
                details={"approval_id": str(approval.approval_id), "notes": notes},
            )
            execution.append_trace("User rejected", f"User rejected action: {notes or 'No reason specified'}")
            execution.status = ExecutionStatus.CANCELLED
            execution.output_response = "Action was rejected by user."
            execution.completed_at = timezone.now()
            execution.save(update_fields=["status", "output_response", "completed_at"])
            return execution

        # Status == APPROVED
        cls._log_audit(
            event_type=AuditEventType.USER_APPROVED,
            agent=agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details={"approval_id": str(approval.approval_id), "notes": notes},
        )
        execution.append_trace("User approved", "User approved action", {"approval_id": str(approval.approval_id)})

        # Resume execution
        execution.status = ExecutionStatus.RUNNING
        execution.save(update_fields=["status"])

        payload = approval.action_payload or {}
        tool_name = payload.get("tool")
        arguments = payload.get("arguments", {})

        current_step_num = execution.steps.count()
        return cls._execute_tool_and_finalize(
            execution=execution,
            agent=agent,
            tool_name=tool_name,
            arguments=arguments,
            step_num=current_step_num,
            working_context={},
        )

    # ── PRIVATE EXECUTION PIPELINE HELPERS ────────────────────────────────────
    @classmethod
    def _execute_tool_and_finalize(
        cls,
        execution: AgentExecution,
        agent: Agent,
        tool_name: str,
        arguments: Dict[str, Any],
        step_num: int,
        working_context: Dict[str, Any],
    ) -> AgentExecution:
        # Step: TOOL EXECUTION
        step_num += 1
        t0 = time.time()
        tool_res = ToolRegistry.execute(tool_name, arguments, working_context)
        duration_ms = int((time.time() - t0) * 1000)

        step_exec = AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.TOOL_EXECUTION,
            status=StepStatus.SUCCESS if tool_res["success"] else StepStatus.FAILED,
            input_payload={"tool": tool_name, "arguments": arguments},
            output_payload=tool_res,
            duration_ms=duration_ms,
            error_detail=tool_res.get("error") or "",
        )

        if not tool_res["success"]:
            cls._log_audit(
                event_type=AuditEventType.EXECUTION_FAILED,
                agent=agent,
                execution=execution,
                severity=AuditSeverity.ERROR,
                details={"tool": tool_name, "error": tool_res.get("error")},
            )
            execution.append_trace("Tool execution failed", tool_res.get("error", "Unknown error"))
            return cls._fail_execution(execution, f"Tool execution failed: {tool_res.get('error')}")

        cls._log_audit(
            event_type=AuditEventType.TOOL_EXECUTED,
            agent=agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details={"tool": tool_name, "result": tool_res.get("result")},
        )
        execution.append_trace("Tool executed", f"Tool '{tool_name}' executed successfully", tool_res.get("result"))

        # Step: RESULT VALIDATION
        step_num += 1
        t0 = time.time()
        val_res = cls._validate_result(tool_res.get("result"))
        duration_ms = int((time.time() - t0) * 1000)

        AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.RESULT_VALIDATION,
            status=StepStatus.SUCCESS,
            input_payload={"raw_result": tool_res.get("result")},
            output_payload={"validated": True},
            duration_ms=duration_ms,
        )
        cls._log_audit(
            event_type=AuditEventType.RESULT_VALIDATED,
            agent=agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details={"validated": True},
        )
        execution.append_trace("Result validated", "Tool execution result validated")

        # Format final output response
        final_response = cls._format_response(tool_name, tool_res.get("result"), arguments)
        return cls._complete_execution(execution, final_response)

    @classmethod
    def _parse_intent(cls, text: str, agent: Agent) -> Dict[str, Any]:
        """Classify user intent using heuristic / LLM parsing."""
        t = text.lower()
        if "balance" in t or "statement" in t or "how much" in t:
            return {"intent": "check_balance", "confidence": 0.95}
        if "transfer" in t or "send" in t or "pay" in t:
            return {"intent": "transfer_funds", "confidence": 0.92}
        if "catalog" in t or "product" in t or "search" in t or "find" in t:
            return {"intent": "query_catalog", "confidence": 0.90}
        if "echo" in t or "test" in t or "ping" in t:
            return {"intent": "echo", "confidence": 0.99}
        return {"intent": "general_chat", "confidence": 0.70}

    @classmethod
    def _gather_context(cls, agent: Agent, user, session_id: str, context: dict) -> Dict[str, Any]:
        memories = {}
        if session_id:
            qs = AgentMemory.objects.filter(agent=agent, session_id=session_id)
            for m in qs:
                memories[m.key] = m.value

        return {
            "session_id": session_id,
            "user_id": user.id if user and getattr(user, "id", None) else None,
            "memories": memories,
            "custom_context": context,
        }

    @classmethod
    def _generate_plan(cls, text: str, intent_info: dict, agent: Agent, context: dict) -> Dict[str, Any]:
        """
        Generate structured tool invocation plan.
        Extracts parameters deterministically without direct database access.
        """
        intent = intent_info.get("intent")

        if intent == "echo":
            return {"tool_name": "echo", "arguments": {"message": text}}

        if intent == "check_balance":
            import re
            acc_match = re.search(r"acc_[a-zA-Z0-9]+", text)
            acc_id = acc_match.group(0) if acc_match else "acc_default"
            return {"tool_name": "check_balance", "arguments": {"account_id": acc_id, "currency": "INR"}}

        if intent == "transfer_funds":
            import re
            # Extract amount
            amt_match = re.search(r"(?:rs\.?|inr|₹)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)", text, re.IGNORECASE)
            amount = 1000.0
            if amt_match:
                amt_str = amt_match.group(1).replace(",", "")
                try:
                    amount = float(amt_str)
                except ValueError:
                    amount = 1000.0

            # Extract recipient
            rec_match = re.search(r"(?:to|vendor|recipient)\s+([a-zA-Z0-9_]+)", text, re.IGNORECASE)
            recipient = rec_match.group(1) if rec_match else "vendor_partner"

            return {
                "tool_name": "transfer_funds",
                "arguments": {
                    "recipient_id": recipient,
                    "amount": amount,
                    "currency": "INR",
                    "note": f"Transfer triggered via {agent.name}",
                },
            }

        if intent == "query_catalog":
            import re
            q = text.replace("search", "").replace("find", "").replace("products", "").strip()
            return {"tool_name": "query_catalog", "arguments": {"query": q or "electronics"}}

        # Default conversational
        return {"tool_name": None, "direct_response": f"I understood your request: '{text}'. How can I assist you further?"}

    @classmethod
    def _validate_result(cls, result: Any) -> bool:
        return result is not None

    @classmethod
    def _format_response(cls, tool_name: str, result: Any, arguments: Dict[str, Any]) -> str:
        if tool_name == "check_balance":
            bal = result.get("available_balance", 0.0)
            curr = result.get("currency", "INR")
            return f"Your account ({result.get('account_id')}) balance is {curr} {bal:,.2f}."
        if tool_name == "transfer_funds":
            amt = result.get("amount", 0.0)
            rec = result.get("recipient_id")
            txn = result.get("transaction_id")
            return f"Successfully initiated transfer of ₹{amt:,.2f} to {rec} (Transaction ID: {txn})."
        if tool_name == "echo":
            return f"Echo response: {result.get('echo')}"
        if tool_name == "query_catalog":
            count = result.get("count", 0)
            return f"Found {count} products matching your query."
        return str(result)

    @classmethod
    def _complete_execution(cls, execution: AgentExecution, output: str) -> AgentExecution:
        execution.status = ExecutionStatus.COMPLETED
        execution.output_response = output
        execution.completed_at = timezone.now()
        execution.save(update_fields=["status", "output_response", "completed_at"])

        cls._log_audit(
            event_type=AuditEventType.EXECUTION_COMPLETED,
            agent=execution.agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details={"output": output},
        )
        execution.append_trace("Execution completed", "Execution completed successfully", {"output": output})
        return execution

    @classmethod
    def _fail_execution(
        cls,
        execution: AgentExecution,
        error: str,
        stage: str = "EXECUTION_FAILED",
        details: Optional[Dict[str, Any]] = None,
    ) -> AgentExecution:
        execution.status = ExecutionStatus.FAILED
        execution.error_message = error
        execution.completed_at = timezone.now()
        execution.save(update_fields=["status", "error_message", "completed_at"])

        audit_details = {"error": error, "stage": stage}
        if details:
            audit_details.update(details)

        cls._log_audit(
            event_type=AuditEventType.EXECUTION_FAILED,
            agent=execution.agent,
            execution=execution,
            severity=AuditSeverity.ERROR,
            details=audit_details,
        )
        execution.append_trace("Execution failed", error, {"stage": stage})
        return execution

    @classmethod
    def _log_audit(
        cls,
        event_type: str,
        agent: Optional[Agent],
        execution: Optional[AgentExecution],
        severity: str = AuditSeverity.INFO,
        details: dict = None,
    ):
        AgentAuditLog.objects.create(
            agent=agent,
            execution=execution,
            event_type=event_type,
            severity=severity,
            actor_type="AGENT" if agent else "SYSTEM",
            actor_id=str(agent.id) if agent else "runtime",
            details=details or {},
        )
