from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class PaymentProvider(ABC):
    """Abstract interface for payment gateway operations."""

    @abstractmethod
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def search_payments(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_payment_intent(self, amount: float, currency: str, customer_id: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_payment_link(self, amount: float, currency: str, customer_email: str, description: str = "", metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_refund(self, payment_id: str, amount: Optional[float] = None, reason: str = "") -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_refunds(self, payment_id: Optional[str] = None) -> List[Dict[str, Any]]:
        pass


class BankingProvider(ABC):
    """Abstract interface for banking, treasury, payouts, and settlements."""

    @abstractmethod
    def create_payout(self, recipient_account: str, amount: float, currency: str = "INR", narration: str = "") -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_payout(self, payout_id: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_settlement(self, settlement_id: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_cashflow(self, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
        pass


class CommunicationProvider(ABC):
    """Abstract interface for messaging, notifications, and risk alerts."""

    @abstractmethod
    def send_notification(self, recipient: str, channel: str, message: str, template: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def create_alert(self, severity: str, title: str, description: str, target_entity: Optional[str] = None) -> Dict[str, Any]:
        pass
