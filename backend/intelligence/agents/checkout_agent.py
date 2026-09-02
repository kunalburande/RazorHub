"""
Checkout Agent — Conversational In-App Checkout for RazorHub Agentic Commerce.

Implements a multi-step, gated checkout flow:
  1. CART_REVIEW  — Confirm items + totals
  2. ADDRESS      — Collect shipping address conversationally
  3. CONFIRM      — Explicit amount confirmation
  4. PAY          — Create Razorpay Order, return payment link
  5. COMPLETE     — Order confirmed, tracking details

Every money action is:
  • Bounded (max amount = confirmed total)
  • Gated (explicit user confirmation required)
  • Audited (logged to AuditEvent with trace_id)

Graceful failure: payment errors explained in plain language with retry options.
"""
import logging
from . import BaseAgent
from intelligence.services.checkout_state import (
    get_session, reset_session, detect_checkout_intent,
    start_cart_review, collect_address, process_address,
    confirm_amount, initiate_payment, handle_payment_failure,
    complete_checkout,
    IDLE, CART_REVIEW, ADDRESS_COLLECTION,
    AMOUNT_CONFIRMATION, PAYMENT_INITIATED, COMPLETED, FAILED,
)

logger = logging.getLogger(__name__)


class CheckoutAgent(BaseAgent):
    name = "checkout"

    def get_system_prompt(self, context: dict) -> str:
        cart_info = context.get("cart", {})
        cart_items = cart_info.get("items", [])
        platform = context.get("platform", "razorhub")
        state = context.get("checkout_state", IDLE)

        if cart_items:
            total = sum(float(i.get('price', 0)) * int(i.get('quantity', 1)) for i in cart_items)
            cart_summary = f"Cart Total: ₹{total:.2f}\nItems:\n" + "\n".join([
                f"- {item.get('name')} × {item.get('quantity', 1)} — ₹{item.get('price', '?')} each"
                for item in cart_items
            ])
        else:
            cart_summary = "User's cart is currently empty."

        return f"""You are the Checkout & Payment Agent for {platform}.
You guide users through a secure, step-by-step checkout flow.

Current checkout state: {state}

Strict Checkout Flow:
1. CART_REVIEW: Show cart summary and ask user to confirm items.
2. ADDRESS: Collect shipping address.
3. AMOUNT_CONFIRMATION: Show final total and ask user to confirm payment.
4. PAYMENT: Create payment link — ONLY after explicit user confirmation.
5. COMPLETE: Confirm order and provide tracking info.

Rules:
- NEVER auto-charge. Every money action needs explicit user "yes"/"confirm".
- If user says "cancel" or "back", stop the flow immediately.
- Be concise (3-5 sentences max per response).
- Use ₹ for currency (INR).

Current Cart:
{cart_summary}"""

    def execute(self, messages: list[dict], context: dict) -> dict:
        """
        Handle the checkout flow using the state machine.
        Each call advances the state based on user input.
        """
        user_id = context.get("user_id", "anonymous")
        session_id = context.get("session_id")
        session = get_session(user_id, session_id)
        cart_items = context.get("cart", {}).get("items", [])
        last_message = messages[-1].get("content", "") if messages else ""
        intent = detect_checkout_intent(last_message)
        state = session["state"]

        # ── State Machine Logic ────────────────────────────────────────────

        # Cancel at any point
        if intent == "cancel":
            reset_session(user_id, session_id)
            return {
                "content": "🚫 Checkout cancelled. Your cart items are still saved — come back whenever you're ready!",
                "checkout_state": IDLE,
            }

        # IDLE: Start checkout
        if state == IDLE:
            if not cart_items:
                return {
                    "content": "Your cart is currently empty! Browse our collection and add some items to get started. 🛍️",
                    "checkout_state": IDLE,
                }
            result = start_cart_review(session, cart_items)
            return self._enrich_response(result, messages, context)

        # CART_REVIEW: User confirms cart → move to address
        if state == CART_REVIEW:
            if intent == "confirm":
                result = collect_address(session)
                return self._enrich_response(result, messages, context)
            elif intent == "modify":
                reset_session(user_id, session_id)
                return {
                    "content": "No problem! Update your cart and come back when you're ready to checkout. 🛒",
                    "checkout_state": IDLE,
                }
            else:
                # Assume address was provided directly
                if len(last_message) > 10:
                    result = collect_address(session, last_message)
                    return self._enrich_response(result, messages, context)
                result = start_cart_review(session, cart_items)
                return self._enrich_response(result, messages, context)

        # ADDRESS_COLLECTION: Process address → confirm amount
        if state == ADDRESS_COLLECTION:
            result = process_address(session, last_message)
            return self._enrich_response(result, messages, context)

        # AMOUNT_CONFIRMATION: User confirms → initiate payment
        if state == AMOUNT_CONFIRMATION:
            if intent in ("confirm", "pay"):
                user = context.get("user")
                result = initiate_payment(session, user)
                return self._enrich_response(result, messages, context)
            else:
                # Re-show confirmation
                result = confirm_amount(session)
                return self._enrich_response(result, messages, context)

        # PAYMENT_INITIATED: Check payment status or handle retry
        if state == PAYMENT_INITIATED:
            if intent == "retry":
                result = initiate_payment(session)
                return self._enrich_response(result, messages, context)
            elif intent == "cod":
                session["payment_method"] = "cod"
                result = complete_checkout(session, payment_id="COD")
                return {
                    "content": result["message"].replace("Payment successful", "Cash on Delivery selected"),
                    "checkout_state": COMPLETED,
                }
            else:
                return {
                    "content": (
                        f"💳 **Payment is pending.**\n\n"
                        f"Order ID: `{session.get('razorpay_order_id', 'N/A')}`\n"
                        f"Amount: **₹{session['final_total']:,.2f}**\n\n"
                        f"Complete your payment using the link above, or reply:\n"
                        f"• **retry** — Generate a new payment link\n"
                        f"• **cod** — Switch to Cash on Delivery\n"
                        f"• **cancel** — Cancel the order"
                    ),
                    "checkout_state": PAYMENT_INITIATED,
                }

        # FAILED: Offer retry or COD
        if state == FAILED:
            if intent == "retry":
                session["state"] = AMOUNT_CONFIRMATION
                result = initiate_payment(session)
                return self._enrich_response(result, messages, context)
            elif intent == "cod":
                session["payment_method"] = "cod"
                result = complete_checkout(session, payment_id="COD")
                return {
                    "content": result["message"],
                    "checkout_state": COMPLETED,
                }
            else:
                return {
                    "content": (
                        "The previous payment didn't go through. You can:\n"
                        "• Reply **retry** to try again\n"
                        "• Reply **cod** for Cash on Delivery\n"
                        "• Reply **cancel** to cancel"
                    ),
                    "checkout_state": FAILED,
                }

        # COMPLETED: Already done
        if state == COMPLETED:
            reset_session(user_id, session_id)
            return {
                "content": "Your order has already been confirmed! 🎉 Need help with anything else?",
                "checkout_state": COMPLETED,
            }

        # Fallback
        return {
            "content": "I can help you checkout! Just add items to your cart and say \"checkout\" when ready.",
            "checkout_state": IDLE,
        }

    def _enrich_response(self, state_result, messages, context):
        """
        Optionally enhance the state machine's response with LLM polish.
        Falls back gracefully to the raw state machine message.
        """
        message = state_result.get("message", "")
        checkout_state = state_result.get("state", IDLE)
        tool_calls = state_result.get("toolCalls")

        # Try to polish with LLM for more natural conversation
        try:
            context_with_state = {**context, "checkout_state": checkout_state}
            polish_messages = messages.copy()
            if polish_messages:
                polish_messages.append({
                    "role": "assistant",
                    "content": f"[CHECKOUT STATE: {checkout_state}]\n{message}"
                })
                polish_messages.append({
                    "role": "user",
                    "content": "Rewrite the above checkout message to be warm, concise, and helpful. Keep all the details (amounts, items, instructions) exactly the same. Do NOT add any new items or change amounts."
                })
                polished = self.call_gemini(polish_messages, context_with_state)
                if polished and len(polished) > 20:
                    message = polished
        except Exception:
            pass  # Fallback to state machine message

        result = {
            "content": message,
            "checkout_state": checkout_state,
        }
        if tool_calls:
            result["toolCalls"] = tool_calls
        return result

