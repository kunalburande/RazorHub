"""
Campaign Orchestrator Agent for RazorHub Seller / Merchant AI.

Empowers sellers to plan, create, monitor, and optimize promotions with:
  • Segment-based targeting (Cart abandoners, High-value, Dormant, New customers)
  • Budget-bounded campaign limits (auto-pause on exhaustion)
  • Real-time ROI and budget burn monitoring
  • Explainability and audit trails
"""
import re
import logging
from decimal import Decimal
from . import BaseAgent
from intelligence.services.campaign_intelligence import CampaignIntelligenceService
from intelligence.models import Campaign, MerchantConfig

logger = logging.getLogger(__name__)


class CampaignAgent(BaseAgent):
    name = "campaign"

    def get_system_prompt(self, context: dict) -> str:
        merchant_cfg = MerchantConfig.get_solo()
        active_campaigns = Campaign.objects.filter(active=True)[:5]
        campaigns_summary = "\n".join([
            f"- {c.name}: {c.discount_value}{'%' if c.discount_type=='percentage' else ' INR'} off | Budget: ₹{c.budget_limit:,.2f} | Spent: ₹{c.current_spend:,.2f} ({c.status})"
            for c in active_campaigns
        ]) if active_campaigns else "No active campaigns currently."

        return f"""You are the AI Campaign Orchestrator for RazorHub Seller.
You help merchants plan, launch, and monitor high-converting promotional campaigns.

Platform Rules:
- Maximum allowed discount: {merchant_cfg.max_discount_percent}%
- Supported segments: ["high_value", "cart_abandoners", "dormant_buyers", "new_customers", "all_customers"]
- Every campaign must have a defined budget limit (default ₹50,000).
- All campaigns auto-pause when the budget limit is reached to protect merchant margins.

Active Campaigns:
{campaigns_summary}

Your Capabilities:
1. Recommend campaigns based on seasonal events (e.g. Diwali, Flash Sale, Weekend Boost).
2. Create bounded campaigns when the seller requests one (e.g., "Run a 15% discount for cart abandoners with a ₹25,000 budget").
3. Report on current campaign performance, budget burn rate, and ROI.
4. Keep responses crisp, actionable, and structured with bold highlights and bullet points."""

    def execute(self, messages: list[dict], context: dict) -> dict:
        last_message = messages[-1].get("content", "") if messages else ""
        text_lower = last_message.lower()

        # Check for goal-driven post-purchase orchestration
        if any(w in text_lower for w in ["increase revenue", "purchased laptops", "post purchase", "orchestrat", "lifecycle sequence", "laptop buyers"]):
            from intelligence.services.campaign_orchestrator import AutonomousCampaignOrchestrator
            plan = AutonomousCampaignOrchestrator.compile_goal_driven_campaign(last_message)
            lines = [
                "🎯 **Autonomous Campaign Orchestrator — Goal-Driven Post-Purchase Lifecycle**\n",
                f"**Segment:** {plan['segment']}",
                f"**Goal:** {plan['goal']}\n",
                "**Eligible Products (Inventory Verified):**"
            ]
            for p in plan["eligible_products"]:
                lines.append(f"• **{p['name']}** — ₹{p['price']:,.0f} (Stock: {p['stock']}, Margin: {p['margin_percent']}%)")

            lines.append("\n**Hard Policy Constraints:**")
            for c in plan["constraints"]["summary"]:
                lines.append(f"• {c}")

            lines.append("\n**Dynamic Order-Triggered Cadence:**")
            for step in plan["cadence"]:
                act = step.get("action", step.get("event"))
                lines.append(f"• **{step['stage']}:** {act} *({step['timing_rationale']})*")

            lines.append("\n🔒 *Invariant: Campaign is dynamically generated and goal-driven, replacing static sequences.*")
            return {"content": "\n".join(lines), "campaign_plan": plan}

        # Check for campaign creation request
        if any(w in text_lower for w in ["create", "run", "launch", "start"]) and any(w in text_lower for w in ["campaign", "discount", "promo", "sale", "%", "off"]):
            return self._handle_create_campaign(last_message, messages, context)

        # Check for campaign performance/status query
        if any(w in text_lower for w in ["status", "performance", "metrics", "analytics", "how is", "report", "spend", "budget"]):
            return self._handle_performance_report(context)

        # General campaign advisory / LLM fallback
        try:
            content = self.call_gemini(messages, context)
            return {"content": content}
        except Exception as e:
            logger.info(f"[CampaignAgent] Fallback execution: {e}")
            return self._fallback_advice()

    def _handle_create_campaign(self, text: str, messages: list[dict], context: dict) -> dict:
        """Parse campaign creation parameters from user request."""
        # Extract discount value
        discount_match = re.search(r'(\d+(?:\.\d+)?)\s*%', text)
        discount_val = Decimal(discount_match.group(1)) if discount_match else Decimal("10.00")

        # Extract budget
        budget_match = re.search(r'(?:budget|cap|limit)(?:\s+of)?\s*(?:₹|inr|rs\.?)?\s*(\d+(?:,\d+)*(?:\.\d+)?)', text, re.IGNORECASE)
        if budget_match:
            budget_str = budget_match.group(1).replace(",", "")
            budget_val = Decimal(budget_str)
        else:
            budget_val = Decimal("30000.00")

        # Extract target segment
        segments = ["all_customers"]
        if "abandon" in text.lower():
            segments = ["cart_abandoners"]
        elif "high value" in text.lower() or "vip" in text.lower():
            segments = ["high_value"]
        elif "dormant" in text.lower() or "inactive" in text.lower():
            segments = ["dormant_buyers"]
        elif "new" in text.lower() or "first" in text.lower():
            segments = ["new_customers"]

        # Derive campaign name
        name_clean = text.split(".")[0][:45]
        campaign_name = f"Promotion: {name_clean.strip()}"

        config = {
            "name": campaign_name,
            "campaign_type": "automated_promotion",
            "discount_type": "percentage",
            "discount_value": discount_val,
            "budget_limit": budget_val,
            "segments": segments,
            "duration_days": 7,
            "auto_pause_at_budget": True
        }

        res = CampaignIntelligenceService.create_campaign_from_ai(config, user=context.get("user"))

        if not res.get("success"):
            return {
                "content": f"⚠️ **Campaign not created**: {res.get('error')}\n\nPlease adjust the parameters and try again.",
                "campaign_status": "error"
            }

        seg_display = ", ".join([s.replace("_", " ").title() for s in segments])
        return {
            "content": (
                f"🚀 **Campaign Launched Successfully!**\n\n"
                f"• **Campaign ID:** `#{res['campaign_id']}`\n"
                f"• **Discount:** **{res['discount']} off**\n"
                f"• **Target Segment:** {seg_display}\n"
                f"• **Budget Cap:** **₹{res['budget_limit']:,.2f}** (Auto-pauses when reached)\n"
                f"• **Duration:** 7 Days\n\n"
                f"Razorpay tracked links have been generated for your buyer segments. "
                f"I will actively monitor conversion and alert you if the budget nears exhaustion."
            ),
            "toolCalls": [{
                "type": "campaign_summary",
                "campaign_id": res["campaign_id"],
                "name": res["name"],
                "discount": res["discount"],
                "budget_limit": res["budget_limit"],
                "segments": res["segments"]
            }]
        }

    def _handle_performance_report(self, context: dict) -> dict:
        """Generate a summary of all running and recent campaigns."""
        campaigns = Campaign.objects.all().order_by('-created_at')[:4]
        if not campaigns:
            return {
                "content": "You don't have any promotional campaigns active right now. Would you like me to recommend a high-impact campaign strategy for this week?"
            }

        lines = ["📊 **Campaign Performance Overview:**\n"]
        for c in campaigns:
            perf = CampaignIntelligenceService.get_campaign_performance(c.id)
            status_icon = "🟢" if c.status == "active" else ("⏸️" if c.status == "paused" else "⚪")
            lines.append(
                f"{status_icon} **{c.name}** (`{c.status.upper()}`)\n"
                f"  • Discount: **{c.discount_value}{'%' if c.discount_type=='percentage' else ' INR'}**\n"
                f"  • Budget Spent: **₹{perf['current_spend']:,.2f}** / ₹{perf['budget_limit']:,.2f} ({perf['budget_burn_pct']}%)\n"
                f"  • Remaining: **₹{perf['remaining_budget']:,.2f}**\n"
            )

        lines.append("Reply **create campaign** to launch a new targeted promotion!")
        return {"content": "\n".join(lines)}

    def _fallback_advice(self) -> dict:
        return {
            "content": (
                "💡 **Recommended Growth Strategies for Your Store:**\n\n"
                "1. **Cart Abandonment Recovery** — 10% discount for shoppers who left items in their cart.\n"
                "2. **VIP Reward** — 15% off for high-value repeat customers.\n"
                "3. **Clearance Booster** — Flat 20% off slow-moving inventory to free up warehouse space.\n\n"
                "Tell me which one you'd like to launch, e.g., *'Run a 10% discount for cart abandoners with a ₹20,000 budget'*"
            )
        }
