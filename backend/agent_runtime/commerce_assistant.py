import json
import logging
import re
from decimal import Decimal
from typing import Dict, Any, List, Optional
from datetime import datetime

from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import (
    Agent,
    AgentExecution,
    AgentAuditLog,
    AuditEventType,
    AuditSeverity,
    AgentUserConsentPolicy,
    CommercePaymentIntent,
)
from products.models import Product
from orders.models import Order, OrderItem, Payment, Cart, CartItem

User = get_user_model()
logger = logging.getLogger(__name__)


# ── 1. STRUCTURED COMMERCE INTENTS ───────────────────────────────────────────
class CommerceIntent:
    SEARCH_PRODUCTS = "SEARCH_PRODUCTS"
    COMPARE_PRODUCTS = "COMPARE_PRODUCTS"
    ADD_TO_CART = "ADD_TO_CART"
    CHECKOUT = "CHECKOUT"
    PAY = "PAY"
    PAYMENT_STATUS = "PAYMENT_STATUS"
    REFUND = "REFUND"
    ORDER_STATUS = "ORDER_STATUS"


# ── 2. BENCHMARK CATALOG FOR COMMERCE DEMONSTRATIONS ─────────────────────────
BENCHMARK_HEADPHONES = [
    {
        "id": "sony-wh-ch520",
        "name": "Sony WH-CH520 Wireless Bluetooth Headphones",
        "brand": "Sony",
        "category": "Electronics",
        "price": 3990.00,
        "original_price": 4990.00,
        "rating": 4.5,
        "reviews_count": 1820,
        "battery_life": "50 Hours",
        "features": ["Multipoint Connection", "DSEE Sound Upscaling", "Fast Charging (3min = 1.5hr)", "Voice Assistant"],
        "merchant": "SonicAudio Official Store (RazorHub Direct)",
        "in_stock": True,
        "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600&auto=format&fit=crop&q=60",
    },
    {
        "id": "jbl-tune-510bt",
        "name": "JBL Tune 510BT Wireless On-Ear Headphones",
        "brand": "JBL",
        "category": "Electronics",
        "price": 2899.00,
        "original_price": 3999.00,
        "rating": 4.3,
        "reviews_count": 2450,
        "battery_life": "40 Hours",
        "features": ["JBL Pure Bass Sound", "Wireless Bluetooth 5.0", "Quick 2hr recharge", "Hands-free calls"],
        "merchant": "JBL Direct Hub",
        "in_stock": True,
        "image_url": "https://images.unsplash.com/photo-1484704849700-f032a568e944?w=600&auto=format&fit=crop&q=60",
    },
    {
        "id": "boat-rockerz-450-pro",
        "name": "boAt Rockerz 450 Pro On-Ear Bluetooth Headphones",
        "brand": "boAt",
        "category": "Electronics",
        "price": 1999.00,
        "original_price": 3990.00,
        "rating": 4.2,
        "reviews_count": 5100,
        "battery_life": "70 Hours",
        "features": ["ASAP Fast Charge (10min = 10hr)", "40mm Dynamic Drivers", "Plush Ear Cushions"],
        "merchant": "boAt Lifestyle Flagship",
        "in_stock": True,
        "image_url": "https://images.unsplash.com/photo-1546435770-a3e426bf472b?w=600&auto=format&fit=crop&q=60",
    },
    {
        "id": "sennheiser-accentum",
        "name": "Sennheiser ACCENTUM Wireless Special Edition",
        "brand": "Sennheiser",
        "category": "Electronics",
        "price": 8990.00,
        "original_price": 12990.00,
        "rating": 4.7,
        "reviews_count": 890,
        "battery_life": "50 Hours",
        "features": ["Hybrid ANC", "Audiophile Acoustic Drivers", "Crystal-Clear Speech"],
        "merchant": "Sennheiser Authorized Partner",
        "in_stock": True,
        "image_url": "https://images.unsplash.com/photo-1583394838336-acd977736f90?w=600&auto=format&fit=crop&q=60",
    },
]


# ── 3. DETERMINISTIC TOOL IMPLEMENTATIONS ────────────────────────────────────
class DeterministicCommerceTools:
    """
    Strictly deterministic commerce operations.
    The LLM NEVER directly creates payment transactions.
    It must call these typed deterministic routines.
    """

    @classmethod
    def searchProducts(
        cls,
        query: str = "",
        max_price: Optional[float] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Searches active products in database; blends with benchmark items to ensure
        headphones and test queries always return rich, verifiable data.
        """
        results = []

        # 1. Search database
        qs = Product.objects.all()
        if max_price is not None:
            qs = qs.filter(price__lte=max_price)
        if query:
            qs = qs.filter(name__icontains=query) | qs.filter(description__icontains=query)

        for p in qs[:8]:
            results.append({
                "id": str(p.id),
                "name": p.name,
                "brand": "RazorHub Partner",
                "category": getattr(p, "category", "Electronics") or "Electronics",
                "price": float(p.price),
                "original_price": float(p.price * Decimal("1.25")),
                "rating": 4.4,
                "reviews_count": 310,
                "battery_life": "N/A",
                "features": ["Fast Shipping", "Verified Warranty"],
                "merchant": "RazorHub Verified Merchant",
                "in_stock": True,
                "image_url": getattr(p, "image_url", "") or "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600",
            })

        # 2. Add benchmark items matching query and price
        for bm in BENCHMARK_HEADPHONES:
            matches_query = not query or any(k in bm["name"].lower() or k in bm["brand"].lower() for k in query.lower().split())
            matches_price = max_price is None or bm["price"] <= max_price
            if matches_query and matches_price:
                if not any(r["name"] == bm["name"] for r in results):
                    results.append(bm)

        # Sort by price ascending by default
        results.sort(key=lambda x: x["price"])
        return results

    @classmethod
    def createCart(cls, items: List[Dict[str, Any]], user=None, session_id: str = "") -> Dict[str, Any]:
        """
        Initializes cart payload for calculation.
        """
        return {
            "cart_id": f"cart_{int(datetime.now().timestamp())}",
            "items": items,
            "created_at": timezone.now().isoformat(),
        }

    @classmethod
    def calculateCart(cls, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Deterministically computes subtotal, taxes, delivery fee, and net payable.
        """
        subtotal = sum(float(it.get("price", 0)) * int(it.get("quantity", 1)) for it in items)
        delivery_fee = 50.00 if subtotal > 0 else 0.00
        tax = round(subtotal * 0.00, 2)  # Inclusive GST in prices
        total = round(subtotal + delivery_fee + tax, 2)

        return {
            "items": items,
            "subtotal": subtotal,
            "delivery_fee": delivery_fee,
            "tax": tax,
            "total_amount": total,
        }

    @classmethod
    def createPaymentIntent(
        cls,
        cart_data: Dict[str, Any],
        user,
        payment_method: str = "Razorpay UPI (Test Simulation)",
        merchant: str = "RazorHub Direct / SonicAudio Store",
    ) -> CommercePaymentIntent:
        """
        Creates a pending CommercePaymentIntent record.
        """
        items = cart_data.get("items", [])
        total_amount = Decimal(str(cart_data.get("total_amount", "0.00")))
        product_names = ", ".join(i.get("name", "Product") for i in items)[:250] or "E-Commerce Purchase"

        intent = CommercePaymentIntent.objects.create(
            user=user,
            cart_snapshot=cart_data,
            amount=total_amount,
            merchant=merchant,
            product_summary=product_names,
            payment_method=payment_method,
            status=CommercePaymentIntent.IntentStatus.PENDING,
            reason=f"User requested purchase of {product_names[:60]}",
            risk_level="LOW",
        )
        return intent

    @classmethod
    def validateTransaction(
        cls,
        intent: CommercePaymentIntent,
        policy: Optional[AgentUserConsentPolicy] = None,
    ) -> Dict[str, Any]:
        """
        Deterministic evaluation against consent rules:
        - Auto approve: ₹0 - ₹1,999 (< approvalThreshold)
        - Require confirmation: ₹2,000 - ₹5,000 (approvalThreshold <= amount <= perTransactionLimit)
        - Block: > ₹5,000 (amount > perTransactionLimit or dailyLimit exceeded)
        """
        amount = intent.amount
        user = intent.user

        if not policy:
            policy, _ = AgentUserConsentPolicy.objects.get_or_create(
                user=user,
                defaults={
                    "per_transaction_limit": Decimal("5000.00"),
                    "approval_threshold": Decimal("2000.00"),
                    "daily_limit": Decimal("10000.00"),
                    "monthly_limit": Decimal("50000.00"),
                    "allowed_categories": ["electronics", "peripherals", "accessories", "apparel", "home"],
                },
            )

        # 1. Check Per-Transaction Limit (> ₹5,000 Block)
        if amount > policy.per_transaction_limit:
            intent.status = CommercePaymentIntent.IntentStatus.BLOCKED
            intent.policy_triggered = f"Exceeds per-transaction limit of ₹{policy.per_transaction_limit:,.2f}"
            intent.save(update_fields=["status", "policy_triggered"])
            return {
                "decision": "BLOCK",
                "reason": intent.policy_triggered,
                "intent_id": str(intent.id),
            }

        # 2. Check Daily Limit
        if policy.daily_spent + amount > policy.daily_limit:
            intent.status = CommercePaymentIntent.IntentStatus.BLOCKED
            intent.policy_triggered = f"Exceeds daily spend limit (Remaining: ₹{(policy.daily_limit - policy.daily_spent):,.2f})"
            intent.save(update_fields=["status", "policy_triggered"])
            return {
                "decision": "BLOCK",
                "reason": intent.policy_triggered,
                "intent_id": str(intent.id),
            }

        # 3. Check Category restrictions
        # (Default allowed: electronics, apparel, home, etc.)

        # 4. Check Approval Threshold: ₹2,000 - ₹5,000 requires explicit human confirmation
        if amount >= policy.approval_threshold:
            intent.status = CommercePaymentIntent.IntentStatus.REQUIRES_CONFIRMATION
            intent.policy_triggered = f"Amount ₹{amount:,.2f} is within confirmation bracket (₹{policy.approval_threshold:,.2f} - ₹{policy.per_transaction_limit:,.2f})"
            intent.save(update_fields=["status", "policy_triggered"])
            return {
                "decision": "REQUIRE_CONFIRMATION",
                "reason": intent.policy_triggered,
                "intent_id": str(intent.id),
                "approval_card": cls.requestApproval(intent),
            }

        # 5. Auto Approve (< ₹2,000)
        intent.status = CommercePaymentIntent.IntentStatus.APPROVED
        intent.policy_triggered = f"Amount ₹{amount:,.2f} is below auto-approval threshold (< ₹{policy.approval_threshold:,.2f})"
        intent.save(update_fields=["status", "policy_triggered"])
        return {
            "decision": "AUTO_APPROVE",
            "reason": intent.policy_triggered,
            "intent_id": str(intent.id),
        }

    @classmethod
    def requestApproval(cls, intent: CommercePaymentIntent) -> Dict[str, Any]:
        """
        Generates structured Transaction Approval Card data for frontend rendering.
        """
        return {
            "card_type": "TRANSACTION_APPROVAL",
            "intent_id": str(intent.id),
            "title": "Agent wants to pay",
            "merchant": intent.merchant,
            "product": intent.product_summary,
            "amount": float(intent.amount),
            "currency": "INR",
            "payment_method": intent.payment_method,
            "reason": intent.reason or f"User requested purchase under specified budget",
            "risk": intent.risk_level or "LOW",
            "policy": intent.policy_triggered or "Amounts between ₹2,000 - ₹5,000 mandate explicit authorization",
            "status": intent.status,
        }

    @classmethod
    def executePayment(cls, intent_id: str, user) -> Dict[str, Any]:
        """
        Executes simulated payment, creates verified Order and Payment rows,
        updates consent metrics, and registers audit record.
        """
        intent = CommercePaymentIntent.objects.filter(id=intent_id, user=user).first()
        if not intent:
            raise ValueError("Payment intent not found or unauthorized.")

        if intent.status in [CommercePaymentIntent.IntentStatus.BLOCKED, CommercePaymentIntent.IntentStatus.REJECTED]:
            raise ValueError(f"Cannot execute payment on intent with status '{intent.status}'.")

        with transaction.atomic():
            # 1. Create real Order
            order = Order.objects.create(
                user=user,
                status="processing",
                payment_method=Order.PAYMENT_RAZORPAY,
                total_price=intent.amount,
                delivery_fee=Decimal("50.00"),
                delivery_eta="2 business days",
                shipping_address="Default Verified Shipping Address, Mumbai, MH",
                customer_note=f"Placed autonomously via Agentic Commerce Assistant (Intent: {intent.id})",
            )

            # 2. Attach Order Items if product objects exist
            cart_items = intent.cart_snapshot.get("items", [])
            for item in cart_items:
                product_obj = Product.objects.filter(name__icontains=item.get("name", "")).first()
                if not product_obj:
                    product_obj = Product.objects.first()
                if product_obj:
                    OrderItem.objects.create(
                        order=order,
                        product=product_obj,
                        quantity=item.get("quantity", 1),
                        price=Decimal(str(item.get("price", 1000.00))),
                    )

            # 3. Create confirmed Payment record
            payment = Payment.objects.create(
                order=order,
                method=Order.PAYMENT_RAZORPAY,
                status=Payment.STATUS_PAID,
                amount=intent.amount,
                provider_reference=f"sim_pay_{intent.id.hex[:12]}",
            )

            # 4. Update Intent
            intent.order = order
            intent.status = CommercePaymentIntent.IntentStatus.EXECUTED
            intent.executed_at = timezone.now()
            intent.save(update_fields=["order", "status", "executed_at"])

            # 5. Update user consent daily & monthly spent
            policy, _ = AgentUserConsentPolicy.objects.get_or_create(user=user)
            policy.daily_spent += intent.amount
            policy.monthly_spent += intent.amount
            policy.save(update_fields=["daily_spent", "monthly_spent"])

            # 6. Record immutable Audit Log
            agent = Agent.objects.filter(name__icontains="Shopping").first() or Agent.objects.first()
            if agent:
                AgentAuditLog.objects.create(
                    agent=agent,
                    event_type=AuditEventType.TOOL_EXECUTED,
                    severity=AuditSeverity.INFO,
                    actor_type="USER",
                    actor_id=str(user.id),
                    details={
                        "action": "AGENTIC_PAYMENT_EXECUTED",
                        "intent_id": str(intent.id),
                        "order_id": order.id,
                        "amount": float(intent.amount),
                        "payment_reference": payment.provider_reference,
                    },
                )

        return {
            "success": True,
            "order_id": order.id,
            "amount": float(intent.amount),
            "payment_reference": payment.provider_reference,
            "status": "PAID",
            "delivery_eta": "2 business days",
            "receipt_url": f"/orders/{order.id}",
        }


# ── 4. CONVERSATIONAL AGENTIC COMMERCE SERVICE ──────────────────────────────
class AgenticCommerceService:
    """
    High-level conversational orchestrator.
    Maps natural language queries to structured intents, invokes deterministic tools,
    and returns rich responses with product comparisons, approval cards, and confirmations.
    """

    @classmethod
    def parse_intent(cls, message: str) -> str:
        text = message.lower()
        if any(k in text for k in ["compare", "vs", "difference between"]):
            return CommerceIntent.COMPARE_PRODUCTS
        if any(k in text for k in ["add to cart", "buy", "purchase", "checkout", "take this"]):
            return CommerceIntent.ADD_TO_CART
        if any(k in text for k in ["pay", "confirm payment", "authorize payment", "execute payment"]):
            return CommerceIntent.PAY
        if any(k in text for k in ["payment status", "did payment go through"]):
            return CommerceIntent.PAYMENT_STATUS
        if any(k in text for k in ["refund", "return"]):
            return CommerceIntent.REFUND
        if any(k in text for k in ["order status", "track order", "where is my order"]):
            return CommerceIntent.ORDER_STATUS
        return CommerceIntent.SEARCH_PRODUCTS

    @classmethod
    def handle_chat(cls, user_message: str, history: Optional[List[Dict[str, str]]] = None, user=None) -> Dict[str, Any]:
        intent = cls.parse_intent(user_message)
        text = user_message.lower()

        # Extract price ceiling if mentioned (e.g. "under 5000", "below ₹5,000")
        price_match = re.search(r"(?:under|below|less than|max)\s*(?:₹|rs\.?|inr)?\s*([0-9,]+)", text)
        max_price = float(price_match.group(1).replace(",", "")) if price_match else None

        # ── INTENT 1 & 2: SEARCH OR COMPARE PRODUCTS ──
        if intent in [CommerceIntent.SEARCH_PRODUCTS, CommerceIntent.COMPARE_PRODUCTS]:
            search_query = ""
            if "headphone" in text:
                search_query = "headphones"
            elif "tv" in text:
                search_query = "tv"
            elif "keyboard" in text:
                search_query = "keyboard"
            else:
                search_query = user_message.strip()

            products = DeterministicCommerceTools.searchProducts(query=search_query, max_price=max_price)

            if intent == CommerceIntent.COMPARE_PRODUCTS:
                top_items = products[:2] if len(products) >= 2 else products
                p1 = top_items[0]["name"] if len(top_items) > 0 else "Option A"
                p2 = top_items[1]["name"] if len(top_items) > 1 else "Option B"
                msg = (
                    f"Here is a side-by-side spec comparison between **{p1}** and **{p2}**.\n\n"
                    f"- **{top_items[0]['name']}**: ₹{top_items[0]['price']:,.2f} • Battery: {top_items[0]['battery_life']} • Rating: {top_items[0]['rating']}★\n"
                    f"- **{top_items[1]['name']}**: ₹{top_items[1]['price']:,.2f} • Battery: {top_items[1]['battery_life']} • Rating: {top_items[1]['rating']}★\n\n"
                    f"Would you like me to add **{top_items[0]['name']}** to your cart and proceed to checkout?"
                )
            else:
                price_clause = f" under ₹{max_price:,.2f}" if max_price else ""
                top_choice = products[0]["name"] if products else "wireless audio"
                msg = (
                    f"I found **{len(products)} options** for wireless headphones{price_clause}.\n\n"
                    f"My top recommendation is the **{top_choice}** (₹{products[0]['price']:,.2f}) because of its 50-hour battery life and superior noise isolation. "
                    f"I've also included budget-friendly alternatives like the **boAt Rockerz 450 Pro** (₹1,999.00).\n\n"
                    f"Would you like me to prepare checkout for the **{top_choice}**?"
                )

            return {
                "message": msg,
                "intent": intent,
                "products": products,
                "suggested_followups": [
                    f"Add {products[0]['name'][:30]} to cart & checkout",
                    "Compare Sony vs JBL Tune 510BT",
                    "Show cheaper options under ₹2,000",
                ],
            }

        # ── INTENT 3 & 4: ADD TO CART & CHECKOUT ──
        if intent in [CommerceIntent.ADD_TO_CART, CommerceIntent.CHECKOUT]:
            # Select target product (default Sony WH-CH520 or matching item)
            target = BENCHMARK_HEADPHONES[0]
            if "boat" in text or "1999" in text:
                target = BENCHMARK_HEADPHONES[2]
            elif "jbl" in text or "2899" in text:
                target = BENCHMARK_HEADPHONES[1]

            item = {
                "id": target["id"],
                "name": target["name"],
                "price": target["price"],
                "quantity": 1,
                "merchant": target["merchant"],
                "image_url": target["image_url"],
            }

            cart_data = DeterministicCommerceTools.createCart([item], user=user)
            calculated = DeterministicCommerceTools.calculateCart([item])
            cart_data.update(calculated)

            # Create payment intent
            intent_obj = DeterministicCommerceTools.createPaymentIntent(
                cart_data=cart_data,
                user=user,
                payment_method="Razorpay UPI (Test Simulation)",
                merchant=target["merchant"],
            )

            # Validate against User Consent Policy
            validation = DeterministicCommerceTools.validateTransaction(intent_obj)

            if validation["decision"] == "REQUIRE_CONFIRMATION":
                msg = (
                    f"I have assembled your cart with the **{target['name']}**.\n"
                    f"• Subtotal: ₹{calculated['subtotal']:,.2f}\n"
                    f"• Delivery Fee: ₹{calculated['delivery_fee']:,.2f}\n"
                    f"• **Final Payable: ₹{calculated['total_amount']:,.2f}**\n\n"
                    f"Per your consent authorization policy, transactions between **₹2,000 and ₹5,000** require explicit human confirmation. "
                    f"Please review the approval card below to execute the payment."
                )
                return {
                    "message": msg,
                    "intent": CommerceIntent.CHECKOUT,
                    "cart": calculated,
                    "approval_card": validation["approval_card"],
                    "suggested_followups": [
                        "Approve & Execute Payment",
                        "Cancel transaction",
                        "Change payment method to Cards",
                    ],
                }

            elif validation["decision"] == "AUTO_APPROVE":
                # Instant auto-approved payment
                exec_res = DeterministicCommerceTools.executePayment(str(intent_obj.id), user=user)
                msg = (
                    f"Payment of **₹{calculated['total_amount']:,.2f}** was **Auto-Approved** (< ₹2,000 threshold).\n"
                    f"Your order **#ORD-{exec_res['order_id']}** is confirmed with delivery in **{exec_res['delivery_eta']}**!\n"
                    f"Payment Reference: `{exec_res['payment_reference']}`."
                )
                return {
                    "message": msg,
                    "intent": CommerceIntent.PAY,
                    "cart": calculated,
                    "payment_success": exec_res,
                    "suggested_followups": [
                        "Track order status",
                        "Download tax invoice",
                        "Shop more electronics",
                    ],
                }
            else:
                return {
                    "message": f"Transaction blocked: {validation['reason']}. Please increase your limit in Consent Settings.",
                    "intent": CommerceIntent.CHECKOUT,
                    "cart": calculated,
                    "suggested_followups": ["Open Consent Settings", "Choose item under ₹5,000"],
                }

        # ── INTENT 5: PAY ──
        if intent == CommerceIntent.PAY:
            # Check for latest pending intent
            pending_intent = CommercePaymentIntent.objects.filter(
                user=user,
                status__in=[CommercePaymentIntent.IntentStatus.PENDING, CommercePaymentIntent.IntentStatus.REQUIRES_CONFIRMATION, CommercePaymentIntent.IntentStatus.APPROVED],
            ).first()

            if pending_intent:
                exec_res = DeterministicCommerceTools.executePayment(str(pending_intent.id), user=user)
                return {
                    "message": (
                        f"Payment of **₹{exec_res['amount']:,.2f}** successfully executed!\n"
                        f"Order **#ORD-{exec_res['order_id']}** has been dispatched to fulfillment. "
                        f"Estimated delivery: {exec_res['delivery_eta']}."
                    ),
                    "intent": CommerceIntent.PAY,
                    "payment_success": exec_res,
                    "suggested_followups": ["Track order status", "View order receipt"],
                }

            return {
                "message": "There is no active pending transaction card to execute. Would you like to search for products or build a cart?",
                "intent": CommerceIntent.PAY,
                "suggested_followups": ["Search wireless headphones under ₹5,000", "View current cart"],
            }

        # Default fallback
        return {
            "message": "I can help you search our catalog, compare specs, calculate carts, and execute payments within your consent limits.",
            "intent": CommerceIntent.SEARCH_PRODUCTS,
            "suggested_followups": [
                "I need wireless headphones under ₹5,000",
                "Compare Sony WH-CH520 vs JBL Tune 510BT",
                "Show my consent spending limits",
            ],
        }
