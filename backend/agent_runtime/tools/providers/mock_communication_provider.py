import uuid
import time
from typing import Dict, Any, Optional
from .interfaces import CommunicationProvider


class MockCommunicationProvider(CommunicationProvider):
    """
    Simulated communication and risk alert provider.
    """

    def __init__(self):
        self._notifications: list = []
        self._alerts: list = []

    def send_notification(self, recipient: str, channel: str, message: str, template: Optional[str] = None) -> Dict[str, Any]:
        msg_id = f"notif_mock_{uuid.uuid4().hex[:10]}"
        record = {
            "id": msg_id,
            "recipient": recipient,
            "channel": channel or "email",
            "message": message,
            "status": "delivered",
            "sent_at": int(time.time()),
        }
        self._notifications.append(record)
        return record

    def create_alert(self, severity: str, title: str, description: str, target_entity: Optional[str] = None) -> Dict[str, Any]:
        alert_id = f"alrt_mock_{uuid.uuid4().hex[:10]}"
        record = {
            "id": alert_id,
            "severity": severity.upper() if severity else "MEDIUM",
            "title": title,
            "description": description,
            "target_entity": target_entity or "system",
            "status": "active",
            "created_at": int(time.time()),
        }
        self._alerts.append(record)
        return record
