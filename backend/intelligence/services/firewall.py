from decimal import Decimal
from intelligence.models import MerchantConfig
from orders.models import TransactionDecision, Consent

class TransactionFirewallService:
    @classmethod
    def evaluate_checkout(cls, cart=None, items=None, actor_type='human', requested_amount=None, buyer_budget=None):
        """
        Evaluate if a checkout should be allowed based on firewall rules and policy engine.
        Accepts either a 'cart' object or a list of 'items' (dict with 'product' and 'quantity').
        """
        config = MerchantConfig.get_solo()
        reason_codes = []
        decision = 'ALLOW'
        risk_score = Decimal('0.0')
        
        checkout_items = items
        if cart and not checkout_items:
            checkout_items = cart.items.all()
            
        if not checkout_items:
            return cls._create_decision(cart, 'ALLOW', [], Decimal('0.0'), Decimal('0.0'), checkout_items)
            
        # 1. AI Checkout Enabled check
        if actor_type == 'ai_agent' and not config.ai_checkout_enabled:
            return cls._create_decision(cart, 'DENY', ['AI_CHECKOUT_DISABLED'], Decimal('1.0'), Decimal('0.0'), checkout_items)
            
        # 2. Total quantity check
        total_quantity = sum(item.quantity if hasattr(item, 'quantity') else item['quantity'] for item in checkout_items)
        if total_quantity > config.max_ai_quantity:
            reason_codes.append('EXCEEDS_MAX_QUANTITY')
            decision = 'DENY'
            risk_score += Decimal('0.5')
            
        # 3. Total amount check
        actual_total = sum((item.product.current_price * item.quantity) if hasattr(item, 'quantity') else (item['product'].current_price * item['quantity']) for item in checkout_items)
        if actual_total > config.max_ai_order_value:
            reason_codes.append('LIMIT_EXCEEDED')
            decision = 'REVIEW'
            risk_score += Decimal('0.6')
            
        # 4. Amount mismatch check
        if requested_amount is not None and requested_amount != actual_total:
            reason_codes.append('AMOUNT_MISMATCH')
            decision = 'DENY'
            risk_score += Decimal('0.8')
            
        # 5. Buyer Budget Check (New)
        if buyer_budget is not None and actual_total > buyer_budget:
            reason_codes.append('BUDGET_EXCEEDED')
            decision = 'DENY'
            
        # 6. Inventory & Margin check (New)
        for item in checkout_items:
            product = item.product if hasattr(item, 'product') else item['product']
            quantity = item.quantity if hasattr(item, 'quantity') else item['quantity']
            
            # Margin check
            price = product.current_price
            cost = product.cost_paise / Decimal("100") if getattr(product, "cost_paise", 0) else Decimal("0")
            margin_pct = ((price - cost) / price * Decimal("100")) if price > 0 else Decimal("0")
            
            # Use configured margin or default to 10%
            min_margin = getattr(config, "min_margin_pct", Decimal("10.0"))
            if margin_pct < min_margin:
                reason_codes.append('MARGIN_FAIL')
                decision = 'DENY'
                
            # Inventory check
            if hasattr(product, 'inventory'):
                if quantity > product.inventory.available_quantity:
                    reason_codes.append('INSUFFICIENT_INVENTORY')
                    decision = 'DENY'
                    risk_score += Decimal('0.2')
            else:
                if quantity > product.stock:
                    reason_codes.append('INSUFFICIENT_STOCK')
                    decision = 'DENY'
                    risk_score += Decimal('0.2')
                    
        # 7. Consent check for AI
        if actor_type == 'ai_agent' and decision == 'ALLOW' and cart:
            if not Consent.objects.filter(cart=cart).exists():
                decision = 'REQUIRE_USER_CONFIRMATION'
                reason_codes.append('MISSING_USER_CONSENT')
                
        # Deduplicate reasons
        reason_codes = list(dict.fromkeys(reason_codes))
        return cls._create_decision(cart, decision, reason_codes, risk_score, actual_total, checkout_items, actor_type)
        
    @classmethod
    def _create_decision(cls, cart, decision, reason_codes, risk_score, amount, checkout_items, actor_type='human'):
        inventory_snapshot = {}
        for item in checkout_items:
            product = item.product if hasattr(item, 'product') else item['product']
            if hasattr(product, 'inventory'):
                inventory_snapshot[str(product.id)] = product.inventory.available_quantity
            else:
                inventory_snapshot[str(product.id)] = product.stock
                
        return TransactionDecision.objects.create(
            cart=cart,
            decision=decision,
            risk_score=risk_score,
            reason_codes=reason_codes,
            actor_type=actor_type,
            policy_version='1.0',
            inventory_snapshot=inventory_snapshot,
            amount=amount
        )
