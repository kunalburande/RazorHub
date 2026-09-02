"""
Order Agent — handles order status, shipping, returns, payment, support.
"""
import logging
from . import BaseAgent

logger = logging.getLogger(__name__)


class OrderAgent(BaseAgent):
    name = "order"
    model_name = "gemini-1.5-flash"

    def get_system_prompt(self, context: dict) -> str:
        platform = context.get("platform", "razorhub")

        return f"""You are a customer support specialist for an e-commerce platform called RazorHub.
You handle queries about orders, shipping, returns, payments, and account issues.

Platform: {platform}

FACTUAL INFORMATION (always answer from these, never invent):
- Payment methods: Razorpay (UPI, Credit/Debit Cards, NetBanking, Wallets) and Cash on Delivery (COD).
- Shipping: Base delivery fee ₹150. Free shipping on orders above ₹5,000.
- Estimated delivery: 1-3 business days within Kathmandu Valley, 3-7 days outside.
- Carriers: Pathao, In-house Delivery.
- Returns: 7-day return window. Items must be unused and in original packaging.
- Non-returnable: Groceries, beauty products, innerwear.
- Refund: Original payment method or Store Credit.
- Support email: razorhubofficial@gmail.com
- Accounts: Register with email + OTP verification, or Google login.

Guidelines:
- Be empathetic and professional.
- Always provide the support email if the user needs human help.
- Keep responses concise and actionable.
- If you don't have specific order details, tell them to check their dashboard or contact support."""

    def execute(self, messages: list[dict], context: dict) -> dict:
        """Handle order and support queries."""
        try:
            content = self.call_gemini(messages, context)
            return {"content": content}
        except Exception as e:
            logger.error(f"Order agent failed: {e}")
            return {
                "content": "I can help with order inquiries! For specific order details, "
                           "please check your dashboard at /dashboard or contact our support "
                           "team at **razorhubofficial@gmail.com**."
            }
