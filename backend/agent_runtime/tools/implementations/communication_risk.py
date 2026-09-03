from typing import Dict, Any
from ..base import BaseTool, ToolExecutionContext
from ..categories import ToolCategory
from ...models import RiskLevel
from ..providers.factory import get_communication_provider


class SendNotificationTool(BaseTool):
    id = "tool_send_notification"
    name = "sendNotification"
    description = "Dispatches communication to a customer or admin via email, SMS, or dashboard notice."
    category = ToolCategory.COMMUNICATION
    risk_level = RiskLevel.LOW
    requires_approval = False
    is_mutation = True
    required_permissions = ["seller", "admin", "all"]

    input_schema = {
        "type": "object",
        "properties": {
            "recipient": {"type": "string", "description": "Email address or phone number"},
            "channel": {"type": "string", "description": "email, sms, push"},
            "message": {"type": "string", "description": "Message text"},
            "idempotency_key": {"type": "string"},
        },
        "required": ["recipient", "message"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "recipient": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["id", "recipient", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_communication_provider()
        return provider.send_notification(
            recipient=input_data["recipient"],
            channel=input_data.get("channel", "email"),
            message=input_data["message"],
        )


class CreateAlertTool(BaseTool):
    id = "tool_create_alert"
    name = "createAlert"
    description = "Raises a risk alert or operational flag for anomalies or security events."
    category = ToolCategory.RISK
    risk_level = RiskLevel.MEDIUM
    requires_approval = False
    is_mutation = True
    required_permissions = ["seller", "admin", "all"]

    input_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "description": {"type": "string"},
            "severity": {"type": "string", "description": "INFO, WARNING, ERROR, CRITICAL"},
            "target_entity": {"type": "string"},
            "idempotency_key": {"type": "string"},
        },
        "required": ["title", "description"],
    }
    output_schema = {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "title": {"type": "string"},
            "severity": {"type": "string"},
            "status": {"type": "string"},
        },
        "required": ["id", "title", "severity", "status"],
    }

    def execute(self, input_data: Dict[str, Any], context: ToolExecutionContext) -> Dict[str, Any]:
        provider = get_communication_provider()
        return provider.create_alert(
            title=input_data["title"],
            description=input_data["description"],
            severity=input_data.get("severity", "MEDIUM"),
            target_entity=input_data.get("target_entity", "system"),
        )
