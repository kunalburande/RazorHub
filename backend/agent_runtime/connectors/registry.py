import time
import logging
from typing import Dict, Any, Type, Optional
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from ..models import Connector, ConnectorCapability, ConnectorExecution, Agent
from .base import BaseConnector
from .implementations import (
    MockCommerceConnector,
    MockPaymentConnector,
    MockBankingConnector,
    MockAccountingConnector,
    MockEmailConnector,
    MockWhatsAppConnector,
    RazorpayTestModeConnector,
    GoogleSheetsConnector,
    GmailConnector,
    TelegramConnector,
)

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """
    Central registry and execution dispatcher for all system connectors.
    Enforces that agents cannot use connectors without explicit configuration.
    """
    _CONNECTOR_CLASSES: Dict[str, Type[BaseConnector]] = {
        MockCommerceConnector.slug: MockCommerceConnector,
        MockPaymentConnector.slug: MockPaymentConnector,
        MockBankingConnector.slug: MockBankingConnector,
        MockAccountingConnector.slug: MockAccountingConnector,
        MockEmailConnector.slug: MockEmailConnector,
        MockWhatsAppConnector.slug: MockWhatsAppConnector,
        RazorpayTestModeConnector.slug: RazorpayTestModeConnector,
        GoogleSheetsConnector.slug: GoogleSheetsConnector,
        GmailConnector.slug: GmailConnector,
        TelegramConnector.slug: TelegramConnector,
    }

    @classmethod
    def get_connector_instance(cls, slug: str) -> BaseConnector:
        conn_cls = cls._CONNECTOR_CLASSES.get(slug)
        if not conn_cls:
            raise ValueError(f"Unknown connector slug: '{slug}'")
        return conn_cls()

    @classmethod
    def seed_default_connectors(cls):
        """
        Populates DB records for the 10 standard connectors and their capabilities.
        """
        for slug, conn_cls in cls._CONNECTOR_CLASSES.items():
            connector, _ = Connector.objects.update_or_create(
                slug=slug,
                defaults={
                    "name": conn_cls.name,
                    "connector_type": conn_cls.connector_type,
                    "description": conn_cls.description,
                    "is_mock": conn_cls.is_mock,
                    "version": conn_cls.version,
                    "status": "ACTIVE",
                },
            )

            # Register capabilities
            for cap in conn_cls.supported_capabilities:
                ConnectorCapability.objects.get_or_create(
                    connector=connector,
                    name=f"{slug}_{cap.lower()}",
                    defaults={
                        "capability": cap,
                        "description": f"{cap} operation for {conn_cls.name}",
                    },
                )

    @classmethod
    def execute(
        cls,
        connector_slug: str,
        capability: str,
        action: str,
        params: Dict[str, Any],
        agent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Executes an action via a connector.
        Enforces agent-scoping: if agent_id is provided, verifies that the agent
        has this connector in agent.connectors.
        Records execution in ConnectorExecution.
        """
        cls.seed_default_connectors()

        connector_db = Connector.objects.filter(slug=connector_slug).first()
        if not connector_db:
            raise ValueError(f"Connector '{connector_slug}' not found in database.")

        agent = None
        if agent_id:
            agent = Agent.objects.filter(id=agent_id).first()
            if not agent:
                raise ValueError(f"Agent '{agent_id}' not found.")

        instance = cls.get_connector_instance(connector_slug)

        start_time = time.time()
        status = "SUCCESS"
        error_msg = ""
        output_data = {}

        try:
            # Enforce agent authorization check
            instance.validate_agent_authorization(agent)
            instance.validate_capability(capability)

            output_data = instance.execute(capability=capability, action=action, params=params, agent=agent)
            return output_data
        except PermissionDenied as pe:
            status = "BLOCKED_BY_POLICY"
            error_msg = str(pe)
            raise pe
        except Exception as ex:
            status = "FAILED"
            error_msg = str(ex)
            raise ex
        finally:
            duration_ms = int((time.time() - start_time) * 1000)
            ConnectorExecution.objects.create(
                connector=connector_db,
                agent=agent,
                capability=capability.upper(),
                action_name=action,
                status=status,
                input_payload=params,
                output_payload=output_data,
                error_message=error_msg,
                duration_ms=duration_ms,
            )
