"""
Return / RTO-Risk Agent Service.

Operational Grounding:
Razorpay's operational agents analyze return-to-origin (RTO) patterns by pincode,
product, and customer history to flag preventable returns on Cash-on-Delivery (COD) orders.

Explainability Requirement:
The score is shown openly to merchants and buyers, not hidden, making it
explainable by construction. High-risk orders are automatically switched to prepaid-only
or nudged with mandatory OTP confirmation.
"""
import logging
from decimal import Decimal
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class RtoRiskService:
    """Predicts Return-to-Origin (RTO) risk and enforces COD fraud guardrails."""

    HIGH_RISK_THRESHOLD = 65  # 65% risk score triggers prepaid switch

    PINCODE_RISK_DATABASE = {
        "110001": 15,  # Central Delhi: Low RTO
        "400001": 12,  # Mumbai Fort: Low RTO
        "560001": 14,  # Bangalore MG Road: Low RTO
        "700001": 25,  # Kolkata: Moderate RTO
        "800001": 72,  # Remote East: High RTO
        "842001": 78,  # Muzaffarpur: High RTO
        "282001": 68,  # Agra Rural: High RTO
    }

    CATEGORY_RETURN_RATES = {
        "apparel": 35,
        "clothing": 35,
        "footwear": 30,
        "shoes": 30,
        "electronics": 12,
        "smartphones": 10,
        "laptops": 8,
        "audio": 15,
        "default": 20
    }

    @classmethod
    def evaluate_cod_order(
        cls,
        pincode: str = "800001",
        customer_refusal_history: int = 2,
        order_amount: Decimal = Decimal("3500.00"),
        category: str = "apparel"
    ) -> Dict[str, Any]:
        """
        Calculates RTO Risk Score (0-100%) and determines explainable fulfillment action.
        """
        amt_val = float(order_amount)
        clean_pincode = str(pincode).strip()

        # 1. Pincode risk factor (0 to 40 pts)
        pincode_risk = cls.PINCODE_RISK_DATABASE.get(clean_pincode, 45)
        pincode_pts = min(40, int(pincode_risk * 0.5))

        # 2. Category return tendency factor (0 to 25 pts)
        cat_key = category.lower() if category else "default"
        cat_rate = cls.CATEGORY_RETURN_RATES.get(cat_key, cls.CATEGORY_RETURN_RATES["default"])
        category_pts = min(25, int(cat_rate * 0.6))

        # 3. Customer refusal history (0 to 25 pts)
        refusal_pts = min(25, customer_refusal_history * 10)

        # 4. High COD value penalty (> ₹3,000 increases impulse refusal probability)
        value_pts = 10 if amt_val > 3000.0 else (5 if amt_val > 1500.0 else 0)

        # Composite RTO Score (0-100)
        total_rto_score = min(100, pincode_pts + category_pts + refusal_pts + value_pts)
        is_high_risk = total_rto_score >= cls.HIGH_RISK_THRESHOLD

        if is_high_risk:
            action = "SWITCH_TO_PREPAID_ONLY"
            recommendation = (
                f"High return risk ({total_rto_score}%). Order converted to prepaid-only "
                f"with a ₹100 instant discount incentive to prevent courier return-to-origin."
            )
        else:
            action = "ALLOW_COD"
            recommendation = (
                f"Low/Acceptable return risk ({total_rto_score}%). Standard COD payment approved."
            )

        explanation_factors = [
            f"Pincode ({clean_pincode}) historical RTO weight: +{pincode_pts} pts",
            f"Product category ({category}) return tendency: +{category_pts} pts",
            f"Customer prior refusal history ({customer_refusal_history} rejections): +{refusal_pts} pts",
            f"Order amount threshold (₹{amt_val:,.0f}): +{value_pts} pts"
        ]

        return {
            "pincode": clean_pincode,
            "order_amount": amt_val,
            "category": category,
            "rto_risk_score": total_rto_score,
            "threshold": cls.HIGH_RISK_THRESHOLD,
            "is_high_risk": is_high_risk,
            "action": action,
            "recommendation": recommendation,
            "score_breakdown": {
                "pincode_points": pincode_pts,
                "category_points": category_pts,
                "customer_history_points": refusal_pts,
                "high_order_value_points": value_pts
            },
            "explainability": explanation_factors,
            "explainable_by_construction": True
        }
