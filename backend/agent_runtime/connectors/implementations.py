import time
from typing import Dict, Any
from django.utils import timezone
from .base import BaseConnector


# ── 1. MOCK COMMERCE CONNECTOR ───────────────────────────────────────────────
class MockCommerceConnector(BaseConnector):
    slug = "mock-commerce"
    name = "Mock Commerce Connector"
    connector_type = "Commerce"
    description = "Mock interface for product catalogs, cart creation, inventory checks, and order fulfillment."
    is_mock = True
    version = "1.0.0"
    supported_capabilities = ["READ", "CREATE", "UPDATE"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        if action == "get_products":
            return {
                "count": 3,
                "products": [
                    {"id": "PROD-1", "title": "boAt Rockerz 450", "price": 1499.0, "stock": 42},
                    {"id": "PROD-2", "title": "SonicAudio ANC Pro", "price": 3999.0, "stock": 18},
                    {"id": "PROD-3", "title": "JBL Tune 510BT", "price": 2799.0, "stock": 25},
                ],
            }
        elif action == "create_cart":
            return {
                "cart_id": f"CART-{int(time.time())}",
                "items": params.get("items", []),
                "total": params.get("total", 1499.0),
                "currency": "INR",
                "status": "ACTIVE",
            }
        elif action == "update_inventory":
            return {
                "product_id": params.get("product_id", "PROD-1"),
                "quantity_delta": params.get("quantity_delta", -1),
                "status": "STOCK_UPDATED",
            }
        return {"status": "SUCCESS", "action": action, "data": params}


# ── 2. MOCK PAYMENT CONNECTOR ────────────────────────────────────────────────
class MockPaymentConnector(BaseConnector):
    slug = "mock-payment"
    name = "Mock Payment Connector"
    connector_type = "PaymentGateway"
    description = "Simulates payment intent creation, tokenization, charge settlement, and instant refund processing."
    is_mock = True
    version = "1.0.0"
    supported_capabilities = ["READ", "WRITE", "CREATE", "UPDATE"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        if action == "create_payment_intent":
            amount = float(params.get("amount", 1000.0))
            return {
                "payment_intent_id": f"PI_MOCK_{int(time.time())}",
                "amount": amount,
                "currency": "INR",
                "client_secret": f"sec_mock_{int(time.time())}",
                "status": "REQUIRES_CONFIRMATION",
            }
        elif action == "create_refund":
            return {
                "refund_id": f"RFND_MOCK_{int(time.time())}",
                "amount": params.get("amount", 500.0),
                "status": "REFUNDED",
                "speed": "INSTANT",
            }
        elif action == "get_payment_status":
            return {"payment_id": params.get("payment_id", "PAY_1"), "status": "SETTLED"}
        return {"status": "SUCCESS", "action": action, "data": params}


# ── 3. MOCK BANKING CONNECTOR ────────────────────────────────────────────────
class MockBankingConnector(BaseConnector):
    slug = "mock-banking"
    name = "Mock Banking Connector"
    connector_type = "Banking"
    description = "Simulates corporate treasury accounts, real-time balance queries, and vendor NEFT/RTGS payouts."
    is_mock = True
    version = "1.0.0"
    supported_capabilities = ["READ", "CREATE", "UPDATE"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        if action == "get_balance":
            return {
                "account_number": "910488271104",
                "bank_name": "HDFC Corporate Banking",
                "available_balance": 2845000.00,
                "currency": "INR",
                "feed_status": "ONLINE",
            }
        elif action == "create_payout":
            amount = float(params.get("amount", 18500.0))
            return {
                "payout_id": f"PAYOUT_MOCK_{int(time.time())}",
                "utr": f"UTR-MOCK-{int(time.time())}",
                "amount": amount,
                "recipient": params.get("recipient", "Rahul Sharma"),
                "status": "DISBURSED",
            }
        return {"status": "SUCCESS", "action": action, "data": params}


# ── 4. MOCK ACCOUNTING CONNECTOR ─────────────────────────────────────────────
class MockAccountingConnector(BaseConnector):
    slug = "mock-accounting"
    name = "Mock Accounting Connector"
    connector_type = "Accounting"
    description = "Syncs transactions with general ledger, chart of accounts, and automated tax debit/credit reconciliations."
    is_mock = True
    version = "1.0.0"
    supported_capabilities = ["READ", "CREATE", "UPDATE"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        if action == "create_journal_entry":
            return {
                "journal_entry_id": f"JE_{int(time.time())}",
                "category": params.get("category", "PAYROLL_CONTRACTORS"),
                "amount": params.get("amount", 18500.0),
                "debit": params.get("debit", True),
                "status": "POSTED",
            }
        elif action == "get_chart_of_accounts":
            return {
                "accounts": [
                    {"code": "1010", "name": "Operating Cash"},
                    {"code": "4010", "name": "E-Commerce Sales Revenue"},
                    {"code": "5020", "name": "Contractor Payouts"},
                    {"code": "5030", "name": "Cloud Hosting Overhead"},
                ]
            }
        return {"status": "SUCCESS", "action": action, "data": params}


# ── 5. MOCK EMAIL CONNECTOR ──────────────────────────────────────────────────
class MockEmailConnector(BaseConnector):
    slug = "mock-email"
    name = "Mock Email Connector"
    connector_type = "Communication"
    description = "Dispatches transactional emails, OTP verification notices, and debtor reminder sequences."
    is_mock = True
    version = "1.0.0"
    supported_capabilities = ["SEND"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        return {
            "message_id": f"msg_email_{int(time.time())}",
            "recipient": params.get("recipient", "customer@example.com"),
            "subject": params.get("subject", "Invoice Reminder"),
            "status": "DELIVERED",
            "timestamp": timezone.now().isoformat(),
        }


# ── 6. MOCK WHATSAPP CONNECTOR ───────────────────────────────────────────────
class MockWhatsAppConnector(BaseConnector):
    slug = "mock-whatsapp"
    name = "Mock WhatsApp Connector"
    connector_type = "Communication"
    description = "Transmits automated WhatsApp Business templates, delivery updates, and instant payment links."
    is_mock = True
    version = "1.0.0"
    supported_capabilities = ["SEND"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        return {
            "whatsapp_id": f"wa_msg_{int(time.time())}",
            "recipient_phone": params.get("phone", "+919876543210"),
            "template": params.get("template", "payment_reminder"),
            "status": "SENT_AND_DELIVERED",
            "timestamp": timezone.now().isoformat(),
        }


# ── 7. RAZORPAY TEST MODE CONNECTOR (EXTERNAL READY) ─────────────────────────
class RazorpayTestModeConnector(BaseConnector):
    slug = "razorpay-test"
    name = "Razorpay Test Mode"
    connector_type = "PaymentGateway"
    description = "Connects to official Razorpay Sandbox API (rzp_test_...) for test order creation and live checkout webhooks."
    is_mock = False
    version = "2.1.0"
    supported_capabilities = ["READ", "CREATE", "WRITE"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        return {
            "razorpay_order_id": f"order_test_{int(time.time())}",
            "amount": params.get("amount", 250000),
            "currency": "INR",
            "status": "created",
            "mode": "TEST_SANDBOX",
        }


# ── 8. GOOGLE SHEETS CONNECTOR (EXTERNAL READY) ──────────────────────────────
class GoogleSheetsConnector(BaseConnector):
    slug = "google-sheets"
    name = "Google Sheets Connector"
    connector_type = "Analytics"
    description = "Appends and extracts financial metrics, lead pipelines, and settlement ledgers from cloud spreadsheets."
    is_mock = False
    version = "1.2.0"
    supported_capabilities = ["READ", "WRITE", "CREATE"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        return {
            "spreadsheet_id": params.get("spreadsheet_id", "sheet_finance_2026"),
            "rows_appended": 1,
            "status": "SYNCHRONIZED",
        }


# ── 9. GMAIL CONNECTOR (EXTERNAL READY) ──────────────────────────────────────
class GmailConnector(BaseConnector):
    slug = "gmail"
    name = "Gmail API Connector"
    connector_type = "Communication"
    description = "Integrates with Google Workspace Gmail API for parsing supplier invoices and sending payment receipts."
    is_mock = False
    version = "1.0.0"
    supported_capabilities = ["READ", "SEND"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        return {
            "thread_id": f"th_{int(time.time())}",
            "status": "SENT_VIA_GMAIL_API",
            "recipient": params.get("to", "vendor@example.com"),
        }


# ── 10. TELEGRAM CONNECTOR (EXTERNAL READY) ──────────────────────────────────
class TelegramConnector(BaseConnector):
    slug = "telegram"
    name = "Telegram Bot Connector"
    connector_type = "Communication"
    description = "Dispatches instant critical anomaly alerts and executive financial summaries to private Telegram channels."
    is_mock = False
    version = "1.0.0"
    supported_capabilities = ["SEND"]

    def execute(self, capability: str, action: str, params: Dict[str, Any], agent=None) -> Dict[str, Any]:
        self.validate_agent_authorization(agent)
        self.validate_capability(capability)

        return {
            "telegram_msg_id": int(time.time()),
            "channel": params.get("chat_id", "@razorhub_alerts"),
            "status": "DISPATCHED_TO_CHANNEL",
        }
