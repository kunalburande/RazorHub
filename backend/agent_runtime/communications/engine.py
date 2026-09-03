import time
from datetime import timedelta
from typing import Dict, Any, Optional
from django.utils import timezone
from django.contrib.auth import get_user_model

from ..models import (
    CommunicationConsent,
    CommunicationPreference,
    CommunicationEvent,
    CommunicationChannel,
    CommunicationEventStatus,
    Agent,
)
from .templates import GovernedCommunicationTemplates
from .channels import (
    EmailChannelProvider,
    SmsChannelProvider,
    WhatsAppChannelProvider,
    InAppChannelProvider,
    TelegramChannelProvider,
)

User = get_user_model()


class CommunicationEngine:
    """
    Central Outbound Communication Layer & Governance Firewall.
    Enforces a strict 6-step pre-flight check before any message reaches a recipient.
    """

    @classmethod
    def get_or_create_preferences(cls, user) -> CommunicationPreference:
        pref, _ = CommunicationPreference.objects.get_or_create(user=user)
        return pref

    @classmethod
    def dispatch(
        cls,
        user,
        channel: str,
        template_name: str,
        immutable_data: Dict[str, Any],
        recipient: Optional[str] = None,
        agent: Optional[Agent] = None,
        personal_greeting: str = "",
    ) -> Dict[str, Any]:
        """
        Executes outbound communication with 6-step pre-flight verification:
        1. check user consent
        2. check channel permission
        3. check opt-out state
        4. check agent permission
        5. check frequency limit
        6. create communication audit record
        """
        start_time = time.time()
        channel_upper = channel.upper()

        # Render template content & retrieve mandatory purpose
        rendered_content, purpose = GovernedCommunicationTemplates.render_content(
            template_name=template_name,
            immutable_data=immutable_data,
            personal_greeting=personal_greeting,
        )

        effective_recipient = recipient
        if not effective_recipient and user:
            if channel_upper == "EMAIL":
                effective_recipient = getattr(user, "email", None) or str(user.id)
            elif channel_upper in ["SMS", "WHATSAPP"]:
                effective_recipient = getattr(user, "phone", None) or getattr(user, "email", None) or str(user.id)
            else:
                effective_recipient = str(user.id)
        if not effective_recipient:
            effective_recipient = "unknown_recipient"

        # Get or create user preferences
        pref = cls.get_or_create_preferences(user)

        # ── STEP 1: CHECK OPT-OUT STATE ──────────────────────────────────────
        # Agents must not repeatedly contact users who have opted out.
        if pref.is_opted_out_all:
            duration_ms = int((time.time() - start_time) * 1000)
            event = CommunicationEvent.objects.create(
                user=user,
                agent=agent,
                channel=channel_upper,
                purpose=purpose,
                template_name=template_name,
                recipient=effective_recipient,
                rendered_content=rendered_content,
                status=CommunicationEventStatus.BLOCKED_OPTED_OUT,
                immutable_data=immutable_data,
                blocked_reason="User has enabled global opt-out (is_opted_out_all=True). Outbound communication halted.",
                duration_ms=duration_ms,
            )
            return {
                "success": False,
                "status": CommunicationEventStatus.BLOCKED_OPTED_OUT,
                "event_id": str(event.id),
                "reason": event.blocked_reason,
            }

        # ── STEP 2: CHECK USER CONSENT ───────────────────────────────────────
        # Ensure active, unrevoked consent exists for this purpose
        consent = CommunicationConsent.objects.filter(
            user=user,
            purpose=purpose,
            is_granted=True,
            revoked_at__isnull=True,
        ).first()

        if not consent:
            duration_ms = int((time.time() - start_time) * 1000)
            event = CommunicationEvent.objects.create(
                user=user,
                agent=agent,
                channel=channel_upper,
                purpose=purpose,
                template_name=template_name,
                recipient=effective_recipient,
                rendered_content=rendered_content,
                status=CommunicationEventStatus.BLOCKED_NO_CONSENT,
                immutable_data=immutable_data,
                blocked_reason=f"User has not granted active consent for purpose '{purpose}'.",
                duration_ms=duration_ms,
            )
            return {
                "success": False,
                "status": CommunicationEventStatus.BLOCKED_NO_CONSENT,
                "event_id": str(event.id),
                "reason": event.blocked_reason,
            }

        # ── STEP 3: CHECK CHANNEL PERMISSION ─────────────────────────────────
        if not pref.is_channel_enabled(channel_upper):
            duration_ms = int((time.time() - start_time) * 1000)
            event = CommunicationEvent.objects.create(
                user=user,
                agent=agent,
                channel=channel_upper,
                purpose=purpose,
                template_name=template_name,
                recipient=effective_recipient,
                rendered_content=rendered_content,
                status=CommunicationEventStatus.BLOCKED_CHANNEL_DISABLED,
                immutable_data=immutable_data,
                blocked_reason=f"Channel '{channel_upper}' is disabled in user communication preferences.",
                duration_ms=duration_ms,
            )
            return {
                "success": False,
                "status": CommunicationEventStatus.BLOCKED_CHANNEL_DISABLED,
                "event_id": str(event.id),
                "reason": event.blocked_reason,
            }

        # ── STEP 4: CHECK AGENT PERMISSION ───────────────────────────────────
        if agent is not None:
            if agent.status != "ACTIVE":
                duration_ms = int((time.time() - start_time) * 1000)
                event = CommunicationEvent.objects.create(
                    user=user,
                    agent=agent,
                    channel=channel_upper,
                    purpose=purpose,
                    template_name=template_name,
                    recipient=effective_recipient,
                    rendered_content=rendered_content,
                    status=CommunicationEventStatus.BLOCKED_AGENT_PERMISSION,
                    immutable_data=immutable_data,
                    blocked_reason=f"Agent '{agent.name}' is not in ACTIVE status (current: {agent.status}).",
                    duration_ms=duration_ms,
                )
                return {
                    "success": False,
                    "status": CommunicationEventStatus.BLOCKED_AGENT_PERMISSION,
                    "event_id": str(event.id),
                    "reason": event.blocked_reason,
                }

        # ── STEP 5: CHECK FREQUENCY LIMIT ────────────────────────────────────
        past_24h = timezone.now() - timedelta(hours=24)
        recent_count = CommunicationEvent.objects.filter(
            user=user,
            created_at__gte=past_24h,
            status=CommunicationEventStatus.DISPATCHED,
        ).count()

        if recent_count >= pref.daily_frequency_limit:
            duration_ms = int((time.time() - start_time) * 1000)
            event = CommunicationEvent.objects.create(
                user=user,
                agent=agent,
                channel=channel_upper,
                purpose=purpose,
                template_name=template_name,
                recipient=effective_recipient,
                rendered_content=rendered_content,
                status=CommunicationEventStatus.BLOCKED_FREQUENCY_LIMIT,
                immutable_data=immutable_data,
                blocked_reason=f"Daily frequency limit reached ({recent_count}/{pref.daily_frequency_limit} sent in past 24h).",
                duration_ms=duration_ms,
            )
            return {
                "success": False,
                "status": CommunicationEventStatus.BLOCKED_FREQUENCY_LIMIT,
                "event_id": str(event.id),
                "reason": event.blocked_reason,
            }

        # ── DISPATCH TO CHANNEL PROVIDER ─────────────────────────────────────
        dispatch_result = {}
        try:
            if channel_upper == CommunicationChannel.EMAIL:
                dispatch_result = EmailChannelProvider.dispatch(
                    recipient=effective_recipient,
                    subject=f"RazorHub Notice: {template_name.replace('_', ' ').title()}",
                    content=rendered_content,
                    user=user,
                )
            elif channel_upper == CommunicationChannel.SMS:
                dispatch_result = SmsChannelProvider.dispatch(
                    recipient=effective_recipient,
                    content=rendered_content,
                    user=user,
                )
            elif channel_upper == CommunicationChannel.WHATSAPP:
                dispatch_result = WhatsAppChannelProvider.dispatch(
                    recipient=effective_recipient,
                    content=rendered_content,
                    user=user,
                )
            elif channel_upper == CommunicationChannel.IN_APP:
                dispatch_result = InAppChannelProvider.dispatch(
                    recipient=effective_recipient,
                    content=rendered_content,
                    user=user,
                )
            elif channel_upper == CommunicationChannel.TELEGRAM:
                chat_id = pref.telegram_chat_id or effective_recipient
                dispatch_result = TelegramChannelProvider.dispatch(
                    recipient=chat_id,
                    content=rendered_content,
                    user=user,
                )
            else:
                raise ValueError(f"Unsupported channel: '{channel_upper}'")
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            event = CommunicationEvent.objects.create(
                user=user,
                agent=agent,
                channel=channel_upper,
                purpose=purpose,
                template_name=template_name,
                recipient=effective_recipient,
                rendered_content=rendered_content,
                status=CommunicationEventStatus.FAILED,
                immutable_data=immutable_data,
                blocked_reason=str(e),
                duration_ms=duration_ms,
            )
            return {
                "success": False,
                "status": CommunicationEventStatus.FAILED,
                "event_id": str(event.id),
                "error": str(e),
            }

        # ── STEP 6: CREATE COMMUNICATION AUDIT RECORD ────────────────────────
        duration_ms = int((time.time() - start_time) * 1000)
        event = CommunicationEvent.objects.create(
            user=user,
            agent=agent,
            channel=channel_upper,
            purpose=purpose,
            template_name=template_name,
            recipient=effective_recipient,
            rendered_content=rendered_content,
            status=CommunicationEventStatus.DISPATCHED,
            immutable_data=immutable_data,
            duration_ms=duration_ms,
        )

        return {
            "success": True,
            "status": CommunicationEventStatus.DISPATCHED,
            "event_id": str(event.id),
            "channel": channel_upper,
            "recipient": effective_recipient,
            "rendered_content": rendered_content,
            "provider_result": dispatch_result,
            "duration_ms": duration_ms,
        }
