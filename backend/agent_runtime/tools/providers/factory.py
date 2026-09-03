import os
from django.conf import settings
from .interfaces import PaymentProvider, BankingProvider, CommunicationProvider
from .mock_payment_provider import MockPaymentProvider
from .razorpay_provider import RazorpayTestProvider
from .mock_banking_provider import MockBankingProvider
from .mock_communication_provider import MockCommunicationProvider

# Cached singleton provider instances
_payment_provider: PaymentProvider = None
_banking_provider: BankingProvider = None
_communication_provider: CommunicationProvider = None


def get_payment_provider() -> PaymentProvider:
    """
    Dependency injection factory resolving active PaymentProvider.
    Configurable via PAYMENT_PROVIDER environment variable ('mock', 'razorpay_test', 'auto').
    """
    global _payment_provider
    if _payment_provider is not None:
        return _payment_provider

    provider_name = os.environ.get("PAYMENT_PROVIDER") or getattr(settings, "PAYMENT_PROVIDER", "auto")
    provider_name = str(provider_name).lower()

    if provider_name == "razorpay_test":
        _payment_provider = RazorpayTestProvider()
    elif provider_name == "mock":
        _payment_provider = MockPaymentProvider()
    else:  # 'auto'
        key_id = getattr(settings, "RAZORPAY_KEY_ID", "") or os.environ.get("RAZORPAY_KEY_ID", "")
        if key_id:
            _payment_provider = RazorpayTestProvider()
        else:
            _payment_provider = MockPaymentProvider()

    return _payment_provider


def get_banking_provider() -> BankingProvider:
    """
    Dependency injection factory resolving active BankingProvider.
    Configurable via BANKING_PROVIDER environment variable.
    """
    global _banking_provider
    if _banking_provider is not None:
        return _banking_provider

    _banking_provider = MockBankingProvider()
    return _banking_provider


def get_communication_provider() -> CommunicationProvider:
    """
    Dependency injection factory resolving active CommunicationProvider.
    Configurable via COMMUNICATION_PROVIDER environment variable.
    """
    global _communication_provider
    if _communication_provider is not None:
        return _communication_provider

    _communication_provider = MockCommunicationProvider()
    return _communication_provider


def reset_providers():
    """Reset cached providers (useful for unit tests testing provider switching)."""
    global _payment_provider, _banking_provider, _communication_provider
    _payment_provider = None
    _banking_provider = None
    _communication_provider = None
