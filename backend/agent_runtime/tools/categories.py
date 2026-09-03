from enum import Enum


class ToolCategory(str, Enum):
    PAYMENTS = "PAYMENTS"
    ORDERS = "ORDERS"
    CUSTOMERS = "CUSTOMERS"
    REFUNDS = "REFUNDS"
    INVOICES = "INVOICES"
    SUBSCRIPTIONS = "SUBSCRIPTIONS"
    BANKING = "BANKING"
    PAYOUTS = "PAYOUTS"
    REPORTING = "REPORTING"
    COMMUNICATION = "COMMUNICATION"
    ANALYTICS = "ANALYTICS"
    RISK = "RISK"

    def __str__(self):
        return self.value
