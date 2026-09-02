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

if __name__ == "__main__":
    # Run the server using stdio communication
    app.run()
