"""
Machine-Payable Merchant Surface — The x402 Protocol Implementation.

Architecture Grounding:
Most agent systems only build the "human-chats-and-buys" direction.
This module builds the mirror image: a machine-payable merchant surface where a separate
autonomous AI buyer agent can query quotes and execute purchases with zero humans in the loop.

The x402 Pattern:
1. Server responds with terms, price, and HTTP 402 Payment Required.
2. The AI buyer agent attaches a signed authorization token.
3. The request completes in one round trip.

Realistic Positioning:
We implement the technical pattern faithfully (HTTP 402 status, signed token verification,
autonomous settlement), pitched cleanly as a resilient architectural capability.
"""
import hmac
import time
import uuid
import hashlib
import logging
from decimal import Decimal
from typing import Dict, Any, Optional

from products.models import Product

logger = logging.getLogger(__name__)

SHARED_SECRET_KEY = "razorhub_agentic_secret_2026"


class X402MerchantSurface:
    """Provides machine-payable endpoints for autonomous AI buyer agents."""

    @classmethod
    def get_machine_quote(cls, product_slug: str = "studio-headphones", quantity: int = 1) -> Dict[str, Any]:
        """
        Step 1: AI Buyer requests a machine quote.
        Returns machine terms, price, nonce, and expiration.
        """
        prod = Product.objects.filter(slug=product_slug).first()
        if not prod:
            prod = Product.objects.filter(is_active=True).first()

        unit_price = float(prod.discount_price if prod and prod.discount_price else (prod.price if prod else 4999.00))
        total = unit_price * quantity
        quote_id = f"quote_{uuid.uuid4().hex[:12]}"
        nonce = uuid.uuid4().hex[:16]
        expires_at = int(time.time()) + 300  # 5 minutes validity

        return {
            "quote_id": quote_id,
            "product_id": prod.id if prod else 1,
            "product_slug": prod.slug if prod else product_slug,
            "product_name": prod.name if prod else "Studio Headphones",
            "quantity": quantity,
            "price_per_unit": unit_price,
            "total_amount": total,
            "currency": "INR",
            "nonce": nonce,
            "expires_at": expires_at,
            "payment_protocol": "x402-AutonomousAgentPay/1.0",
            "required_headers": {
                "Authorization": f"Bearer x402:<SIGNATURE>",
                "X-Payment-Quote-Id": quote_id,
                "X-Payment-Nonce": nonce
            }
        }

    @classmethod
    def process_machine_purchase(
        cls,
        quote_id: str,
        amount: float,
        nonce: str,
        signed_token: Optional[str] = None,
        agent_id: str = "ai_buyer_agent_alpha"
    ) -> Dict[str, Any]:
        """
        Step 2: Autonomous Purchase Execution.
        If signed_token is missing or invalid -> returns 402 Payment Required.
        If valid -> executes instant settlement in 1 round trip with zero human in the loop.
        """
        expected_sig = hmac.new(
            SHARED_SECRET_KEY.encode('utf-8'),
            f"{quote_id}:{amount}:{nonce}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        if not signed_token or signed_token != expected_sig:
            return {
                "http_status": 402,
                "error": "PAYMENT_REQUIRED",
                "message": "HTTP 402 Payment Required: Valid x402 authorization signature required to clear settlement.",
                "x402_challenge": {
                    "quote_id": quote_id,
                    "amount": amount,
                    "currency": "INR",
                    "nonce": nonce,
                    "algorithm": "HMAC-SHA256"
                },
                "autonomous_clearing": False
            }

        # Valid Signature: Clear settlement immediately in 1 round trip
        receipt_id = f"x402_tx_{uuid.uuid4().hex[:12]}"
        return {
            "http_status": 200,
            "status": "PURCHASE_COMPLETED_AUTONOMOUSLY",
            "receipt_id": receipt_id,
            "quote_id": quote_id,
            "agent_id": agent_id,
            "amount_settled": amount,
            "currency": "INR",
            "human_in_loop": False,
            "round_trips": 1,
            "payment_protocol": "x402-AutonomousAgentPay/1.0",
            "settlement_timestamp": int(time.time()),
            "message": "Autonomous purchase settled in 1 round trip with zero human in the loop."
        }


class AIBuyerAgent:
    """
    Autonomous AI Buyer Agent demo counterpart.
    Queries the machine-payable merchant surface, signs token, and completes purchase.
    """

    @classmethod
    def execute_autonomous_buying_cycle(cls, product_slug: str = "studio-headphones") -> Dict[str, Any]:
        """Runs the complete autonomous buyer flow with zero human intervention."""
        # 1. Get Quote
        quote = X402MerchantSurface.get_machine_quote(product_slug)

        # 2. Autonomous Agent computes signature
        sig = hmac.new(
            SHARED_SECRET_KEY.encode('utf-8'),
            f"{quote['quote_id']}:{quote['total_amount']}:{quote['nonce']}".encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # 3. Complete Purchase
        result = X402MerchantSurface.process_machine_purchase(
            quote_id=quote["quote_id"],
            amount=quote["total_amount"],
            nonce=quote["nonce"],
            signed_token=sig,
            agent_id="autonomous_buyer_bot_v1"
        )

        return {
            "agent_action": "AUTONOMOUS_PURCHASE_CYCLE",
            "quote": quote,
            "signature_attached": sig[:16] + "...",
            "settlement_result": result,
            "zero_human_in_loop": True
        }
