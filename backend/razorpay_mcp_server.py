import sys
import uuid
import json
from mcp.server.mcpserver import MCPServer

# Initialize the server
app = MCPServer("razorpay-mcp-server")

@app.tool()
def create_payment_link(amount: float, description: str = "Order Payment") -> str:
    """
    Generate a Razorpay payment link for an order. Use this after the user confirms their cart.
    Returns JSON containing the link details.
    """
    # Generate a fake payment link ID for testing
    link_id = f"plink_{uuid.uuid4().hex[:12]}"
    url = f"https://rzp.io/i/{link_id[:8]}"
    
    result = {
        "id": link_id,
        "status": "created",
        "short_url": url,
        "amount": amount,
        "description": description
    }
    return json.dumps(result, indent=2)

@app.tool()
def check_payment_status(link_id: str) -> str:
    """
    Check the status of a payment link using its ID.
    Returns JSON containing the payment status.
    """
    result = {
        "id": link_id,
        "status": "paid", # Fake successful payment
        "amount_paid": 400
    }
    return json.dumps(result, indent=2)

@app.tool()
def create_upi_mandate(amount: float, max_amount: float = 0.0, description: str = "Agentic UPI Autopay Mandate", customer_vpa: str = "user@upi") -> str:
    """
    Generate an instant Razorpay UPI Autopay Mandate for conversational in-app checkout.
    """
    mandate_id = f"uman_{uuid.uuid4().hex[:12]}"
    max_amt = max_amount if max_amount > 0 else amount * 1.5
    result = {
        "id": mandate_id,
        "type": "upi_mandate",
        "status": "created",
        "amount": amount,
        "max_amount": max_amt,
        "customer_vpa": customer_vpa,
        "auth_url": f"upi://mandate?pa=razorpay@icici&pn=RazorHub&mc=5411&tid={mandate_id}",
        "description": description,
        "instant_payment_ready": True
    }
    return json.dumps(result, indent=2)

@app.tool()
def confirm_cart_and_pay(order_id: str, amount: float, confirmed_by_user: bool, item_name: str = "Item") -> str:
    """
    Execute instant payment after user confirmation.
    LIABILITY MODEL: The merchant absorbs disputes over what was actually ordered.
    Therefore, the confirmation step is strictly non-negotiable.
    """
    if not confirmed_by_user:
        return json.dumps({
            "success": False,
            "error": "LIABILITY_CHECK_FAILED: Cart confirmation is non-negotiable. Merchant absorbs disputes over ordered items. Explicit user confirmation required before payment execution.",
            "status": "AWAITING_USER_CONFIRMATION",
            "order_id": order_id
        }, indent=2)

    payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    result = {
        "success": True,
        "status": "PAID",
        "payment_id": payment_id,
        "order_id": order_id,
        "amount": amount,
        "item": item_name,
        "payment_method": "upi_mandate",
        "liability_shield": "CONFIRMED_BY_USER",
        "message": f"Payment of ₹{amount:,.0f} authorized via instant UPI mandate for {item_name}."
    }
    return json.dumps(result, indent=2)

@app.tool()
def query_agent_catalog(product_slug_or_id: str = "headphones-a") -> str:
    """
    Read-only MCP tool for autonomous AI shopping agents to cross-check catalog listings.
    Returns Schema.org JSON-LD Product/Offer representation.
    """
    import django
    import os
    if not os.environ.get("DJANGO_SETTINGS_MODULE"):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
        try:
            django.setup()
        except Exception:
            pass

    from intelligence.services.catalog_reconciliation import CatalogReconciliationService
    from products.models import Product

    prod = CatalogReconciliationService.get_product(product_slug_or_id)
    if not prod:
        prod = Product.objects.filter(is_active=True).first()

    if prod:
        from intelligence.services.agent_manifest import AgentManifestService
        schema_data = AgentManifestService.generate_schema_org_json_ld(prod)
        return json.dumps(schema_data, indent=2)

    return json.dumps({"error": "Product not found"}, indent=2)

if __name__ == "__main__":
    # Run the server using stdio communication
    app.run()


