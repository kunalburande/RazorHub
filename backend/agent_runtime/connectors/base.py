from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from rest_framework.exceptions import PermissionDenied


class BaseConnector(ABC):
    """
    Abstract Base Class for all RazorHub Agentic Connectors.
    Enforces strict agent scoping and capability validation.
    """
    slug: str = ""
    name: str = ""
    connector_type: str = ""
    description: str = ""
    is_mock: bool = True
    version: str = "1.0.0"
    supported_capabilities: List[str] = []

    def validate_agent_authorization(self, agent) -> None:
        """
        Enforces rule: 'Agent configuration must specify which connectors an agent is allowed to use.
        Do not allow an agent to access every connector by default.'
        """
        if agent is None:
            # Direct system/admin execution is permitted if authenticated
            return

        # Check if this connector is explicitly attached to the agent
        is_allowed = agent.connectors.filter(slug=self.slug).exists()
        if not is_allowed:
            raise PermissionDenied(
                f"Access Prohibited: Agent '{agent.name}' is not authorized to use connector '{self.name}' ({self.slug}). "
                f"Attach this connector in Agent Configuration to grant access."
            )

    def validate_capability(self, capability: str) -> None:
        cap_upper = capability.upper()
        if cap_upper not in self.supported_capabilities:
            raise ValueError(
                f"Unsupported Capability: Connector '{self.name}' does not expose capability '{cap_upper}'. "
                f"Supported capabilities: {self.supported_capabilities}"
            )

    @abstractmethod
    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        """
        Executes action under the given capability.
        """
        pass
