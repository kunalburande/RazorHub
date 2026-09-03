from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class RuleEvaluationResult:
    rule_id: str
    rule_name: str
    points: int
    triggered: bool
    reason: Optional[str] = None
    is_critical: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


class BaseRiskRule:
    rule_id: str = "base_rule"
    rule_name: str = "Base Risk Rule"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        raise NotImplementedError


class AmountAnomalyRule(BaseRiskRule):
    rule_id: str = "amount_anomaly"
    rule_name: str = "Transaction Amount Anomaly"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        amount = float(inputs.get("transaction_amount") or 0.0)
        avg_amount = float(inputs.get("customer_avg_amount") or 0.0)

        if amount <= 0:
            return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)

        if avg_amount > 0:
            ratio = amount / avg_amount
            if ratio >= 4.0:
                return RuleEvaluationResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    points=25,
                    triggered=True,
                    reason=f"amount {ratio:.1f}x customer average",
                    details={"amount": amount, "customer_avg": avg_amount, "ratio": round(ratio, 2)},
                )
            elif ratio >= 3.0:
                return RuleEvaluationResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    points=18,
                    triggered=True,
                    reason=f"amount {ratio:.1f}x customer average",
                    details={"amount": amount, "customer_avg": avg_amount, "ratio": round(ratio, 2)},
                )
            elif ratio >= 2.0:
                return RuleEvaluationResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    points=10,
                    triggered=True,
                    reason=f"amount {ratio:.1f}x customer average",
                    details={"amount": amount, "customer_avg": avg_amount, "ratio": round(ratio, 2)},
                )

        # Extreme absolute amount without average history
        if amount >= 100000.0:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=20,
                triggered=True,
                reason=f"unusually high absolute transaction amount (₹{amount:,.2f})",
                details={"amount": amount},
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class FailedAttemptsRule(BaseRiskRule):
    rule_id: str = "failed_attempts"
    rule_name: str = "Failed Authorization Attempts"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        failed_attempts = int(inputs.get("failed_attempts") or 0)

        if failed_attempts >= 10:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=45,
                triggered=True,
                reason=f"{failed_attempts} failed attempts in 10 minutes (severe brute-force anomaly)",
                is_critical=True,
                details={"failed_attempts": failed_attempts},
            )
        elif failed_attempts >= 6:
            # Matches user example: "7 failed attempts in 10 minutes"
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=28,
                triggered=True,
                reason=f"{failed_attempts} failed attempts in 10 minutes",
                details={"failed_attempts": failed_attempts},
            )
        elif failed_attempts >= 3:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=15,
                triggered=True,
                reason=f"{failed_attempts} failed attempts in recent window",
                details={"failed_attempts": failed_attempts},
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class DeviceAnomalyRule(BaseRiskRule):
    rule_id: str = "device_anomaly"
    rule_name: str = "Device & Client Fingerprint Risk"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        device = inputs.get("device") or {}
        if isinstance(device, str):
            device = {"name": device, "is_new_device": True}

        is_new_device = bool(device.get("is_new_device"))
        is_vpn_proxy = bool(device.get("is_vpn_proxy") or device.get("is_tor"))
        mismatch = bool(device.get("device_fingerprint_mismatch"))

        if is_new_device and is_vpn_proxy:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=22,
                triggered=True,
                reason="new device using anonymizing VPN/proxy",
                details=device,
            )
        elif is_new_device:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=10,
                triggered=True,
                reason="new device",
                details=device,
            )
        elif is_vpn_proxy:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=15,
                triggered=True,
                reason="traffic routed through anonymizing VPN/proxy",
                details=device,
            )
        elif mismatch:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=12,
                triggered=True,
                reason="hardware fingerprint mismatch against session token",
                details=device,
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class MerchantTrustRule(BaseRiskRule):
    rule_id: str = "merchant_trust"
    rule_name: str = "Merchant Reputation & History"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        merchant_history = inputs.get("merchant_history") or {}
        if isinstance(merchant_history, str):
            merchant_history = {"merchant_name": merchant_history, "is_new": True}

        is_new = bool(merchant_history.get("is_new") or merchant_history.get("total_transactions") == 0)
        dispute_rate = float(merchant_history.get("dispute_rate") or 0.0)

        if is_new:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=9,
                triggered=True,
                reason="new merchant",
                details=merchant_history,
            )
        elif dispute_rate > 0.05:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=20,
                triggered=True,
                reason=f"merchant has high historical dispute rate ({dispute_rate:.1%})",
                details=merchant_history,
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class CategoryRiskRule(BaseRiskRule):
    rule_id: str = "category_risk"
    rule_name: str = "Transaction Category Risk"

    HIGH_RISK_CATEGORIES = {
        "crypto": 8,
        "cryptocurrency": 8,
        "gambling": 15,
        "gaming_tokens": 10,
        "gift_cards": 10,
        "prepaid_voucher": 10,
        "cash": 20,
        "unknown": 8,
        "unusual": 8,
    }


    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        category = str(inputs.get("category") or "").lower().strip()
        is_unusual_flag = bool(inputs.get("is_unusual_category"))

        if category in self.HIGH_RISK_CATEGORIES or is_unusual_flag:
            points = self.HIGH_RISK_CATEGORIES.get(category, 8)
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=points,
                triggered=True,
                reason="unusual category",
                details={"category": category},
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class LocationAnomalyRule(BaseRiskRule):
    rule_id: str = "location_anomaly"
    rule_name: str = "Geolocation & Travel Velocity"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        loc = inputs.get("location") or {}
        if isinstance(loc, str):
            loc = {"country": loc}

        is_impossible = bool(loc.get("is_impossible_travel"))
        distance_km = float(loc.get("distance_km") or 0.0)
        current_country = str(loc.get("current_country") or "").upper()
        home_country = str(loc.get("home_country") or "").upper()

        if is_impossible or distance_km >= 3000:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=50,
                triggered=True,
                reason=f"impossible travel detected: {int(distance_km)}km displacement in under 1 hour",
                is_critical=True,
                details=loc,
            )
        elif current_country and home_country and current_country != home_country:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=15,
                triggered=True,
                reason=f"location country mismatch ({current_country} vs {home_country})",
                details=loc,
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class ChargebackHistoryRule(BaseRiskRule):
    rule_id: str = "chargeback_history"
    rule_name: str = "Customer Chargeback & Dispute History"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        cb = inputs.get("chargeback_history") or {}
        count = int(cb.get("chargeback_count") or 0)
        rate = float(cb.get("chargeback_rate") or 0.0)

        if count >= 5:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=50,
                triggered=True,
                reason=f"excessive chargeback history ({count} chargebacks)",
                is_critical=True,
                details=cb,
            )
        elif count >= 2 or rate > 0.05:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=25,
                triggered=True,
                reason=f"elevated chargeback history ({count} chargebacks, {rate:.1%} rate)",
                details=cb,
            )
        elif count == 1:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=10,
                triggered=True,
                reason=f"prior dispute recorded on account",
                details=cb,
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class RefundHistoryRule(BaseRiskRule):
    rule_id: str = "refund_history"
    rule_name: str = "Refund Spike History"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        ref = inputs.get("refund_history") or {}
        count = int(ref.get("refund_count") or 0)
        rate = float(ref.get("refund_rate") or 0.0)

        if rate >= 0.30 or count >= 5:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=18,
                triggered=True,
                reason=f"elevated customer refund rate ({rate:.1%})",
                details=ref,
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class VelocityRule(BaseRiskRule):
    rule_id: str = "velocity"
    rule_name: str = "Transaction Velocity Spike"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        vel = inputs.get("velocity") or {}
        txns_10m = int(vel.get("txns_last_10m") or 0)
        txns_1h = int(vel.get("txns_last_1h") or 0)

        if txns_10m >= 15:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=45,
                triggered=True,
                reason=f"severe velocity burst ({txns_10m} txns in 10 minutes)",
                is_critical=True,
                details=vel,
            )
        elif txns_10m >= 5:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=20,
                triggered=True,
                reason=f"high transaction velocity ({txns_10m} txns in 10m)",
                details=vel,
            )
        elif txns_1h >= 10:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=12,
                triggered=True,
                reason=f"unusual hourly velocity ({txns_1h} txns in 1 hour)",
                details=vel,
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class CustomerAgeRule(BaseRiskRule):
    rule_id: str = "customer_age"
    rule_name: str = "Customer Account Age & Trust"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        # Age in days
        age_days = inputs.get("customer_age_days")
        if age_days is None and inputs.get("customer_age") is not None:
            age_val = inputs.get("customer_age")
            if isinstance(age_val, (int, float)) and age_val < 365:
                age_days = int(age_val)

        if age_days is not None:
            age_days = int(age_days)
            if age_days < 7:
                return RuleEvaluationResult(
                    rule_id=self.rule_id,
                    rule_name=self.rule_name,
                    points=10,
                    triggered=True,
                    reason=f"new account created {age_days} days ago",
                    details={"customer_age_days": age_days},
                )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)


class PaymentHistoryRule(BaseRiskRule):
    rule_id: str = "payment_history"
    rule_name: str = "Historical Payment Success Rate"

    def evaluate(self, inputs: Dict[str, Any]) -> RuleEvaluationResult:
        hist = inputs.get("payment_history") or {}
        success = int(hist.get("successful_transactions") or 0)
        failed = int(hist.get("failed_transactions") or 0)
        total = success + failed

        if total >= 5 and (failed / total) > 0.60:
            return RuleEvaluationResult(
                rule_id=self.rule_id,
                rule_name=self.rule_name,
                points=18,
                triggered=True,
                reason=f"high payment failure history ({failed}/{total} failed)",
                details=hist,
            )

        return RuleEvaluationResult(self.rule_id, self.rule_name, 0, False)
