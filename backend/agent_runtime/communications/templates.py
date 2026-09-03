from typing import Dict, Any, Tuple


class GovernedCommunicationTemplates:
    """
    Registry of communication templates with immutable financial, legal, and compliance anchors.
    LLM/agent personalization may adjust greeting or tone, but cannot modify the immutable data.
    """

    TEMPLATES = {
        "payment_recovery": {
            "purpose": "TRANSACTIONAL",
            "required_anchors": ["order_id", "amount", "payment_link", "discount_limit"],
            "compliance_text": "Secure checkout session powered by RazorHub PCI-DSS compliant checkout.",
            "render": lambda data, greeting: (
                f"{greeting or 'Hello'}, we noticed your recent checkout for order {data['order_id']} was incomplete. "
                f"You can safely complete your payment of ₹{data['amount']:,.2f} using the link below (Max available discount: {data['discount_limit']}%):\n"
                f"{data['payment_link']}\n\n"
                f"[Compliance Notice: Secure checkout session powered by RazorHub PCI-DSS compliant checkout.]"
            ),
        },
        "invoice_reminder": {
            "purpose": "COLLECTIONS",
            "required_anchors": ["invoice_number", "amount_due", "due_date", "bank_details"],
            "compliance_text": "Please reference invoice number in payment remarks. TDS deduction applicable as per statutory regulations.",
            "render": lambda data, greeting: (
                f"{greeting or 'Dear Partner'}, this is a friendly reminder regarding invoice {data['invoice_number']} "
                f"for the amount of ₹{data['amount_due']:,.2f}, due on {data['due_date']}.\n"
                f"Bank details: {data['bank_details']}\n\n"
                f"[Statutory Notice: Please reference invoice number in payment remarks. TDS deduction applicable as per statutory regulations.]"
            ),
        },
        "payment_confirmation": {
            "purpose": "TRANSACTIONAL",
            "required_anchors": ["transaction_id", "amount_paid", "tax_invoice_id"],
            "compliance_text": "Payment processed via RazorHub Gateway. Official GST tax invoice receipt generated.",
            "render": lambda data, greeting: (
                f"{greeting or 'Thank you'}, your payment of ₹{data['amount_paid']:,.2f} has been confirmed. "
                f"Transaction Reference: {data['transaction_id']} (Tax Invoice: {data['tax_invoice_id']}).\n\n"
                f"[Official Receipt: Payment processed via RazorHub Gateway. Official GST tax invoice receipt generated.]"
            ),
        },
        "payout_approval": {
            "purpose": "ACCOUNT_UPDATES",
            "required_anchors": ["payout_id", "beneficiary_name", "amount", "utr_reference"],
            "compliance_text": "Disbursement authorized under corporate treasury governance limits.",
            "render": lambda data, greeting: (
                f"{greeting or 'Treasury Notification'}: Payout {data['payout_id']} to {data['beneficiary_name']} "
                f"for ₹{data['amount']:,.2f} has been approved. Bank UTR: {data['utr_reference']}.\n\n"
                f"[Governance Notice: Disbursement authorized under corporate treasury governance limits.]"
            ),
        },
        "risk_alert": {
            "purpose": "SECURITY_ALERTS",
            "required_anchors": ["alert_code", "incident_timestamp", "security_escalation_link"],
            "compliance_text": "Automated security sentinel alert. If unauthorized, lock account credentials immediately.",
            "render": lambda data, greeting: (
                f"{greeting or 'URGENT SECURITY ALERT'}: Anomaly detected [{data['alert_code']}] at {data['incident_timestamp']}. "
                f"Review activity immediately: {data['security_escalation_link']}\n\n"
                f"[Security Policy: Automated security sentinel alert. If unauthorized, lock account credentials immediately.]"
            ),
        },
        "cashflow_alert": {
            "purpose": "ACCOUNT_UPDATES",
            "required_anchors": ["current_balance", "burn_rate", "runway_months", "forecasted_inflow"],
            "compliance_text": "RazorHub Corporate Treasury automated diagnostic.",
            "render": lambda data, greeting: (
                f"{greeting or 'Treasury Advisory'}: Current cash balance is ₹{data['current_balance']:,.2f} with monthly burn ₹{data['burn_rate']:,.2f}. "
                f"Runway is projected at {data['runway_months']} months with forecasted inflow of ₹{data['forecasted_inflow']:,.2f}.\n\n"
                f"[Advisory: RazorHub Corporate Treasury automated diagnostic.]"
            ),
        },
    }

    @classmethod
    def render_content(
        cls, template_name: str, immutable_data: Dict[str, Any], personal_greeting: str = ""
    ) -> Tuple[str, str]:
        """
        Renders governed content ensuring immutable anchors cannot be modified.
        Returns (rendered_content, purpose).
        """
        tmpl = cls.TEMPLATES.get(template_name)
        if not tmpl:
            raise ValueError(f"Unknown communication template: '{template_name}'")

        # Validate that all required immutable financial/legal anchors are supplied
        missing = [a for a in tmpl["required_anchors"] if a not in immutable_data]
        if missing:
            raise ValueError(f"Template '{template_name}' missing required immutable anchors: {missing}")

        rendered = tmpl["render"](immutable_data, personal_greeting)
        return rendered, tmpl["purpose"]
