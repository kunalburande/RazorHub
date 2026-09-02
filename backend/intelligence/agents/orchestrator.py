"""
Orchestrator Agent — the central brain that classifies user intent
and routes to the correct specialized agent.
"""
import logging
from . import BaseAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    name = "orchestrator"

    # The specialized agents we can route to
    VALID_AGENTS = ["search", "shopping", "checkout", "upsell", "campaign", "order", "general"]

    def get_system_prompt(self, context: dict) -> str:
        platform = context.get("platform", "razorhub")
        return f"""You are an intent classification router for an AI commerce assistant.
Your ONLY job is to analyze the user's latest message and classify their intent.

Platform: {platform}
Available agents:
- "search": Product discovery, finding items, comparing products, browsing catalog, checking availability
- "shopping": Cart operations, adding items, deals, discounts, summarize cart
- "checkout": Express checkout, generating payment links, confirming orders, completing purchases
- "upsell": Product upgrades, complementary accessories, cross-selling, "frequently bought together"
- "campaign": Seller promotional campaigns, creating discounts, setting budgets, marketing analytics (seller/merchant mode)
- "order": Order status, shipping, returns, payment methods, delivery tracking, account/support questions
- "general": Greetings, about the platform, founder questions, general conversation, anything that doesn't fit above

You MUST respond with ONLY a valid JSON object, nothing else:
{{"agent": "<agent_name>", "reasoning": "<one sentence why>", "refined_query": "<the user's core question rephrased clearly>"}}"""

    def _fallback_classification(self, last_content: str) -> str:
        """Heuristic-based intent classification if LLM is offline or timed out."""
        text = last_content.lower()
        if any(k in text for k in ["campaign", "promo", "budget", "burn rate", "seller marketing", "run a sale", "launch promo"]):
            return "campaign"
        if any(k in text for k in ["upgrade", "accessory", "accessories", "compatible with", "goes well with", "frequently bought", "bundle"]):
            return "upsell"
        if any(k in text for k in ["cart", "deal", "discount", "offer", "recommend", "suggest", "add to cart", "basket"]):
            return "shopping"
        if any(k in text for k in ["pay", "checkout", "buy now", "purchase", "upi", "payment link", "bill"]):
            return "checkout"
        if any(k in text for k in ["deliver", "ship", "track", "order status", "return", "refund", "support", "help", "contact", "policy", "service"]):
            return "order"
        if any(k in text for k in ["about razorhub", "what is", "hello", "hi", "hey", "who are you", "what can you do"]):
            return "general"
        # Default to search if looking for products
        return "search"

    def execute(self, messages: list[dict], context: dict) -> dict:
        """
        Classify the user's intent and return the routing decision.
        """
        last_content = messages[-1].get("content", "") if messages else ""
        try:
            result = self.call_gemini_json(messages, context, temperature=0.1)

            agent = result.get("agent", "general")
            if agent not in self.VALID_AGENTS:
                agent = self._fallback_classification(last_content)

            return {
                "agent": agent,
                "reasoning": result.get("reasoning", "Classified by LLM"),
                "refined_query": result.get("refined_query", last_content),
            }
        except Exception as e:
            logger.info(f"Orchestrator using heuristic classification: {e}")
            agent = self._fallback_classification(last_content)
            return {
                "agent": agent,
                "reasoning": f"Routed to {agent} via heuristic fallback",
                "refined_query": last_content,
            }

