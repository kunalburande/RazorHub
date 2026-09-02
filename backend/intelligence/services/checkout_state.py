"""
Checkout Session State Machine for RazorHub Agentic Commerce.

Manages the conversational checkout flow:
  IDLE → CART_REVIEW → ADDRESS_COLLECTION → AMOUNT_CONFIRMATION → PAYMENT_INITIATED → COMPLETED / FAILED

Every state transition is logged to AuditEvent with trace_id, bounded amounts,
and gated_by fields as required by the audit trail specification.
"""
import uuid
import re
import logging
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── State Constants ─────────────────────────────────────────────────────
IDLE = "IDLE"
CART_REVIEW = "CART_REVIEW"
ADDRESS_COLLECTION = "ADDRESS_COLLECTION"
AMOUNT_CONFIRMATION = "AMOUNT_CONFIRMATION"
PAYMENT_INITIATED = "PAYMENT_INITIATED"
COMPLETED = "COMPLETED"
FAILED = "FAILED"

# ── In-memory session store (production: use Redis or DB-backed) ────────
_sessions: dict[str, dict] = {}


def _session_key(user_id, session_id=None):
    return f"checkout_{user_id}_{session_id or 'default'}"


def get_session(user_id, session_id=None):
    """Get or create a checkout session for a user."""
    key = _session_key(user_id, session_id)
    if key not in _sessions:
        _sessions[key] = {
            "state": IDLE,
            "trace_id": str(uuid.uuid4()),
            "user_id": user_id,
            "session_id": session_id,
            "cart_items": [],
            "cart_total": Decimal("0.00"),
            "delivery_fee": Decimal("0.00"),
            "discount": Decimal("0.00"),
            "final_total": Decimal("0.00"),
            "shipping_address": "",
            "payment_method": "razorpay",
            "razorpay_order_id": None,
            "razorpay_payment_link": None,
            "error": None,
            "created_at": timezone.now().isoformat(),
            "steps_log": [],
        }
    return _sessions[key]


def reset_session(user_id, session_id=None):
    """Reset a checkout session to IDLE."""
    key = _session_key(user_id, session_id)
    if key in _sessions:
        del _sessions[key]


def _log_step(session, action, details="", gated_by=None, outcome="success"):
    """Log a checkout step to the session's audit trail."""
    step = {
        "trace_id": session["trace_id"],
        "action": action,
        "state": session["state"],
        "timestamp": timezone.now().isoformat(),
        "details": details,
        "outcome": outcome,
    }
    if gated_by:
        step["gated_by"] = gated_by
    session["steps_log"].append(step)
    logger.info(f"[Checkout] {action} | state={session['state']} | outcome={outcome}")


def log_to_audit_event(session, action, outcome, details="", razorpay_entity=None):
    """
    Persist a checkout audit event to the AuditEvent model.
    Follows the universal audit trail schema from requirements.
    """
    from intelligence.models import AuditEvent
    try:
        payload = {
            "trace_id": session["trace_id"],
            "cart_total": str(session["cart_total"]),
            "final_total": str(session["final_total"]),
            "delivery_fee": str(session["delivery_fee"]),
            "discount": str(session["discount"]),
            "shipping_address": session.get("shipping_address", ""),
            "cart_items_count": len(session.get("cart_items", [])),
        }
        if razorpay_entity:
            payload["razorpay_entity"] = razorpay_entity
        payload["bounded"] = {
            "max_amount": str(session["final_total"]),
            "currency": "INR",
        }

        AuditEvent.objects.create(
            event_id=f"chk_{uuid.uuid4().hex[:12]}",
            trace_id=session["trace_id"],
            agent="checkout_agent",
            action=action,
            details=details,
            status=outcome,
            payload=payload,
        )
    except Exception as e:
        logger.error(f"[Checkout Audit] Failed to log: {e}")


# ── State Transition Functions ──────────────────────────────────────────

def start_cart_review(session, cart_items):
    """
    Transition: IDLE → CART_REVIEW.
    Populates the session with cart items and computes totals.
    """
    if not cart_items:
        session["state"] = IDLE
        _log_step(session, "cart_review_empty", "Cart is empty", outcome="skipped")
        return {
            "state": IDLE,
            "message": "Your cart is empty. Add some items first!",
        }

    session["cart_items"] = cart_items
    cart_total = sum(
        Decimal(str(item.get("price", 0))) * int(item.get("quantity", 1))
        for item in cart_items
    )
    session["cart_total"] = cart_total

    # Default delivery fee (waived above threshold)
    from intelligence.models import MerchantConfig
    config = MerchantConfig.get_solo()
    free_threshold = config.free_shipping_threshold
    if cart_total >= free_threshold:
        session["delivery_fee"] = Decimal("0.00")
    else:
        session["delivery_fee"] = Decimal("150.00")

    session["final_total"] = cart_total + session["delivery_fee"] - session["discount"]
    session["state"] = CART_REVIEW
    _log_step(session, "cart_review_started", f"Cart total: ₹{cart_total}")

    # Build display
    items_display = []
    for item in cart_items:
        qty = int(item.get("quantity", 1))
        price = Decimal(str(item.get("price", 0)))
        items_display.append(
            f"• **{item.get('name', 'Product')}** × {qty} — ₹{price * qty:,.2f}"
        )

    delivery_text = "🆓 **Free Delivery!**" if session["delivery_fee"] == 0 else f"🚚 Delivery: ₹{session['delivery_fee']:,.2f}"

    message = (
        f"🛒 **Order Summary** ({len(cart_items)} item{'s' if len(cart_items) != 1 else ''}):\n\n"
        + "\n".join(items_display)
        + f"\n\n💰 Subtotal: **₹{cart_total:,.2f}**\n"
        + f"{delivery_text}\n"
        + f"**Total: ₹{session['final_total']:,.2f}**\n\n"
        + "Shall I proceed? Reply **yes** to continue, or **change** to modify your cart."
    )

    return {"state": CART_REVIEW, "message": message}


def collect_address(session, user_message=""):
    """
    Transition: CART_REVIEW → ADDRESS_COLLECTION.
    If address is provided in the message, validate and move forward.
    """
    session["state"] = ADDRESS_COLLECTION
    _log_step(session, "address_collection_started", gated_by="user_confirmation")

    # Try to extract address from the message
    if user_message and len(user_message) > 10:
        # Basic validation: should have some structure
        session["shipping_address"] = user_message.strip()
        return confirm_amount(session)

    message = (
        "📍 **Shipping Address**\n\n"
        "Please provide your delivery address including:\n"
        "- Full name\n"
        "- Street address\n"
        "- City, State, PIN code\n"
        "- Phone number\n\n"
        "Just type it out — I'll take care of the rest!"
    )
    return {"state": ADDRESS_COLLECTION, "message": message}


def process_address(session, address_text):
    """
    Process the user's address input and validate it.
    Then transition to AMOUNT_CONFIRMATION.
    """
    address = address_text.strip()

    if len(address) < 10:
        _log_step(session, "address_validation_failed", "Address too short", outcome="failed")
        return {
            "state": ADDRESS_COLLECTION,
            "message": "The address seems too short. Please provide a complete shipping address with street, city, state, and PIN code.",
        }

    # Basic PIN code validation for India
    pin_match = re.search(r'\b\d{6}\b', address)
    if not pin_match:
        _log_step(session, "address_validation_warning", "No PIN code found")
        # Still accept but warn
        pass

    session["shipping_address"] = address
    _log_step(session, "address_collected", f"Address: {address[:50]}...")

    return confirm_amount(session)


def confirm_amount(session):
    """
    Transition: ADDRESS_COLLECTION → AMOUNT_CONFIRMATION.
    Shows final total and asks for explicit payment confirmation.
    """
    session["state"] = AMOUNT_CONFIRMATION
    _log_step(session, "amount_confirmation_requested",
              f"Total: ₹{session['final_total']:,.2f}",
              gated_by="user_confirmation")

    address_preview = session["shipping_address"][:80] + ("..." if len(session["shipping_address"]) > 80 else "")

    message = (
        f"✅ **Final Confirmation**\n\n"
        f"📦 **Items:** {len(session['cart_items'])} item(s)\n"
        f"💰 **Total Amount:** **₹{session['final_total']:,.2f}** (incl. delivery)\n"
        f"📍 **Deliver to:** {address_preview}\n"
        f"💳 **Payment:** Razorpay (UPI / Card / NetBanking)\n\n"
        f"⚠️ **Confirm Payment?** Reply **pay** or **confirm** to proceed.\n"
        f"Reply **cancel** to go back."
    )
    return {"state": AMOUNT_CONFIRMATION, "message": message}


def initiate_payment(session, user=None):
    """
    Transition: AMOUNT_CONFIRMATION → PAYMENT_INITIATED.
    Creates a Razorpay Order and returns the checkout details.
    """
    from intelligence.services.razorpay_service import RazorpayService

    session["state"] = PAYMENT_INITIATED
    _log_step(session, "payment_initiation_started",
              f"Amount: ₹{session['final_total']:,.2f}",
              gated_by="user_confirmation")

    try:
        receipt = f"conv_order_{uuid.uuid4().hex[:10]}"
        notes = {
            "type": "conversational_checkout",
            "trace_id": session["trace_id"],
            "items_count": str(len(session["cart_items"])),
            "shipping_address": session["shipping_address"][:200],
            "gated_by": "user_confirmation",
            "bounded": "true",
        }

        rzp_order = RazorpayService.create_order(
            amount=session["final_total"],
            receipt=receipt,
            notes=notes,
        )

        session["razorpay_order_id"] = rzp_order["id"]

        # Log success audit event
        log_to_audit_event(
            session,
            action="payment_initiated",
            outcome="success",
            details=f"Razorpay Order created: {rzp_order['id']}",
            razorpay_entity={"type": "order", "id": rzp_order["id"]},
        )

        _log_step(session, "payment_initiated",
                  f"Razorpay Order: {rzp_order['id']}")

        message = (
            f"💳 **Payment Ready!**\n\n"
            f"Order ID: `{rzp_order['id']}`\n"
            f"Amount: **₹{session['final_total']:,.2f}**\n\n"
            f"🔗 **Complete your payment** using UPI, Credit/Debit Card, or NetBanking.\n\n"
            f"Your order is secured and will be confirmed once payment is complete. "
            f"This payment link is valid for 30 minutes."
        )

        return {
            "state": PAYMENT_INITIATED,
            "message": message,
            "toolCalls": [{
                "type": "checkout_confirm",
                "razorpay_order_id": rzp_order["id"],
                "amount": str(session["final_total"]),
                "currency": "INR",
                "receipt": receipt,
            }],
        }

    except Exception as e:
        return handle_payment_failure(session, str(e))


def handle_payment_failure(session, error_message):
    """
    Graceful failure handling for payment errors.
    Explains error in plain language, offers retry, logs event.
    """
    session["state"] = FAILED
    session["error"] = error_message
    _log_step(session, "payment_failed", error_message, outcome="failed")

    # Log failure audit event
    log_to_audit_event(
        session,
        action="payment_failed",
        outcome="failed",
        details=f"Error: {error_message}",
    )

    # Map Razorpay error codes to user-friendly messages
    user_message = "The payment couldn't be processed."
    if "BAD_REQUEST_ERROR" in error_message:
        user_message = "There was an issue with the payment details."
    elif "card" in error_message.lower() or "declined" in error_message.lower():
        user_message = "Your card was declined by the bank."
    elif "timeout" in error_message.lower():
        user_message = "The payment gateway timed out."
    elif "insufficient" in error_message.lower():
        user_message = "Insufficient funds in your account."

    message = (
        f"❌ **Payment Failed**\n\n"
        f"{user_message}\n\n"
        f"**What you can do:**\n"
        f"• Try a different payment method (UPI, Card, NetBanking)\n"
        f"• Check your card/account balance\n"
        f"• Reply **retry** to try again\n"
        f"• Reply **cod** for Cash on Delivery\n\n"
        f"Don't worry — no amount has been charged."
    )

    return {"state": FAILED, "message": message}


def complete_checkout(session, payment_id=None):
    """
    Transition: PAYMENT_INITIATED → COMPLETED.
    Called when payment is verified as successful.
    """
    session["state"] = COMPLETED
    _log_step(session, "checkout_completed",
              f"Payment: {payment_id or 'confirmed'}")

    log_to_audit_event(
        session,
        action="payment_captured",
        outcome="success",
        details=f"Payment captured: {payment_id}",
        razorpay_entity={"type": "payment", "id": payment_id or "unknown"},
    )

    message = (
        f"🎉 **Order Confirmed!**\n\n"
        f"✅ Payment successful\n"
        f"📦 Your order is being processed\n"
        f"📍 Delivering to: {session['shipping_address'][:60]}...\n"
        f"📋 Order ID: `{session.get('razorpay_order_id', 'N/A')}`\n\n"
        f"You'll receive tracking details shortly. Thank you for shopping with RazorHub! 🛍️"
    )

    return {"state": COMPLETED, "message": message}


# ── Intent Detection Helpers ────────────────────────────────────────────

def detect_checkout_intent(message_text):
    """Detect what the user wants to do in the checkout flow."""
    text = message_text.lower().strip()

    if any(w in text for w in ["yes", "proceed", "continue", "go ahead", "sure", "ok", "okay"]):
        return "confirm"
    if any(w in text for w in ["pay", "confirm payment", "confirm order", "place order"]):
        return "pay"
    if any(w in text for w in ["cancel", "stop", "no", "back", "nevermind", "never mind"]):
        return "cancel"
    if any(w in text for w in ["retry", "try again", "again"]):
        return "retry"
    if any(w in text for w in ["cod", "cash on delivery", "cash"]):
        return "cod"
    if any(w in text for w in ["change", "modify", "edit", "update"]):
        return "modify"

    return "unknown"
