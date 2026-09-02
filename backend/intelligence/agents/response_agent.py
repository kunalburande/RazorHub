"""
Response Agent — takes raw agent outputs and generates polished customer-facing messages.
Also handles "general" queries (greetings, about, founder, etc.) directly.
"""
import logging
from . import BaseAgent

logger = logging.getLogger(__name__)


class ResponseAgent(BaseAgent):
    name = "response"

    def get_system_prompt(self, context: dict) -> str:
        platform = context.get("platform", "razorhub")

        return f"""You are RazorHub AI (also called Kinu AI), a friendly and knowledgeable e-commerce and shopping assistant.
You help customers exclusively with shopping, product discovery, order support, store information, delivery, and services.

Platform: {platform}

CRITICAL FACTS (always use these, never invent):
- Platform name: RazorHub.
- Purpose: Assisting customers with product discovery, cart management, deals, delivery questions, and order service doubts.
- Support email: razorhubofficial@gmail.com
- Currency: Indian Rupee (₹ / INR).
- The AI assistant is called RazorHub AI / Kinu AI.
- Scope: Keep answers strictly focused on shopping, product details, orders, delivery, store queries, and customer services.

Response formatting:
- Use **bold** for emphasis on product names, prices, and key info.
- Keep responses concise (2-5 sentences max).
- Be friendly, professional, and helpful.
- When mentioning products, always include [PRODUCT:slug] tags.
- When the user wants to add something to cart, use [ADD_TO_CART:slug] tags."""

    def execute(self, messages: list[dict], context: dict) -> dict:
        """Handle general queries directly."""
        last_query = messages[-1].get("content", "").lower() if messages else ""

        try:
            content = self.call_gemini(messages, context)
            return {"content": content}
        except Exception as e:
            logger.info(f"Response agent fallback: {e}")

            if "who made" in last_query or "founder" in last_query or "creator" in last_query or "who are you" in last_query or "what are you" in last_query:
                return {
                    "content": "I am **RazorHub AI**, your e-commerce shopping assistant! 🛍️\n\nI'm here to help you search products, discover discounts, manage your cart, and answer any questions about our delivery, checkout, and merchant services."
                }

            if "delivery" in last_query or "shipping" in last_query:
                return {
                    "content": "📦 **RazorHub Fast Delivery:**\n• Standard delivery within **1–3 business days**.\n• **Free delivery** on all orders above **₹5,000** (otherwise ₹150 flat fee).\n• Live tracking is provided for every order!"
                }

            return {
                "content": "Hey there! 👋 I'm **RazorHub AI**, your shopping companion. Ask me to find products, summarize your cart, check deals, or answer any doubts about our services! 🛍️"
            }
