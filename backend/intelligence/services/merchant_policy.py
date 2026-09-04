"""
Merchant Policy Engine — Deterministic Gating & Policy Language (DSL).

Enforces the centerpiece of RazorHub's "Explainable, Bounded, and Gated" AI architecture.
LLMs may reason and propose actions, but deterministic code strictly validates
money, discounts, margins, categories, and approval thresholds before execution.

Example:
    LLM Proposes:
      Offer: Phone + case
      Total: ₹32,698

    Merchant Policy:
      max autonomous order = ₹5,000

    Decision:
      BLOCKED → human confirmation required
"""
import re
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

DEFAULT_POLICY_YAML = """merchant_policy:
  max_discount: 10%
  max_autonomous_order_value: 5000
  max_items_per_order: 5
  min_margin_percent: 18%
  preferred_categories:
    - accessories
    - bundles
  forbidden_categories:
    - restricted_products
  auto_approval:
    under: 1500
  human_approval:
    from: 1500
    to: 5000
  human_required:
    above: 5000
"""

DEFAULT_POLICY_DICT: Dict[str, Any] = {
    "max_discount": Decimal("10.00"),
    "max_autonomous_order_value": Decimal("5000.00"),
    "max_items_per_order": 5,
    "min_margin_percent": Decimal("18.00"),
    "preferred_categories": ["accessories", "bundles"],
    "forbidden_categories": ["restricted_products"],
    "auto_approval_under": Decimal("1500.00"),
    "human_approval_from": Decimal("1500.00"),
    "human_approval_to": Decimal("5000.00"),
    "human_required_above": Decimal("5000.00"),
}


class MerchantPolicyEngine:
    """Deterministic policy enforcement engine for autonomous agent actions."""

    @classmethod
    def parse_policy_yaml(cls, yaml_text: str) -> Dict[str, Any]:
        """
        Parses declarative YAML policy into structured runtime rules.
        Uses robust regex parsing so external PyYAML dependencies are optional.
        """
        policy = dict(DEFAULT_POLICY_DICT)

        def extract_num(pattern, text, default=None):
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                clean = m.group(1).replace(',', '').replace('₹', '').replace('rs.', '').replace('%', '').strip()
                try:
                    return Decimal(clean)
                except Exception:
                    return default
            return default

        # Max discount
        d = extract_num(r'max_discount\s*:\s*([\d\.]+)%?', yaml_text)
        if d is not None:
            policy["max_discount"] = d

        # Max autonomous order value
        v = extract_num(r'max_autonomous_order_value\s*:\s*₹?\s*([\d\.,]+)', yaml_text)
        if v is not None:
            policy["max_autonomous_order_value"] = v

        # Max items
        i = extract_num(r'max_items_per_order\s*:\s*(\d+)', yaml_text)
        if i is not None:
            policy["max_items_per_order"] = int(i)

        # Min margin
        m_pct = extract_num(r'min_margin_percent\s*:\s*([\d\.]+)%?', yaml_text)
        if m_pct is not None:
            policy["min_margin_percent"] = m_pct

        # Auto approval under
        under = extract_num(r'auto_approval\s*:\s*(?:under\s*:\s*)?₹?\s*([\d\.,]+)', yaml_text)
        if under is not None:
            policy["auto_approval_under"] = under

        # Human required above
        above = extract_num(r'human_required\s*:\s*(?:above\s*:\s*)?₹?\s*([\d\.,]+)', yaml_text)
        if above is not None:
            policy["human_required_above"] = above

        return policy

    @classmethod
    def load_active_policy(cls) -> Dict[str, Any]:
        """Loads active merchant policy from database or returns default."""
        try:
            from intelligence.models import MerchantConfig
            cfg = MerchantConfig.get_solo()
            policy = dict(DEFAULT_POLICY_DICT)
            if hasattr(cfg, 'max_discount_percent') and cfg.max_discount_percent:
                policy["max_discount"] = Decimal(str(cfg.max_discount_percent))
            if hasattr(cfg, 'max_ai_order_value') and cfg.max_ai_order_value:
                # If custom max_ai_order_value exists, treat as max_autonomous_order_value
                policy["max_autonomous_order_value"] = Decimal(str(cfg.max_ai_order_value))
                policy["human_required_above"] = Decimal(str(cfg.max_ai_order_value))
            return policy
        except Exception as e:
            logger.warning(f"[PolicyEngine] Error loading policy from database: {e}")
            return dict(DEFAULT_POLICY_DICT)

    @classmethod
    def evaluate_proposal(
        cls,
        proposal: Dict[str, Any],
        policy: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deterministically evaluates an LLM or agent action proposal against merchant policy.

        Returns explainable decision dictionary:
            - allowed: bool (can the action execute autonomously right now?)
            - decision: str ("BLOCKED → human confirmation required" | "APPROVED → autonomous execution permitted")
            - status: "BLOCKED" | "GATED" | "APPROVED"
            - rule_violated: Optional[str]
            - limit_value: Optional[float]
            - proposed_value: Optional[float]
            - explanation: str
        """
        if policy is None:
            policy = cls.load_active_policy()

        items = proposal.get("items", [])
        total_price = Decimal(str(proposal.get("total_price", 0.0)))
        discount_pct = Decimal(str(proposal.get("discount_pct", 0.0)))
        margin_pct = Decimal(str(proposal.get("margin_pct", 30.0)))
        categories = proposal.get("categories", [])

        # ── 1. Items Limit Check ──────────────────────────────────────────────
        max_items = policy.get("max_items_per_order", 5)
        if len(items) > max_items:
            return {
                "allowed": False,
                "decision": "BLOCKED → items limit exceeded",
                "status": "BLOCKED",
                "rule_violated": "max_items_per_order",
                "limit_value": max_items,
                "proposed_value": len(items),
                "explanation": f"Policy limit: max {max_items} items per order. Proposed bundle contains {len(items)} items. Decision: BLOCKED.",
            }

        # ── 2. Discount Ceiling Check ─────────────────────────────────────────
        max_discount = policy.get("max_discount", Decimal("10.00"))
        if discount_pct > max_discount:
            return {
                "allowed": False,
                "decision": "BLOCKED → discount limit exceeded",
                "status": "BLOCKED",
                "rule_violated": "max_discount",
                "limit_value": float(max_discount),
                "proposed_value": float(discount_pct),
                "explanation": f"Policy limit: max discount = {max_discount}%. Proposed discount = {discount_pct}%. Decision: BLOCKED.",
            }

        # ── 3. Margin Floor Check ─────────────────────────────────────────────
        min_margin = policy.get("min_margin_percent", Decimal("18.00"))
        if margin_pct < min_margin:
            return {
                "allowed": False,
                "decision": "BLOCKED → margin floor violated",
                "status": "BLOCKED",
                "rule_violated": "min_margin_percent",
                "limit_value": float(min_margin),
                "proposed_value": float(margin_pct),
                "explanation": f"Policy limit: min margin = {min_margin}%. Proposed offer margin = {margin_pct}%. Decision: BLOCKED.",
            }

        # ── 4. Forbidden Category Check ───────────────────────────────────────
        forbidden = set(policy.get("forbidden_categories", []))
        if any(cat in forbidden for cat in categories):
            violation = [cat for cat in categories if cat in forbidden][0]
            return {
                "allowed": False,
                "decision": "BLOCKED → forbidden category",
                "status": "BLOCKED",
                "rule_violated": "forbidden_categories",
                "limit_value": None,
                "proposed_value": violation,
                "explanation": f"Category '{violation}' is restricted by merchant policy. Decision: BLOCKED.",
            }

        # ── 5. Autonomous Gating & Approval Tiers ─────────────────────────────
        max_autonomous = policy.get("max_autonomous_order_value", Decimal("5000.00"))
        human_required_above = policy.get("human_required_above", max_autonomous)
        auto_approval_under = policy.get("auto_approval_under", Decimal("1500.00"))
        human_approval_to = policy.get("human_approval_to", max_autonomous)

        # Tier 3: Hard Stop / Human Required (Total > ₹5,000)
        if total_price > human_required_above:
            return {
                "allowed": False,
                "decision": "BLOCKED → human confirmation required",
                "status": "BLOCKED",
                "tier": "HUMAN_REQUIRED",
                "rule_violated": "max_autonomous_order_value",
                "limit_value": float(human_required_above),
                "proposed_value": float(total_price),
                "explanation": (
                    f"Policy limit: max autonomous order = Rs.{human_required_above:,.0f}. "
                    f"Proposed offer total of Rs.{total_price:,.0f} exceeds limit. "
                    f"Decision: BLOCKED → human confirmation required."
                )
            }

        # Tier 2: Human Approval Window (e.g. ₹1,500 to ₹5,000)
        if total_price > auto_approval_under:
            return {
                "allowed": False,
                "decision": "GATED → merchant authorization pending",
                "status": "GATED",
                "tier": "HUMAN_APPROVAL",
                "rule_violated": "human_approval_window",
                "limit_value": float(auto_approval_under),
                "proposed_value": float(total_price),
                "explanation": (
                    f"Order value Rs.{total_price:,.0f} falls in the gated review tier "
                    f"(Rs.{auto_approval_under:,.0f} to Rs.{human_approval_to:,.0f}). "
                    f"Decision: GATED → merchant authorization pending."
                )
            }

        # Tier 1: Autonomous Auto-Approval (Total <= ₹1,500)
        return {
            "allowed": True,
            "decision": "APPROVED → autonomous execution permitted",
            "status": "APPROVED",
            "tier": "AUTO_APPROVAL",
            "rule_violated": None,
            "limit_value": float(auto_approval_under),
            "proposed_value": float(total_price),
            "explanation": (
                f"Order value Rs.{total_price:,.0f} is within autonomous threshold "
                f"(under Rs.{auto_approval_under:,.0f}). Decision: APPROVED."
            )
        }
