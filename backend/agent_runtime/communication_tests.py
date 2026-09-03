from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from crm.models import Notification
from .models import (
    CommunicationConsent,
    CommunicationPreference,
    CommunicationEvent,
    CommunicationChannel,
    CommunicationEventStatus,
    Agent,
)
from .communications.engine import CommunicationEngine
from .communications.templates import GovernedCommunicationTemplates

User = get_user_model()


class OutboundCommunicationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="recipient@razorhub.test",
            password="testpassword123",
            username="recipient_user",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.agent = Agent.objects.create(
            name="Receivables & Communications Agent",
            description="Autonomous agent for follow-ups and notifications",
            system_prompt="Send polite notifications",
            status="ACTIVE",
        )

        # Ensure preference exists
        self.pref = CommunicationEngine.get_or_create_preferences(self.user)

    def test_successful_dispatch_with_consent_and_channel_enabled(self):
        """Verifies active consent + enabled channel dispatches successfully."""
        CommunicationConsent.objects.create(
            user=self.user,
            purpose="TRANSACTIONAL",
            is_granted=True,
        )

        res = CommunicationEngine.dispatch(
            user=self.user,
            channel="EMAIL",
            template_name="payment_confirmation",
            immutable_data={
                "transaction_id": "TXN-9021",
                "amount_paid": 4500.0,
                "tax_invoice_id": "GST-2026-09",
            },
            personal_greeting="Hello Priya",
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["status"], CommunicationEventStatus.DISPATCHED)
        self.assertIn("₹4,500.00", res["rendered_content"])
        self.assertIn("TXN-9021", res["rendered_content"])

        event = CommunicationEvent.objects.get(id=res["event_id"])
        self.assertEqual(event.status, CommunicationEventStatus.DISPATCHED)

    def test_real_in_app_notification_creation(self):
        """Verifies In-App channel creates real crm.models.Notification in database."""
        CommunicationConsent.objects.create(
            user=self.user,
            purpose="SECURITY_ALERTS",
            is_granted=True,
        )

        initial_count = Notification.objects.filter(user=self.user).count()

        res = CommunicationEngine.dispatch(
            user=self.user,
            channel="IN_APP",
            template_name="risk_alert",
            immutable_data={
                "alert_code": "SEC_IP_MISMATCH",
                "incident_timestamp": "2026-09-03 18:30 IST",
                "security_escalation_link": "https://razorhub.test/security/lock",
            },
            personal_greeting="Immediate Action Required",
        )

        self.assertTrue(res["success"])
        self.assertEqual(res["status"], CommunicationEventStatus.DISPATCHED)

        # Check real CRM Notification was created
        new_count = Notification.objects.filter(user=self.user).count()
        self.assertEqual(new_count, initial_count + 1)
        latest_notif = Notification.objects.filter(user=self.user).latest("id")
        self.assertIn("SEC_IP_MISMATCH", latest_notif.body)

    def test_blocked_by_missing_consent(self):
        """Verifies missing consent halts communication with BLOCKED_NO_CONSENT."""
        # No consent created for COLLECTIONS
        res = CommunicationEngine.dispatch(
            user=self.user,
            channel="EMAIL",
            template_name="invoice_reminder",
            immutable_data={
                "invoice_number": "INV-101",
                "amount_due": 12000.0,
                "due_date": "2026-09-15",
                "bank_details": "HDFC 910488271104",
            },
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["status"], CommunicationEventStatus.BLOCKED_NO_CONSENT)
        self.assertIn("not granted active consent", res["reason"])

    def test_blocked_by_revoked_consent(self):
        """Verifies revoked consent halts communication."""
        consent = CommunicationConsent.objects.create(
            user=self.user,
            purpose="TRANSACTIONAL",
            is_granted=True,
        )
        consent.revoke()

        res = CommunicationEngine.dispatch(
            user=self.user,
            channel="EMAIL",
            template_name="payment_confirmation",
            immutable_data={
                "transaction_id": "TXN-888",
                "amount_paid": 500.0,
                "tax_invoice_id": "GST-888",
            },
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["status"], CommunicationEventStatus.BLOCKED_NO_CONSENT)

    def test_blocked_by_channel_disabled(self):
        """Verifies disabled channel halts communication."""
        CommunicationConsent.objects.create(
            user=self.user,
            purpose="TRANSACTIONAL",
            is_granted=True,
        )
        self.pref.sms_enabled = False
        self.pref.save()

        res = CommunicationEngine.dispatch(
            user=self.user,
            channel="SMS",
            template_name="payment_confirmation",
            immutable_data={
                "transaction_id": "TXN-888",
                "amount_paid": 500.0,
                "tax_invoice_id": "GST-888",
            },
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["status"], CommunicationEventStatus.BLOCKED_CHANNEL_DISABLED)

    def test_blocked_by_opt_out_all(self):
        """
        Verifies rule: 'Agents must not repeatedly contact users who have opted out.'
        Global opt-out stops any attempt before consent/channel checks.
        """
        CommunicationConsent.objects.create(
            user=self.user,
            purpose="TRANSACTIONAL",
            is_granted=True,
        )
        self.pref.is_opted_out_all = True
        self.pref.save()

        res = CommunicationEngine.dispatch(
            user=self.user,
            channel="EMAIL",
            template_name="payment_confirmation",
            immutable_data={
                "transaction_id": "TXN-888",
                "amount_paid": 500.0,
                "tax_invoice_id": "GST-888",
            },
            agent=self.agent,
        )

        self.assertFalse(res["success"])
        self.assertEqual(res["status"], CommunicationEventStatus.BLOCKED_OPTED_OUT)
        self.assertIn("global opt-out", res["reason"])

    def test_blocked_by_frequency_limit(self):
        """Verifies exceeding daily frequency ceiling blocks further dispatch."""
        CommunicationConsent.objects.create(
            user=self.user,
            purpose="TRANSACTIONAL",
            is_granted=True,
        )
        self.pref.daily_frequency_limit = 2
        self.pref.save()

        # 1st dispatch -> success
        res1 = CommunicationEngine.dispatch(
            user=self.user,
            channel="EMAIL",
            template_name="payment_confirmation",
            immutable_data={"transaction_id": "TXN-1", "amount_paid": 100.0, "tax_invoice_id": "G-1"},
        )
        self.assertTrue(res1["success"])

        # 2nd dispatch -> success
        res2 = CommunicationEngine.dispatch(
            user=self.user,
            channel="EMAIL",
            template_name="payment_confirmation",
            immutable_data={"transaction_id": "TXN-2", "amount_paid": 200.0, "tax_invoice_id": "G-2"},
        )
        self.assertTrue(res2["success"])

        # 3rd dispatch -> BLOCKED_FREQUENCY_LIMIT
        res3 = CommunicationEngine.dispatch(
            user=self.user,
            channel="EMAIL",
            template_name="payment_confirmation",
            immutable_data={"transaction_id": "TXN-3", "amount_paid": 300.0, "tax_invoice_id": "G-3"},
        )
        self.assertFalse(res3["success"])
        self.assertEqual(res3["status"], CommunicationEventStatus.BLOCKED_FREQUENCY_LIMIT)

    def test_blocked_by_inactive_agent(self):
        """Verifies inactive agent cannot dispatch outbound communications."""
        CommunicationConsent.objects.create(
            user=self.user,
            purpose="TRANSACTIONAL",
            is_granted=True,
        )
        self.agent.status = "PAUSED"
        self.agent.save()

        res = CommunicationEngine.dispatch(
            user=self.user,
            channel="EMAIL",
            template_name="payment_confirmation",
            immutable_data={"transaction_id": "TXN-1", "amount_paid": 100.0, "tax_invoice_id": "G-1"},
            agent=self.agent,
        )
        self.assertFalse(res["success"])
        self.assertEqual(res["status"], CommunicationEventStatus.BLOCKED_AGENT_PERMISSION)

    def test_immutable_template_anchors_and_legal_compliance(self):
        """Verifies all 6 templates enforce immutable financial/legal anchors."""
        # 1. payment_recovery
        rec_content, _ = GovernedCommunicationTemplates.render_content(
            "payment_recovery",
            {"order_id": "ORD-123", "amount": 2999.0, "payment_link": "https://rzp.test/pay/1", "discount_limit": 10},
        )
        self.assertIn("₹2,999.00", rec_content)
        self.assertIn("10%", rec_content)
        self.assertIn("PCI-DSS compliant", rec_content)

        # 2. payout_approval
        payout_content, _ = GovernedCommunicationTemplates.render_content(
            "payout_approval",
            {"payout_id": "PO-99", "beneficiary_name": "Vendor Corp", "amount": 50000.0, "utr_reference": "UTR-999"},
        )
        self.assertIn("PO-99", payout_content)
        self.assertIn("₹50,000.00", payout_content)
        self.assertIn("UTR-999", payout_content)

        # 3. cashflow_alert
        cash_content, _ = GovernedCommunicationTemplates.render_content(
            "cashflow_alert",
            {"current_balance": 2800000.0, "burn_rate": 420000.0, "runway_months": 6.7, "forecasted_inflow": 150000.0},
        )
        self.assertIn("₹2,800,000.00", cash_content)
        self.assertIn("6.7 months", cash_content)

        # Missing required anchor raises ValueError
        with self.assertRaises(ValueError):
            GovernedCommunicationTemplates.render_content(
                "payment_recovery",
                {"order_id": "ORD-123"},  # missing amount, payment_link, discount_limit
            )

    def test_rest_api_communication_endpoints(self):
        """Verifies REST endpoints for preferences, consents, and dispatching."""
        # 1. GET preferences
        res_pref = self.client.get("/api/agent-runtime/communication/preferences/")
        self.assertEqual(res_pref.status_code, status.HTTP_200_OK)

        # 2. PATCH preferences
        res_patch = self.client.patch(
            "/api/agent-runtime/communication/preferences/",
            {"daily_frequency_limit": 8, "whatsapp_enabled": True},
            format="json",
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(res_patch.json()["daily_frequency_limit"], 8)

        # 3. POST consent
        res_consent = self.client.post(
            "/api/agent-runtime/communication/consents/",
            {"purpose": "ACCOUNT_UPDATES", "is_granted": True},
            format="json",
        )
        self.assertEqual(res_consent.status_code, status.HTTP_200_OK)
        self.assertTrue(res_consent.json()["is_granted"])

        # 4. POST send
        send_res = self.client.post(
            "/api/agent-runtime/communication/send/",
            {
                "channel": "EMAIL",
                "template_name": "payout_approval",
                "immutable_data": {
                    "payout_id": "PO-100",
                    "beneficiary_name": "Rahul",
                    "amount": 18500.0,
                    "utr_reference": "UTR-100",
                },
            },
            format="json",
        )
        self.assertEqual(send_res.status_code, status.HTTP_200_OK)
        self.assertTrue(send_res.json()["success"])

        # 5. GET events
        events_res = self.client.get("/api/agent-runtime/communication/events/")
        self.assertEqual(events_res.status_code, status.HTTP_200_OK)
        self.assertTrue(len(events_res.json()) > 0)
