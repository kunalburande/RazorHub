import logging
from typing import Any, Dict, List, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class ExecutionReplayEngine:
    """
    Observability Replay Engine.
    Enables replaying past agent executions in a deterministic, observable sandbox
    to verify policy decisions, tool selections, and timeline event sequences.
    """

    @classmethod
    def replay(
        cls,
        execution_id: str,
        user=None,
        sandbox: bool = True,
    ) -> Dict[str, Any]:
        from ..models import AgentExecution, ExecutionStatus
        from ..runtime import AgentRuntime
        from .scrubber import SecretScrubber

        try:
            original = AgentExecution.objects.prefetch_related("steps").get(execution_id=execution_id)
        except AgentExecution.DoesNotExist:
            raise ValueError(f"Execution '{execution_id}' not found.")

        orig_summary = {
            "execution_id": str(original.execution_id),
            "agent_id": str(original.agent.id),
            "agent_name": original.agent.name,
            "status": original.status,
            "initial_request": original.initial_request,
            "intent": original.intent,
            "duration_ms": original.duration_ms,
            "tools_selected": original.tools_selected,
            "risk_score": (original.risk_checks or {}).get("risk_score", 0),
            "policy_checks": original.policy_checks,
            "output_response": original.output_response,
            "timeline": original.timeline or [],
        }

        # Prepare context for replay execution
        replay_context = dict(original.context_data or {})
        replay_context["is_replay"] = True
        replay_context["replay_of"] = str(original.execution_id)
        replay_context["sandbox"] = sandbox

        # Execute replay
        replayed = AgentRuntime.run(
            request_text=original.initial_request,
            agent=original.agent,
            user=user or original.user,
            context=replay_context,
        )

        replayed_summary = {
            "execution_id": str(replayed.execution_id),
            "status": replayed.status,
            "intent": replayed.intent,
            "duration_ms": replayed.duration_ms,
            "tools_selected": replayed.tools_selected,
            "risk_score": (replayed.risk_checks or {}).get("risk_score", 0),
            "policy_checks": replayed.policy_checks,
            "output_response": replayed.output_response,
            "timeline": replayed.timeline or [],
        }

        # Compare outcomes
        intent_match = (original.intent or "").lower() == (replayed.intent or "").lower()
        tools_match = (original.tools_selected or []) == (replayed.tools_selected or [])
        status_match = original.status == replayed.status

        orig_risk = (original.risk_checks or {}).get("risk_score", 0)
        rep_risk = (replayed.risk_checks or {}).get("risk_score", 0)
        risk_match = orig_risk == rep_risk

        playback_events = cls._build_playback_events(replayed.timeline or original.timeline or [])

        return {
            "success": True,
            "sandbox": sandbox,
            "matched": intent_match and tools_match,
            "verifications": {
                "intent_match": intent_match,
                "tools_match": tools_match,
                "status_match": status_match,
                "risk_match": risk_match,
            },
            "original": SecretScrubber.scrub(orig_summary),
            "replayed": SecretScrubber.scrub(replayed_summary),
            "playback_events": playback_events,
        }

    @classmethod
    def _build_playback_events(cls, timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Formats timeline items for UI step-by-step replay player.
        """
        events = []
        for idx, item in enumerate(timeline):
            events.append({
                "step_index": idx + 1,
                "time": item.get("time", "00:00:00"),
                "timestamp": item.get("timestamp", ""),
                "title": item.get("title", ""),
                "stage": item.get("stage", ""),
                "status": item.get("status", "INFO"),
                "meta": item.get("meta", {}),
            })
        return events
