import uuid
from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from .models import (
    Agent,
    AgentPaymentAuthorization,
    AgentAuthorizationLedger,
)
from .authorization_service import (
    AgentAuthorizationService,
    AuthorizationDecision,
)

User = get_user_model()


class AgentPaymentAuthorizationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="reserve_user@razorhub.test",
            password="testpassword123",
            username="reserve_user",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.agent = Agent.objects.create(
            name="Reserve Pay Agent",
            description="Agent supporting simulated pre-authorized payments",
            system_prompt="You handle consent-based payments.",
            status="ACTIVE",
            approval_mode="AUTO",
            risk_level="LOW",
        )

        self.auth = AgentPaymentAuthorization.objects.create(
            user=self.user,
            agent=self.agent,
            max_transaction_amount=Decimal("5000.00"),
            daily_limit=Decimal("10000.00"),
            monthly_limit=Decimal("50000.00"),
            approval_threshold=Decimal("2000.00"),
            allowed_categories=["electronics", "peripherals", "apparel"],
            blocked_categories=["cash", "crypto", "gambling"],
            allowed_merchants=["RazorHub Direct", "SonicAudio Official Store"],
            blocked_merchants=["Fraudulent Store"],
            status=AgentPaymentAuthorization.AuthStatus.ACTIVE,
        )

    def test_authorization_creation_and_defaults(self):
        """Verifies authorization fields and remaining balances."""
        self.assertEqual(self.auth.used_today, Decimal("0.00"))
        self.assertEqual(self.auth.used_this_month, Decimal("0.00"))
        self.assertEqual(self.auth.status, AgentPaymentAuthorization.AuthStatus.ACTIVE)

    def test_atomic_limit_consumption(self):
        """Verifies real-time consumption of daily and monthly limits for auto-approved payments."""
        res = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("1500.00"),
            merchant="RazorHub Direct",
            category="electronics",
            idempotency_key="tx_key_001",
        )
        self.assertEqual(res["decision"], AuthorizationDecision.AUTO_APPROVED)
        self.assertEqual(res["used_today"], 1500.00)
        self.assertEqual(res["used_this_month"], 1500.00)
        self.assertEqual(res["remaining_today"], 8500.00)
        self.assertEqual(res["remaining_month"], 48500.00)

        self.auth.refresh_from_db()
        self.assertEqual(self.auth.used_today, Decimal("1500.00"))
        self.assertEqual(self.auth.used_this_month, Decimal("1500.00"))

        # Verify ledger row created
        ledger = AgentAuthorizationLedger.objects.filter(idempotency_key="tx_key_001").first()
        self.assertIsNotNone(ledger)
        self.assertEqual(ledger.amount, Decimal("1500.00"))
        self.assertEqual(ledger.before_today, Decimal("0.00"))
        self.assertEqual(ledger.after_today, Decimal("1500.00"))

    def test_duplicate_payment_protection_via_idempotency(self):
        """Verifies calling verify_and_consume with identical idempotency_key does not double-deduct."""
        # First execution
        res1 = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("1000.00"),
            merchant="RazorHub Direct",
            category="electronics",
            idempotency_key="unique_key_100",
        )
        self.assertEqual(res1["decision"], AuthorizationDecision.AUTO_APPROVED)

        # Second execution with identical key
        res2 = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("1000.00"),
            merchant="RazorHub Direct",
            category="electronics",
            idempotency_key="unique_key_100",
        )
        self.assertEqual(res2["decision"], AuthorizationDecision.DUPLICATE)

        # Confirm ledger has only 1 entry and used_today is 1000, not 2000
        self.auth.refresh_from_db()
        self.assertEqual(self.auth.used_today, Decimal("1000.00"))
        self.assertEqual(AgentAuthorizationLedger.objects.filter(idempotency_key="unique_key_100").count(), 1)

    def test_per_transaction_and_daily_limit_blocking(self):
        """Verifies transactions exceeding per-transaction or daily ceilings are blocked."""
        # Exceeds max per-transaction (₹5,000)
        res_over_max = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("6000.00"),
            merchant="RazorHub Direct",
            category="electronics",
            idempotency_key="over_max_key",
        )
        self.assertEqual(res_over_max["decision"], AuthorizationDecision.BLOCKED)
        self.assertIn("exceeds maximum authorized transaction limit", res_over_max["reason"])

        # Exceeds daily limit (10,000)
        self.auth.used_today = Decimal("9000.00")
        self.auth.save(update_fields=["used_today"])

        res_over_daily = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("1500.00"),
            merchant="RazorHub Direct",
            category="electronics",
            idempotency_key="over_daily_key",
        )
        self.assertEqual(res_over_daily["decision"], AuthorizationDecision.BLOCKED)
        self.assertIn("exceeds remaining daily limit", res_over_daily["reason"])

    def test_category_and_merchant_restrictions(self):
        """Verifies blocked categories and blocked merchants trigger denial."""
        res_blocked_cat = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("500.00"),
            merchant="RazorHub Direct",
            category="crypto",
            idempotency_key="crypto_tx",
        )
        self.assertEqual(res_blocked_cat["decision"], AuthorizationDecision.BLOCKED)
        self.assertIn("blocked by consent policy", res_blocked_cat["reason"])

        res_blocked_merch = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("500.00"),
            merchant="Fraudulent Store",
            category="electronics",
            idempotency_key="fraud_tx",
        )
        self.assertEqual(res_blocked_merch["decision"], AuthorizationDecision.BLOCKED)
        self.assertIn("blocked by consent policy", res_blocked_merch["reason"])

    def test_confirmation_threshold_trigger(self):
        """Verifies transactions between approvalThreshold and maxTransactionAmount require human confirmation."""
        res_confirm = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("3500.00"),
            merchant="RazorHub Direct",
            category="electronics",
            idempotency_key="confirm_tx_01",
        )
        self.assertEqual(res_confirm["decision"], AuthorizationDecision.REQUIRES_CONFIRMATION)
        # Should not have deducted funds yet
        self.auth.refresh_from_db()
        self.assertEqual(self.auth.used_today, Decimal("0.00"))

        # Now simulate confirmation approval
        res_confirmed = AgentAuthorizationService.verify_and_consume(
            auth_id=str(self.auth.id),
            amount=Decimal("3500.00"),
            merchant="RazorHub Direct",
            category="electronics",
            idempotency_key="confirm_tx_01",
            is_confirmation=True,
        )
        self.assertEqual(res_confirmed["decision"], AuthorizationDecision.AUTO_APPROVED)
        self.auth.refresh_from_db()
        self.assertEqual(self.auth.used_today, Decimal("3500.00"))

    def test_api_lifecycle_endpoints(self):
        """Tests Pause, Resume, Revoke, Edit Limits, and Test Verify API endpoints."""
        auth_id = str(self.auth.id)

        # 1. Pause
        res_pause = self.client.post(f"/api/agent-runtime/authorizations/{auth_id}/pause/")
        self.assertEqual(res_pause.status_code, status.HTTP_200_OK)
        self.auth.refresh_from_db()
        self.assertEqual(self.auth.status, AgentPaymentAuthorization.AuthStatus.PAUSED)

        # Verify transaction fails when paused
        res_fail_paused = self.client.post(
            f"/api/agent-runtime/authorizations/{auth_id}/test_verify/",
            {"amount": 500, "merchant": "RazorHub Direct", "category": "electronics"},
            format="json",
        )
        self.assertEqual(res_fail_paused.status_code, status.HTTP_400_BAD_REQUEST)

        # 2. Resume
        res_resume = self.client.post(f"/api/agent-runtime/authorizations/{auth_id}/resume/")
        self.assertEqual(res_resume.status_code, status.HTTP_200_OK)
        self.auth.refresh_from_db()
        self.assertEqual(self.auth.status, AgentPaymentAuthorization.AuthStatus.ACTIVE)

        # 3. Edit Limits
        res_limits = self.client.patch(
            f"/api/agent-runtime/authorizations/{auth_id}/limits/",
            {"max_transaction_amount": 7500.00, "daily_limit": 15000.00},
            format="json",
        )
        self.assertEqual(res_limits.status_code, status.HTTP_200_OK)
        self.auth.refresh_from_db()
        self.assertEqual(self.auth.max_transaction_amount, Decimal("7500.00"))
        self.assertEqual(self.auth.daily_limit, Decimal("15000.00"))

        # 4. Revoke
        res_revoke = self.client.post(f"/api/agent-runtime/authorizations/{auth_id}/revoke/")
        self.assertEqual(res_revoke.status_code, status.HTTP_200_OK)
        self.auth.refresh_from_db()
        self.assertEqual(self.auth.status, AgentPaymentAuthorization.AuthStatus.REVOKED)
