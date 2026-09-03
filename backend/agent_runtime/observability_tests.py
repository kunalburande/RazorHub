import json
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    Agent,
    AgentStatus,
    ApprovalMode,
    ExecutionStatus,
    AgentExecution,
    AgentAuditLog,
)
from .observability.scrubber import SecretScrubber
from .observability.replay import ExecutionReplayEngine
from .runtime import AgentRuntime

User = get_user_model()


class ObservabilityAndAuditTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="observability_tester@kinahub.com",
            email="observability_tester@kinahub.com",
            password="testpassword123",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.agent = Agent.objects.create(
            name="Observability Sentinel Agent",
            description="Agent for testing end-to-end execution observability and audit trails",
            system_prompt="You are an autonomous commerce assistant. Use tools safely under zero-trust governance.",
            status=AgentStatus.ACTIVE,
            approval_mode=ApprovalMode.AUTO,
        )

    def test_secret_scrubber_masks_sensitive_keys_and_patterns(self):
        """
        Requirement: 'Sensitive values such as API secrets must never appear in logs.'
        """
        payload = {
            "api_key": "sk_test_SECRET_API_KEY_1234567890",
            "password": "SuperSecretPassword!",
            "card_number": "4111222233334444",
            "cvv": "987",
            "user_token": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "nested": {
                "secret_key": "rzp_test_9876543210abcdef",
                "client_secret": "my_client_secret_xyz",
                "safe_field": "safe_information",
            },
            "log_message": "Contact API at rzp_test_1234567890abcd with Bearer mySecretTokenValue123",
        }

        scrubbed = SecretScrubber.scrub(payload)

        # Sensitive keys should be redacted
        self.assertEqual(scrubbed["api_key"], SecretScrubber.REDACTED_LABEL)
        self.assertEqual(scrubbed["password"], SecretScrubber.REDACTED_LABEL)
        self.assertEqual(scrubbed["cvv"], SecretScrubber.REDACTED_LABEL)
        self.assertIn("****-****-****-4444", scrubbed["card_number"])
        self.assertEqual(scrubbed["nested"]["secret_key"], SecretScrubber.REDACTED_LABEL)
        self.assertEqual(scrubbed["nested"]["client_secret"], SecretScrubber.REDACTED_LABEL)
        self.assertEqual(scrubbed["nested"]["safe_field"], "safe_information")

        # Inline strings should have secrets replaced
        self.assertNotIn("rzp_test_1234567890abcd", scrubbed["log_message"])
        self.assertIn("[REDACTED_RAZORPAY_KEY]", scrubbed["log_message"])
        self.assertNotIn("mySecretTokenValue123", scrubbed["log_message"])
        self.assertIn("Bearer [REDACTED_TOKEN]", scrubbed["log_message"])


    def test_full_20_fields_execution_capture(self):
        """
        Requirement: Every agent execution must capture all 20 specified fields:
        executionId, agentId, userId, timestamp, intent, input, context,
        toolsSelected, toolInputs, policyChecks, riskChecks, approvalRequest,
        approvalResponse, toolResults, finalAction, status, error, duration,
        model, tokenUsage
        """
        prompt = "Pay Rahul ₹5,000 for invoice INV-101"
        execution = AgentRuntime.run(
            request_text=prompt,
            agent=self.agent,
            user=self.user,
        )

        self.assertIsNotNone(execution.execution_id)
        self.assertEqual(execution.agent.id, self.agent.id)
        self.assertEqual(execution.user.id, self.user.id)
        self.assertIsNotNone(execution.started_at)
        self.assertTrue(bool(execution.intent))
        self.assertTrue(bool(execution.input_payload))
        self.assertTrue(bool(execution.context_data))
        self.assertTrue(isinstance(execution.tools_selected, list))
        self.assertTrue(isinstance(execution.tool_inputs, list))
        self.assertTrue(isinstance(execution.policy_checks, list))
        self.assertTrue(isinstance(execution.risk_checks, dict))
        self.assertTrue(isinstance(execution.approval_request, dict))
        self.assertTrue(isinstance(execution.tool_results, list))
        self.assertTrue(bool(execution.final_action))
        self.assertIn(execution.status, [ExecutionStatus.COMPLETED, ExecutionStatus.WAITING_APPROVAL])
        self.assertGreaterEqual(execution.duration_ms, 0)
        self.assertEqual(execution.model_name, "gemini-2.0-flash")
        self.assertTrue(isinstance(execution.token_usage, dict))
        self.assertGreater(execution.token_usage.get("total_tokens", 0), 0)

        # Serializer representation check for both camelCase and snake_case
        res = self.client.get(f"/api/agent-runtime/executions/{execution.execution_id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()

        expected_fields = [
            "executionId",
            "agentId",
            "userId",
            "timestamp",
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
            "model",
            "tokenUsage",
        ]
        for field in expected_fields:
            self.assertIn(field, data, f"Missing required field {field} in execution response")

    def test_execution_timeline_events_and_formatting(self):
        """
        Requirement: Create an execution timeline UI with formatted timestamps:
        Example:
        15:42:02 Agent started
        15:42:03 User intent identified
        15:42:03 Payment data retrieved
        15:42:04 Risk score calculated: 21
        15:42:04 Policy approved
        15:42:04 No human approval required
        ...
        15:42:06 Audit record written
        """
        prompt = "Check my account balance"
        execution = AgentRuntime.run(
            request_text=prompt,
            agent=self.agent,
            user=self.user,
        )

        timeline = execution.timeline
        self.assertTrue(isinstance(timeline, list))
        self.assertGreater(len(timeline), 4)

        titles = [t["title"] for t in timeline]
        stages = [t["stage"] for t in timeline]

        # Verify timeline sequence
        self.assertIn("Agent started", titles)
        self.assertIn("User intent identified", titles)
        self.assertTrue(any("retrieved" in t for t in titles))
        self.assertTrue(any("Risk score calculated" in t for t in titles))
        self.assertTrue(any("Policy approved" in t for t in titles))
        self.assertIn("Audit record written", titles)

        # Verify time format: HH:MM:SS
        for item in timeline:
            time_str = item.get("time")
            self.assertIsNotNone(time_str)
            parts = time_str.split(":")
            self.assertEqual(len(parts), 3, f"Time '{time_str}' not in HH:MM:SS format")

        # Test dedicated timeline endpoint
        res = self.client.get(f"/api/agent-runtime/executions/{execution.execution_id}/timeline/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.json()["timeline"]), len(timeline))

    def test_execution_replay_engine(self):
        """
        Requirement: Provide 'Replay execution' functionality comparing
        original execution vs replayed run in an observable sandbox.
        """
        prompt = "Search catalog for premium headphones"
        orig_execution = AgentRuntime.run(
            request_text=prompt,
            agent=self.agent,
            user=self.user,
        )

        replay_result = ExecutionReplayEngine.replay(
            execution_id=str(orig_execution.execution_id),
            user=self.user,
            sandbox=True,
        )

        self.assertTrue(replay_result["success"])
        self.assertTrue(replay_result["sandbox"])
        self.assertIn("verifications", replay_result)
        self.assertTrue(replay_result["verifications"]["intent_match"])
        self.assertIn("playback_events", replay_result)
        self.assertGreater(len(replay_result["playback_events"]), 0)

        # Test replay API endpoint
        res = self.client.post(f"/api/agent-runtime/executions/{orig_execution.execution_id}/replay/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("original", data)
        self.assertIn("replayed", data)

    def test_observability_detail_endpoints(self):
        """
        Requirement: Provide:
        - View execution
        - View tool calls
        - View policy decisions
        - View errors
        """
        execution = AgentRuntime.run(
            request_text="Show overview report",
            agent=self.agent,
            user=self.user,
        )

        # 1. View execution
        res_exec = self.client.get(f"/api/agent-runtime/executions/{execution.execution_id}/")
        self.assertEqual(res_exec.status_code, status.HTTP_200_OK)

        # 2. View tool calls
        res_tools = self.client.get(f"/api/agent-runtime/executions/{execution.execution_id}/tool-calls/")
        self.assertEqual(res_tools.status_code, status.HTTP_200_OK)
        tools_data = res_tools.json()
        self.assertIn("tools_selected", tools_data)
        self.assertIn("tool_results", tools_data)

        # 3. View policy decisions
        res_policy = self.client.get(f"/api/agent-runtime/executions/{execution.execution_id}/policy-decisions/")
        self.assertEqual(res_policy.status_code, status.HTTP_200_OK)
        policy_data = res_policy.json()
        self.assertIn("policy_checks", policy_data)
        self.assertIn("risk_checks", policy_data)

        # 4. View errors
        res_err = self.client.get(f"/api/agent-runtime/executions/{execution.execution_id}/errors/")
        self.assertEqual(res_err.status_code, status.HTTP_200_OK)
        err_data = res_err.json()
        self.assertIn("has_error", err_data)
        self.assertFalse(err_data["has_error"])
