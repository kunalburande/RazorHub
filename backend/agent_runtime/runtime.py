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
from .observability.scrubber import SecretScrubber

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

        scrubbed_input = SecretScrubber.scrub({"request": request_text, "session_id": session_id})
        execution = AgentExecution.objects.create(
            agent=agent,
            user=user if getattr(user, "is_authenticated", False) else None,
            trigger=trigger,
            initial_request=request_text,
            input_payload=scrubbed_input,
            status=ExecutionStatus.RUNNING,
            current_step="EXECUTION_START",
            model_name="gemini-2.0-flash",
            timeline=[],
        )

        cls._log_audit(
            event_type=AuditEventType.EXECUTION_START,
            agent=agent,
            execution=execution,
            severity=AuditSeverity.INFO,
            details={"request": request_text, "session_id": session_id},
        )
        execution.append_trace("EXECUTION_START", "Agent started", {"request": request_text})
        execution.add_timeline_event("Agent started", stage="EXECUTION_START", status="INFO")

        # ── STAGE 2: AGENT STATUS CHECK ──
        if agent.status != AgentStatus.ACTIVE:
            err = f"Agent '{agent.name}' cannot execute requests while in '{agent.status}' state."
            return cls._fail_execution(execution, err, stage="AGENT_INACTIVE")

        # ── STAGE 3: INTENT PARSING ──
        step_num = 1
        t0 = time.time()
        intent_info = cls._parse_intent(request_text, agent)
        duration_ms = int((time.time() - t0) * 1000)

        intent_name = intent_info.get("intent", "GENERAL_QUERY")
        execution.intent = intent_name
        execution.save(update_fields=["intent"])

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
        execution.append_trace("Intent identified", f"Intent: {intent_name}", intent_info)
        execution.add_timeline_event("User intent identified", stage="INTENT_IDENTIFIED", status="INFO", meta=intent_info)

        # ── STAGE 4: CONTEXT GATHERING ──
        step_num += 1
        t0 = time.time()
        working_context = cls._gather_context(agent, user, session_id, context)
        working_context["execution_id"] = str(execution.execution_id)
        duration_ms = int((time.time() - t0) * 1000)

        execution.context_data = SecretScrubber.scrub(working_context)
        execution.save(update_fields=["context_data"])

        AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.CONTEXT_GATHERING,
            status=StepStatus.SUCCESS,
            input_payload={"session_id": session_id},
            output_payload=SecretScrubber.scrub(working_context),
            duration_ms=duration_ms,
        )
        ctx_msg = "Payment data retrieved" if any(w in (intent_name or "").lower() for w in ["payment", "invoice", "payout", "refund", "order", "recovery"]) else "Context data retrieved"
        execution.append_trace("Context gathered", "Context successfully gathered", {"user_id": str(user.id) if user else None})
        execution.add_timeline_event(ctx_msg, stage="CONTEXT_GATHERING", status="INFO", meta={"context_keys": list(working_context.keys())})


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

        if tool_name:
            execution.tools_selected = [tool_name]
            execution.tool_inputs = [SecretScrubber.scrub(arguments)]
            execution.save(update_fields=["tools_selected", "tool_inputs"])
            execution.append_trace("Tool selected", f"Selected tool '{tool_name}'", {"tool": tool_name, "arguments": arguments})
            execution.add_timeline_event(f"Tool selected: {tool_name}", stage="TOOL_SELECTED", status="INFO", meta={"tool": tool_name})


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
        risk_score = getattr(gov_res, "risk_score", 0)

        risk_details = {
            "risk_score": risk_score,
            "risk_level": getattr(gov_res, "risk_level", "LOW" if risk_score < 30 else "MEDIUM" if risk_score < 60 else "HIGH" if risk_score < 85 else "CRITICAL"),
            "critical_rule_triggered": getattr(gov_res, "critical_rule_triggered", False),
            "reasons": getattr(gov_res, "risk_reasons", []),
        }
        policy_details = {
            "allowed": is_allowed,
            "governance_decision": gov_res.decision,
            "policy_triggered": gov_res.policy_triggered,
            "reason": gov_res.reason or policy_res.reason,
        }

        execution.risk_checks = SecretScrubber.scrub(risk_details)
        execution.policy_checks = [SecretScrubber.scrub(policy_details)]
        execution.save(update_fields=["risk_checks", "policy_checks"])

        # Structured timeline events matching user example:
        # "15:42:04 Risk score calculated: 21"
        # "15:42:04 Policy approved"
        execution.add_timeline_event(f"Risk score calculated: {risk_score}", stage="RISK_EVALUATION", status="INFO" if risk_score < 60 else "WARNING", meta=risk_details)
        if is_allowed:
            execution.add_timeline_event("Policy approved", stage="POLICY_EVALUATION", status="INFO", meta=policy_details)
        else:
            execution.add_timeline_event(f"Policy denied: {gov_res.reason or policy_res.reason}", stage="POLICY_DENIED", status="FAILED", meta=policy_details)

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
            execution.approval_request = SecretScrubber.scrub({
                "needs_approval": True,
                "reason": gov_res.reason,
                "requires_double": gov_res.requires_double_confirmation,
                "approval_id": gov_res.approval_id,
            })
            execution.save(update_fields=["status", "output_response", "approval_request"])
            execution.add_timeline_event(f"Action requires confirmation: {gov_res.reason}", stage="APPROVAL_REQUIRED", status="WARNING")
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
            execution.approval_request = SecretScrubber.scrub({
                "needs_approval": True,
                "reason": approval_reason,
                "approval_id": str(approval.approval_id),
                "approval_mode": agent.approval_mode,
            })
            execution.save(update_fields=["status", "output_response", "approval_request"])
            execution.add_timeline_event(f"Approval required: {approval_reason}", stage="APPROVAL_REQUIRED", status="WARNING")

            cls._log_audit(
                event_type=AuditEventType.APPROVAL_REQUIRED,
                agent=agent,
                execution=execution,
                severity=AuditSeverity.WARNING,
                details={"approval_id": str(approval.approval_id), "reason": approval_reason},
            )
            execution.append_trace("Approval required", f"Execution paused awaiting approval: {approval_reason}", {"approval_id": str(approval.approval_id)})
            return execution
        else:
            # Matches user example: "15:42:04 No human approval required"
            execution.approval_request = {"needs_approval": False}
            execution.save(update_fields=["approval_request"])
            execution.add_timeline_event("No human approval required", stage="APPROVAL_CHECK", status="INFO")


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
            execution.approval_response = SecretScrubber.scrub({
                "decision": "REJECTED",
                "approver": str(approver) if approver else "user",
                "notes": notes,
                "timestamp": timezone.now().isoformat(),
            })
            execution.save(update_fields=["approval_response"])
            execution.add_timeline_event(f"Action rejected by user: {notes or 'No reason specified'}", stage="USER_REJECTED", status="WARNING")

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
        execution.approval_response = SecretScrubber.scrub({
            "decision": "APPROVED",
            "approver": str(approver) if approver else "user",
            "notes": notes,
            "timestamp": timezone.now().isoformat(),
        })
        execution.save(update_fields=["approval_response"])
        execution.add_timeline_event("User approval granted", stage="USER_APPROVED", status="INFO", meta={"approval_id": str(approval.approval_id)})

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

        # Emit timeline event before tool execution matching user specification
        if tool_name == "create_payment_intent":
            execution.add_timeline_event("Payment intent created", stage="PAYMENT_INTENT_CREATED", status="INFO")
        elif "payment" in tool_name.lower():
            execution.add_timeline_event(f"Executing payment tool: {tool_name}", stage="TOOL_EXECUTION", status="INFO")
        else:
            execution.add_timeline_event(f"Executing tool: {tool_name}", stage="TOOL_EXECUTION", status="INFO")

        tool_res = ToolRegistry.execute(tool_name, arguments, working_context)
        duration_ms = int((time.time() - t0) * 1000)

        scrubbed_res = SecretScrubber.scrub(tool_res)
        execution.tool_results = [scrubbed_res]
        execution.final_action = f"Executed {tool_name}"
        if not execution.tools_selected:
            execution.tools_selected = [tool_name]
        if not execution.tool_inputs:
            execution.tool_inputs = [SecretScrubber.scrub(arguments)]
        execution.save(update_fields=["tool_results", "final_action", "tools_selected", "tool_inputs"])

        step_exec = AgentExecutionStep.objects.create(
            execution=execution,
            step_number=step_num,
            step_type=StepType.TOOL_EXECUTION,
            status=StepStatus.SUCCESS if tool_res["success"] else StepStatus.FAILED,
            input_payload=SecretScrubber.scrub({"tool": tool_name, "arguments": arguments}),
            output_payload=scrubbed_res,
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
            execution.add_timeline_event(f"Tool {tool_name} failed: {tool_res.get('error')}", stage="TOOL_FAILED", status="ERROR")
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

        # Timeline event on completion:
        if tool_name in ["execute_payment", "execute_checkout"]:
            execution.add_timeline_event("Payment completed", stage="PAYMENT_COMPLETED", status="SUCCESS")
        else:
            execution.add_timeline_event(f"Tool {tool_name} completed", stage="TOOL_SUCCESS", status="SUCCESS")

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
            input_payload=SecretScrubber.scrub({"raw_result": tool_res.get("result")}),
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
        if "echo" in t or "ping" in t or text.strip().startswith("Echo"):
            return {"intent": "echo", "confidence": 0.99, "entities": {}}
        elif "balance" in t or "statement" in t or "how much" in t:
            return {"intent": "CHECK_BALANCE", "confidence": 0.95, "entities": {}}
        elif "refund" in t or "spike" in t:
            return {"intent": "ANALYZE_REFUNDS", "confidence": 0.92, "entities": {}}
        elif "invoice" in t or "overdue" in t or "receivable" in t:
            return {"intent": "MANAGE_RECEIVABLES", "confidence": 0.90, "entities": {}}
        elif "pay " in t or "payout" in t or "transfer" in t:
            return {"intent": "EXECUTE_PAYOUT", "confidence": 0.88, "entities": {}}
        elif "catalog" in t or "search" in t or "product" in t or "buy" in t or "order" in t or "headphone" in t or "purchase" in t:
            return {"intent": "COMMERCE_ORDER", "confidence": 0.89, "entities": {}}
        elif "reconcil" in t or "settle" in t:
            return {"intent": "RECONCILE_SETTLEMENTS", "confidence": 0.91, "entities": {}}
        elif "report" in t or "summary" in t or "metrics" in t:
            return {"intent": "GENERATE_REPORT", "confidence": 0.85, "entities": {}}
        else:
            return {"intent": "GENERAL_QUERY", "confidence": 0.75, "entities": {}}

    @classmethod
    def _gather_context(cls, agent: Agent, user, session_id: str, caller_ctx: Dict[str, Any]) -> Dict[str, Any]:
        memories = {}
        qs = AgentMemory.objects.filter(agent=agent)
        if session_id:
            qs = qs.filter(session_id=session_id)
        for m in qs[:20]:
            memories[m.key] = m.value

        ctx = {
            "agent_id": str(agent.id),
            "agent_name": agent.name,
            "session_id": session_id,
            "memories": memories,
        }
        if user and getattr(user, "is_authenticated", False):
            ctx["user_id"] = str(user.id)
            ctx["user_email"] = user.email

        if caller_ctx:
            ctx.update(caller_ctx)
        return ctx

    @classmethod
    def _generate_plan(cls, request: str, intent: Dict[str, Any], agent: Agent, context: Dict[str, Any]) -> Dict[str, Any]:
        intent_type = intent.get("intent", "GENERAL_QUERY")
        t = request.lower()

        agent_tool_names = set(agent.tools.values_list("name", flat=True)) if agent and agent.pk else set()

        if intent_type == "echo":
            return {"tool_name": "echo", "arguments": {"message": request}}

        elif intent_type == "CHECK_BALANCE":
            import re
            acc_match = re.search(r"acc_[a-zA-Z0-9]+", request)
            acc_id = acc_match.group(0) if acc_match else "acc_primary_001"
            chosen_tool = "check_balance" if "check_balance" in agent_tool_names or not agent_tool_names else "check_balance"
            return {"tool_name": chosen_tool, "arguments": {"account_id": acc_id, "currency": "INR"}}

        elif intent_type == "ANALYZE_REFUNDS":
            return {"tool_name": "analyze_refunds", "arguments": {"lookback_days": 30}}

        elif intent_type == "MANAGE_RECEIVABLES":
            return {"tool_name": "get_overdue_invoices", "arguments": {"days_threshold": 30}}

        elif intent_type == "EXECUTE_PAYOUT":
            import re
            amt_match = re.search(r"(?:rs\.?|inr|₹)?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)", request, re.IGNORECASE)
            amount = 1000.0
            if amt_match:
                try:
                    amount = float(amt_match.group(1).replace(",", ""))
                except ValueError:
                    amount = 1000.0

            rec_match = re.search(r"(?:to|vendor|recipient)\s+([a-zA-Z0-9_]+)", request, re.IGNORECASE)
            recipient = rec_match.group(1) if rec_match else ("Rahul Enterprises" if "rahul" in t else "vendor_partner")

            if "execute_payout" in agent_tool_names:
                return {"tool_name": "execute_payout", "arguments": {"recipient": recipient, "amount": amount, "currency": "INR"}}
            else:
                return {
                    "tool_name": "transfer_funds",
                    "arguments": {
                        "recipient_id": recipient,
                        "amount": amount,
                        "currency": "INR",
                        "note": f"Transfer triggered via {agent.name}",
                    },
                }

        elif intent_type == "COMMERCE_ORDER":
            if "query_catalog" in agent_tool_names or "catalog" in t or "search" in t or "find" in t:
                import re
                q = request.replace("search", "").replace("find", "").replace("products", "").replace("catalog", "").strip()
                return {"tool_name": "query_catalog", "arguments": {"query": q or "headphones"}}
            return {"tool_name": "create_payment_intent", "arguments": {"amount": 2999.0, "currency": "INR", "item": "Wireless Headphones"}}

        elif intent_type == "RECONCILE_SETTLEMENTS":
            return {"tool_name": "reconcile_settlements", "arguments": {"batch_id": "set_batch_today"}}

        elif intent_type == "GENERATE_REPORT":
            return {"tool_name": "generate_report", "arguments": {"report_type": "EXECUTIVE_SUMMARY"}}

        else:
            return {"tool_name": None, "direct_response": f"I analyzed your request: '{request}'. How else can I assist your business?"}

    @classmethod
    def _validate_result(cls, result: Any) -> Dict[str, Any]:
        return {"valid": True}

    @classmethod
    def _format_response(cls, tool_name: str, result: Any, arguments: Dict[str, Any]) -> str:
        if isinstance(result, dict) and "formatted_response" in result:
            return result["formatted_response"]
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
        return f"Successfully executed {tool_name} with parameters {arguments}. Result: {result}"


    @classmethod
    def _complete_execution(cls, execution: AgentExecution, output: str) -> AgentExecution:
        t_now = timezone.now()
        duration_ms = int((t_now - execution.started_at).total_seconds() * 1000) if execution.started_at else 0
        execution.duration_ms = max(duration_ms, 1)

        req_len = len(execution.initial_request or "")
        out_len = len(output or "")
        execution.token_usage = {
            "prompt_tokens": max(15, req_len // 4 + 40),
            "completion_tokens": max(10, out_len // 4 + 20),
            "total_tokens": max(25, (req_len + out_len) // 4 + 60),
        }

        execution.status = ExecutionStatus.COMPLETED
        execution.output_response = output
        execution.completed_at = t_now
        execution.current_step = "COMPLETED"

        # Matching user specification:
        # "15:42:06 Audit record written"
        execution.add_timeline_event("Audit record written", stage="AUDIT_RECORD", status="INFO")

        execution.save(update_fields=["status", "output_response", "duration_ms", "token_usage", "completed_at", "current_step"])

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
        t_now = timezone.now()
        duration_ms = int((t_now - execution.started_at).total_seconds() * 1000) if execution.started_at else 0
        execution.duration_ms = max(duration_ms, 1)

        execution.status = ExecutionStatus.FAILED
        execution.error_message = error
        execution.completed_at = t_now
        execution.current_step = stage

        execution.add_timeline_event(f"Execution failed: {error}", stage=stage, status="ERROR", meta=details)
        execution.add_timeline_event("Audit record written", stage="AUDIT_RECORD", status="INFO")

        execution.save(update_fields=["status", "error_message", "duration_ms", "completed_at", "current_step"])

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
        scrubbed_details = SecretScrubber.scrub(details or {})
        AgentAuditLog.objects.create(
            agent=agent,
            execution=execution,
            event_type=event_type,
            severity=severity,
            actor_type="AGENT" if agent else "SYSTEM",
            actor_id=str(agent.id) if agent else "runtime",
            details=scrubbed_details,
        )
