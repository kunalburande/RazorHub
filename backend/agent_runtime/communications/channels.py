import logging
from typing import Dict, Any
from crm.models import Notification

logger = logging.getLogger(__name__)


class EmailChannelProvider:
    @staticmethod
    def dispatch(recipient: str, subject: str, content: str, user=None) -> Dict[str, Any]:
        logger.info(f"[OUTBOUND EMAIL] To: {recipient} | Subject: {subject}\n{content}")
        return {"channel": "EMAIL", "recipient": recipient, "provider": "mock_smtp_logger", "status": "DELIVERED"}


class SmsChannelProvider:
    @staticmethod
    def dispatch(recipient: str, content: str, user=None) -> Dict[str, Any]:
        logger.info(f"[OUTBOUND SMS] To: {recipient}\n{content}")
        return {"channel": "SMS", "recipient": recipient, "provider": "mock_telecom_sms", "status": "DELIVERED"}


class WhatsAppChannelProvider:
    @staticmethod
    def dispatch(recipient: str, content: str, user=None) -> Dict[str, Any]:
        logger.info(f"[OUTBOUND WHATSAPP] To: {recipient}\n{content}")
        return {"channel": "WHATSAPP", "recipient": recipient, "provider": "mock_meta_cloud_api", "status": "DELIVERED"}


class InAppChannelProvider:
    @staticmethod
    def dispatch(recipient: str, content: str, user=None) -> Dict[str, Any]:
        """
        Real application notification: persists directly to crm.models.Notification for the user.
        """
        if user:
            notif = Notification.objects.create(
                user=user,
                notification_type="status",
                body=content[:500],  # truncated summary for body if needed
            )
            return {
                "channel": "IN_APP",
                "notification_id": notif.id,
                "user_id": user.id,
                "status": "DELIVERED",
                "real_notification": True,
            }
        return {"channel": "IN_APP", "status": "SKIPPED_NO_USER"}


class TelegramChannelProvider:
    @staticmethod
    def dispatch(recipient: str, content: str, user=None) -> Dict[str, Any]:
        logger.info(f"[OUTBOUND TELEGRAM BOT] Chat: {recipient}\n{content}")
        return {"channel": "TELEGRAM", "recipient": recipient, "provider": "mock_telegram_bot", "status": "DELIVERED"}
