import logging
from typing import Dict, Any, List, Optional
from .rules import (
    BaseRiskRule,
    RuleEvaluationResult,
    AmountAnomalyRule,
    FailedAttemptsRule,
    DeviceAnomalyRule,
    MerchantTrustRule,
    CategoryRiskRule,
    LocationAnomalyRule,
    ChargebackHistoryRule,
    RefundHistoryRule,
    VelocityRule,
    CustomerAgeRule,
    PaymentHistoryRule,
)

logger = logging.getLogger(__name__)


class FinancialRiskEngine:
    """
    Explainable Financial Risk Engine.
    Evaluates 11 core financial, behavioral, and context dimensions deterministically.
    """

    RULES: List[BaseRiskRule] = [
        AmountAnomalyRule(),
        FailedAttemptsRule(),
        DeviceAnomalyRule(),
        MerchantTrustRule(),
        CategoryRiskRule(),
        LocationAnomalyRule(),
        ChargebackHistoryRule(),
        RefundHistoryRule(),
        VelocityRule(),
        CustomerAgeRule(),
        PaymentHistoryRule(),
    ]

    @classmethod
    def evaluate(
        cls,
        inputs: Dict[str, Any],
        include_llm_explanation: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes deterministic rules-first evaluation.

        Inputs:
        - transaction amount
        - customer age
        - merchant history
        - payment history
        - refund history
        - chargeback history
        - velocity
        - category
        - device
        - location
        - failed attempts

        Returns:
        {
            "riskScore": 0-100,
            "riskLevel": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
            "reasons": [...],
            "critical_rule_triggered": bool,
            "rule_breakdown": [...],
            "explanation": str
        }
        """
        base_score = 2
        total_points = base_score
        reasons: List[str] = []
        rule_breakdown: List[Dict[str, Any]] = []
        critical_rule_triggered = False

        for rule in cls.RULES:
            res: RuleEvaluationResult = rule.evaluate(inputs)
            if res.triggered:
                total_points += res.points
                if res.reason:
                    reasons.append(res.reason)
                if res.is_critical:
                    critical_rule_triggered = True

                rule_breakdown.append({
                    "rule_id": res.rule_id,
                    "rule_name": res.rule_name,
                    "points": res.points,
                    "reason": res.reason,
                    "is_critical": res.is_critical,
                    "details": res.details,
                })

        # Hard deterministic override: critical rules clamp to >= 85 and CRITICAL
        risk_score = min(100, max(0, total_points))

        if critical_rule_triggered:
            risk_score = max(85, risk_score)
            risk_level = "CRITICAL"
        else:
            if risk_score >= 85:
                risk_level = "CRITICAL"
            elif risk_score >= 60:
                risk_level = "HIGH"
            elif risk_score >= 30:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

        # Deterministic explainable synthesis
        default_explanation = cls._build_deterministic_explanation(
            risk_score=risk_score,
            risk_level=risk_level,
            reasons=reasons,
            critical_rule_triggered=critical_rule_triggered,
        )

        explanation = default_explanation
        if include_llm_explanation:
            explanation = cls._generate_llm_explanation(
                risk_score=risk_score,
                risk_level=risk_level,
                reasons=reasons,
                critical_rule_triggered=critical_rule_triggered,
                default_explanation=default_explanation,
            )

        return {
            "riskScore": risk_score,
            "riskLevel": risk_level,
            "reasons": reasons,
            "critical_rule_triggered": critical_rule_triggered,
            "rule_breakdown": rule_breakdown,
            "explanation": explanation,
            "inputs_summary": {
                "amount": inputs.get("transaction_amount"),
                "category": inputs.get("category"),
                "failed_attempts": inputs.get("failed_attempts"),
                "is_critical": critical_rule_triggered,
            },
        }

    @classmethod
    def _build_deterministic_explanation(
        cls,
        risk_score: int,
        risk_level: str,
        reasons: List[str],
        critical_rule_triggered: bool,
    ) -> str:
        """
        Deterministic, audit-compliant natural-language explanation.
        """
        if not reasons:
            return f"Transaction evaluated with a clean risk profile (Score: {risk_score}/100, Level: {risk_level}). No anomalous indicators detected."

        bullet_points = "\n".join([f"• {r}" for r in reasons])

        if critical_rule_triggered:
            prefix = "[CRITICAL SECURITY INTERVENTION] A non-negotiable deterministic security rule was triggered. System cannot allow automated execution.\n"
        elif risk_level == "HIGH":
            prefix = "[HIGH RISK ADVISORY] Elevated risk anomalies detected across multiple dimensions. Requires human supervisor review.\n"
        elif risk_level == "MEDIUM":
            prefix = "[MODERATE RISK NOTICE] Minor deviations observed from standard customer baseline.\n"
        else:
            prefix = "[LOW RISK] Transaction is within standard operating parameters.\n"

        return f"{prefix}Calculated Risk Score: {risk_score}/100 ({risk_level}).\nTriggered Factors:\n{bullet_points}"

    @classmethod
    def _generate_llm_explanation(
        cls,
        risk_score: int,
        risk_level: str,
        reasons: List[str],
        critical_rule_triggered: bool,
        default_explanation: str,
    ) -> str:
        """
        Optionally enhances explanation with LLM narrative.
        THE LLM MUST NEVER OVERRIDE CRITICAL DETERMINISTIC RULES OR CLASSIFICATIONS.
        """
        try:
            from intelligence.agents import BaseAgent

            class RiskAnalystAgent(BaseAgent):
                name = "RiskAnalyst"

            agent_caller = RiskAnalystAgent()
            prompt = (
                f"You are a Zero-Trust Financial Risk Analyst. Provide a brief 2-sentence executive summary "
                f"explaining why this transaction received a riskScore of {risk_score} and riskLevel of '{risk_level}'.\n"
                f"Deterministic triggered reasons:\n{', '.join(reasons)}\n"
                f"Critical rule triggered: {critical_rule_triggered}.\n"
                f"CRITICAL CONSTRAINT: You cannot dispute, alter, or downgrade the risk level or score. "
                f"Do not recommend bypassing security checks."
            )
            messages = [{"role": "user", "content": prompt}]
            narrative = agent_caller.call_gemini(messages, context={}, temperature=0.2)
            if narrative and len(str(narrative).strip()) > 10:
                text = str(narrative).strip()
                if critical_rule_triggered and "[CRITICAL" not in text:
                    text = f"[CRITICAL SECURITY INTERVENTION] {text}"
                return text
        except Exception as e:
            logger.warning(f"LLM risk explanation fallback to deterministic: {e}")

        return default_explanation

