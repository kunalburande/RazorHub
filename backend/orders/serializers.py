from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.db.models import Q
from rest_framework import serializers
from crm.models import ActivityLog, Notification
from products.models import Product
from products.serializers import ProductSerializer
from .models import Order, OrderItem, Payment, Refund, Payout, Settlement




PROMO_CODES = {
    "aura10": Decimal("10"),
    "balensarkar12": Decimal("12"),
}


class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(source="product", queryset=Product.objects.filter(is_active=True), write_only=True)

    class Meta:
        model = OrderItem
        fields = ["id", "product", "product_id", "quantity", "price"]
        read_only_fields = ["id", "product", "price"]


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "order", "method", "status", "amount", "provider_reference", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "amount", "provider_reference", "created_at", "updated_at"]


class RefundSerializer(serializers.ModelSerializer):
    order_id = serializers.IntegerField(source="order.id", read_only=True)
    customer_email = serializers.EmailField(source="order.user.email", read_only=True)

    class Meta:
        model = Refund
        fields = ["id", "refund_id", "order", "order_id", "customer_email", "payment", "amount", "currency", "reason", "status", "notes", "created_at"]


class PayoutSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = Payout
        fields = ["id", "payout_id", "store", "store_name", "recipient_name", "recipient_account", "amount", "currency", "mode", "status", "utr", "narration", "created_at"]


class SettlementSerializer(serializers.ModelSerializer):
    store_name = serializers.CharField(source="store.name", read_only=True)

    class Meta:
        model = Settlement
        fields = ["id", "settlement_id", "store", "store_name", "amount", "fees", "tax", "net_amount", "status", "utr", "settlement_date", "is_delayed", "notes", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    payment = PaymentSerializer(read_only=True)
    customer_email = serializers.EmailField(source="user.email", read_only=True)
    promo_code = serializers.CharField(required=False, allow_blank=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            mode = request.query_params.get("mode")
            if request.user.effective_role == "seller" or mode == "seller":
                store = getattr(getattr(request.user, "seller_profile", None), "store", None)
                if not store:
                    from sellers.models import Store
                    store = (
                        Store.objects.filter(seller__user=request.user).first()
                        or Store.objects.filter(support_email__iexact=getattr(request.user, "email", "")).first()
                    )
                if store:
                    filtered_items = []
                    for item in data.get("items", []):
                        prod = item.get("product")
                        if isinstance(prod, dict):
                            st = prod.get("store")
                            st_id = st.get("id") if isinstance(st, dict) else prod.get("store_id", st)
                            if st_id == store.id:
                                filtered_items.append(item)
                    data["items"] = filtered_items if filtered_items else data.get("items", [])
        return data

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_email",
            "status",
            "payment_method",
            "delivery_eta",
            "delivery_fee",
            "promo_code",
            "discount_amount",
            "total_price",
            "shipping_address",
            "customer_note",
            "items",
            "payment",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "customer_email",
            "status",
            "delivery_eta",
            "delivery_fee",
            "discount_amount",
            "total_price",
            "payment",
            "created_at",
            "updated_at",
        ]

    def validate_promo_code(self, value):
        code = (value or "").strip().lower()
        if code and code not in PROMO_CODES:
            raise serializers.ValidationError("Promo code is not valid.")
        return code

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Order must contain at least one item.")
        for item in items:
            product = item["product"]
            quantity = item["quantity"]
            if quantity < 1:
                raise serializers.ValidationError("Quantity must be at least 1.")
            if product.stock < quantity:
                raise serializers.ValidationError(f"{product.name} only has {product.stock} units available.")
        return items

    @transaction.atomic
    def create(self, validated_data):
        from .utils import calculate_delivery_info
        from intelligence.services.firewall import TransactionFirewallService
        
        items_data = validated_data.pop("items")
        user = self.context["request"].user
        promo_code = validated_data.get("promo_code", "").strip().lower()
        shipping_address = validated_data.get("shipping_address", "")
        
        # Policy Engine Guard
        decision_obj = TransactionFirewallService.evaluate_checkout(
            items=items_data,
            actor_type='human',
            buyer_budget=None
        )
        if decision_obj.decision == 'DENY':
            raise serializers.ValidationError(
                {"policy_engine": f"Order blocked due to policy violations: {', '.join(decision_obj.reason_codes)}"}
            )
        
        products = [item["product"] for item in items_data]
        quantity_map = {item["product"].id: item["quantity"] for item in items_data}
        total_fee, item_deliveries = calculate_delivery_info(shipping_address, products, quantity_map)
        
        # Aggregate unique ETAs
        unique_etas = set(info["eta"] for info in item_deliveries.values())
        delivery_eta = ", ".join(unique_etas) if unique_etas else "Unknown"
        
        subtotal = sum(
            (item["product"].current_price * item["quantity"] for item in items_data),
            Decimal("0"),
        )
        discount_rate = PROMO_CODES.get(promo_code, Decimal("0"))
        discount_amount = (subtotal * discount_rate / Decimal("100")).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )
        total = (subtotal + total_fee - discount_amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        validated_data["promo_code"] = promo_code
        validated_data["delivery_fee"] = total_fee
        validated_data["delivery_eta"] = delivery_eta
        validated_data["discount_amount"] = discount_amount
        validated_data["total_price"] = total
        order = Order.objects.create(user=user, **validated_data)

        order_items = []
        for item in items_data:
            product = item["product"]
            quantity = item["quantity"]
            # Lock the product row to prevent concurrent stock race conditions
            locked_product = Product.objects.select_for_update().get(pk=product.pk)
            if locked_product.stock < quantity:
                raise serializers.ValidationError(
                    f"{locked_product.name} only has {locked_product.stock} units left (you requested {quantity})."
                )
            order_items.append(OrderItem(order=order, product=locked_product, quantity=quantity, price=locked_product.current_price))
            locked_product.stock = max(locked_product.stock - quantity, 0)
            locked_product.save(update_fields=["stock"])
            if hasattr(locked_product, "inventory"):
                locked_product.inventory.quantity = locked_product.stock
                locked_product.inventory.save(update_fields=["quantity", "updated_at"])

        OrderItem.objects.bulk_create(order_items)
        
        request_data = self.context.get("request", {}).data if hasattr(self.context.get("request", None), "data") else {}
        provider_ref = request_data.get("provider_reference", "")
        explicit_payment_status = request_data.get("payment_status", "")

        if explicit_payment_status == "failed" or "fail" in str(provider_ref).lower():
            payment_status = Payment.STATUS_FAILED
            order.status = "cancelled"
            order.save(update_fields=["status"])
        elif order.payment_method == Order.PAYMENT_RAZORPAY and provider_ref:
            payment_status = Payment.STATUS_PAID
            order.status = "processing"
            order.save(update_fields=["status"])
        else:
            payment_status = Payment.STATUS_PENDING

        Payment.objects.create(
            order=order,
            method=order.payment_method,
            amount=total,
            status=payment_status,
            provider_reference=provider_ref,
        )
        ActivityLog.objects.create(
            actor=user,
            verb="created_order",
            target_type="order",
            target_id=str(order.id),
            metadata={
                "payment_method": order.payment_method,
                "payment_status": payment_status,
                "provider_reference": provider_ref,
                "total": str(total),
            },
        )
        status_text = "placed" if payment_status != Payment.STATUS_FAILED else "failed"
        Notification.objects.create(
            user=user,
            notification_type="order",
            title=f"Order #{order.id} {status_text}",
            body=f"Your order total is ₹{total} (Payment: {payment_status.upper()}).",
        )

        seller_users = {
            item["product"].store.seller.user
            for item in items_data
            if item["product"].store and item["product"].store.seller
        }
        for seller_user in seller_users:
            Notification.objects.create(
                user=seller_user,
                notification_type="order",
                title=f"New order #{order.id}",
                body="A customer placed an order containing your products.",
            )

        # Clean up ordered items from user's active database Cart
        if user and getattr(user, "is_authenticated", False):
            try:
                from .models import Cart as DbCart
                db_cart = DbCart.objects.filter(user=user).first()
                if db_cart:
                    ordered_product_ids = [item["product"].id for item in items_data if hasattr(item.get("product"), "id")]
                    if ordered_product_ids:
                        db_cart.items.filter(product_id__in=ordered_product_ids).delete()
                    if not db_cart.items.exists():
                        db_cart.items.all().delete()
            except Exception:
                pass

        return order


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]
