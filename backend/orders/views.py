from django.db.models import Sum, Count, Q
from crm.models import ActivityLog, Notification
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Order, Payment, Refund, Payout, Settlement
from .serializers import (
    OrderSerializer,
    OrderStatusSerializer,
    RefundSerializer,
    PayoutSerializer,
    SettlementSerializer,
)


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        queryset = Order.objects.select_related("user", "payment").prefetch_related("items__product", "items__product__images", "items__product__store")
        mode = self.request.query_params.get("mode")
        if mode == "seller" or user.effective_role == "seller":
            store = getattr(getattr(user, "seller_profile", None), "store", None)
            if not store:
                return Order.objects.none()
            return queryset.filter(items__product__store=store).distinct()
        if user.effective_role == "admin":
            return queryset
        return queryset.filter(user=user)

    @action(detail=False, methods=["get"])
    def summary(self, request):
        queryset = self.get_queryset()
        user = request.user
        mode = request.query_params.get("mode")
        if user.effective_role == "seller" or mode == "seller":
            store = getattr(getattr(user, "seller_profile", None), "store", None)
            if not store:
                return Response({
                    "orders": 0,
                    "pending": 0,
                    "processing": 0,
                    "delivered": 0,
                    "revenue": "0",
                })
            from .models import OrderItem
            from decimal import Decimal
            seller_items = OrderItem.objects.filter(order__in=queryset, product__store=store)
            order_ids = seller_items.values_list("order_id", flat=True).distinct()
            orders_count = order_ids.count()
            pending = Order.objects.filter(id__in=order_ids, status="pending").count()
            processing = Order.objects.filter(id__in=order_ids, status="processing").count()
            delivered = Order.objects.filter(id__in=order_ids, status="delivered").count()
            revenue = sum((item.price * item.quantity for item in seller_items), Decimal("0"))
            return Response({
                "orders": orders_count,
                "pending": pending,
                "processing": processing,
                "delivered": delivered,
                "revenue": str(revenue),
            })

        agg = queryset.aggregate(
            orders=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            processing=Count("id", filter=Q(status="processing")),
            delivered=Count("id", filter=Q(status="delivered")),
            revenue=Sum("total_price"),
        )
        return Response({
            "orders": agg["orders"],
            "pending": agg["pending"],
            "processing": agg["processing"],
            "delivered": agg["delivered"],
            "revenue": str(agg["revenue"] or 0),
        })

    @action(detail=True, methods=["patch"])
    def status(self, request, pk=None):
        user = request.user
        if user.effective_role not in ["seller", "admin"]:
            return Response({"detail": "Only sellers and admins can update order status."}, status=403)

        order = self.get_object()
        serializer = OrderStatusSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        old_status = order.status
        serializer.save()

        ActivityLog.objects.create(
            actor=user,
            verb="updated_order_status",
            target_type="order",
            target_id=str(order.id),
            metadata={"from": old_status, "to": order.status},
        )
        Notification.objects.create(
            user=order.user,
            notification_type="status",
            title=f"Order #{order.id} is now {order.status}",
            body="Your order status was updated.",
        )
        return Response(OrderSerializer(order, context={"request": request}).data)

    @action(detail=False, methods=["post"], permission_classes=[permissions.AllowAny])
    def calculate_delivery(self, request):
        from .utils import calculate_delivery_info
        from products.models import Product
        
        shipping_address = request.data.get("shipping_address", "")
        items = request.data.get("items", [])
        product_ids = [item.get("product_id") for item in items if item.get("product_id")]
        
        # Build a {product_id: quantity} map so the algorithm can calculate real subtotals
        quantity_map = {}
        for item in items:
            pid = item.get("product_id")
            if pid:
                quantity_map[pid] = item.get("quantity", 1)
        
        products = Product.objects.select_related("category", "store").filter(id__in=product_ids, is_active=True)
        total_fee, item_deliveries = calculate_delivery_info(shipping_address, products, quantity_map)
        
        return Response({
            "total_fee": str(total_fee),
            "item_deliveries": item_deliveries
        })

from rest_framework.views import APIView
from intelligence.services.razorpay_service import RazorpayService
from intelligence.services.commerce_audit import CommerceAuditService
import json
from .models import Payment

class RazorpayWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, *args, **kwargs):
        body = request.body.decode('utf-8')
        signature = request.headers.get('X-Razorpay-Signature')
        
        if not signature:
            return Response({'error': 'Missing signature'}, status=400)
            
        if not RazorpayService.verify_webhook_signature(body, signature):
            return Response({'error': 'Invalid signature'}, status=400)
            
        try:
            event = json.loads(body)
            event_type = event.get('event')
            
            # Simple handling for MVP
            if event_type in ['payment.authorized', 'payment.captured', 'payment.failed']:
                payment_id = event['payload']['payment']['entity']['id']
                order_id = event['payload']['payment']['entity']['order_id']
                status = event['payload']['payment']['entity']['status']
                
                try:
                    payment = Payment.objects.get(provider_reference=order_id)
                    payment.status = status
                    payment.save()
                    
                    if status == 'captured' and payment.order.status == 'pending':
                        payment.order.status = 'processing'
                        payment.order.save()
                        
                    CommerceAuditService.log_webhook(event_type, payment_id, order_id, status)
                except Payment.DoesNotExist:
                    pass
                    
            return Response({'status': 'ok'})
        except Exception as e:
            return Response({'error': str(e)}, status=500)


from .models import Cart, CartItem
from products.models import Product
from products.serializers import ProductListSerializer

class CartView(APIView):
    """
    User-scoped Cart management:
    GET /api/cart/ -> Returns authenticated user's cart items from database.
    POST /api/cart/ -> Synchronizes user's cart items with the database.
    DELETE /api/cart/ -> Clears the user's cart in the database.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = cart.items.select_related('product', 'product__category', 'product__brand', 'product__store').prefetch_related('product__images').all()
        data = []
        for it in items:
            data.append({
                "product": ProductListSerializer(it.product, context={"request": request}).data,
                "quantity": it.quantity
            })
        return Response({"items": data})

    def post(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        raw_items = request.data.get("items", [])
        
        cart.items.all().delete()
        new_items = []
        for item_data in raw_items:
            prod_id = item_data.get("product_id")
            if not prod_id and isinstance(item_data.get("product"), dict):
                prod_id = item_data["product"].get("id")
            quantity = int(item_data.get("quantity", 1))
            if prod_id and quantity > 0:
                p = Product.objects.filter(id=prod_id).first()
                if p:
                    new_items.append(CartItem(cart=cart, product=p, quantity=quantity))
        
        if new_items:
            CartItem.objects.bulk_create(new_items)
            
        items = cart.items.select_related('product', 'product__category', 'product__brand', 'product__store').prefetch_related('product__images').all()
        data = []
        for it in items:
            data.append({
                "product": ProductListSerializer(it.product, context={"request": request}).data,
                "quantity": it.quantity
            })
        return Response({"items": data})

    def delete(self, request):
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart.items.all().delete()
        return Response({"items": []})


class RefundViewSet(viewsets.ModelViewSet):
    serializer_class = RefundSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if user.effective_role == "admin":
            return Refund.objects.all().order_by("-created_at")
        if user.effective_role == "seller":
            store = getattr(getattr(user, "seller_profile", None), "store", None)
            if store:
                return Refund.objects.filter(order__items__product__store=store).distinct().order_by("-created_at")
            return Refund.objects.none()
        return Refund.objects.filter(order__user=user).order_by("-created_at")


class PayoutViewSet(viewsets.ModelViewSet):
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if user.effective_role == "admin":
            return Payout.objects.all().order_by("-created_at")
        if user.effective_role == "seller":
            store = getattr(getattr(user, "seller_profile", None), "store", None)
            if store:
                return Payout.objects.filter(store=store).order_by("-created_at")
        return Payout.objects.none()


class SettlementViewSet(viewsets.ModelViewSet):
    serializer_class = SettlementSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        user = self.request.user
        if user.effective_role == "admin":
            return Settlement.objects.all().order_by("-settlement_date", "-created_at")
        if user.effective_role == "seller":
            store = getattr(getattr(user, "seller_profile", None), "store", None)
            if store:
                return Settlement.objects.filter(store=store).order_by("-settlement_date", "-created_at")
        return Settlement.objects.none()

