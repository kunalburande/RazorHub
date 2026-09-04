from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum
from django.db.models.functions import TruncMonth
from rest_framework.exceptions import PermissionDenied
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from orders.models import Order, OrderItem
from products.models import Product
from .models import SellerProfile, Store
from .serializers import SellerProfileSerializer, StoreSerializer


class IsSellerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.effective_role in ["seller", "admin"]))


class StorePermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and (user.effective_role in ["seller", "admin"]))


class SellerProfileViewSet(viewsets.ModelViewSet):
    serializer_class = SellerProfileSerializer
    permission_classes = [IsSellerOrAdmin]

    def get_queryset(self):
        queryset = SellerProfile.objects.select_related("user").prefetch_related("store").order_by("-id")
        if self.request.user.effective_role == "admin":
            return queryset
        return queryset.filter(user=self.request.user)

    def perform_update(self, serializer):
        if self.request.user.effective_role != "admin":
            forbidden = {"status", "internal_notes"} & set(self.request.data.keys())
            if forbidden:
                raise PermissionDenied("Only admins can change seller moderation fields.")
        serializer.save()

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        seller_profile = getattr(request.user, "seller_profile", None)
        if not seller_profile:
            return Response({"detail": "Seller profile not found."}, status=404)

        store = getattr(seller_profile, "store", None)
        if not store:
            return Response({
                "store": None, "products": 0, "active_products": 0,
                "orders": 0, "units_sold": 0, "revenue": "0",
                "top_products": [], "top_categories": [],
                "recent_orders": [], "monthly_revenue": [],
                "low_stock_products": [],
            })

        # Basic product stats
        product_stats = Product.objects.filter(store=store).aggregate(
            total=Count("id"),
            active=Count("id", filter=Q(is_active=True)),
        )

        # Order stats (only orders containing this seller's products)
        line_total = ExpressionWrapper(F("price") * F("quantity"), output_field=DecimalField(max_digits=12, decimal_places=2))
        seller_order_items = OrderItem.objects.filter(product__store=store)
        
        order_stats = seller_order_items.aggregate(
            distinct_orders=Count("order", distinct=True),
            units_sold=Sum("quantity"),
            revenue=Sum(line_total),
        )

        # Top 5 products by order count
        prod_line_total = ExpressionWrapper(F("order_items__price") * F("order_items__quantity"), output_field=DecimalField(max_digits=12, decimal_places=2))
        top_products = list(
            Product.objects.filter(store=store)
            .annotate(order_count=Count("order_items"), total_revenue=Sum(prod_line_total, default=0))
            .order_by("-order_count")
            .values("id", "name", "stock", "order_count", "total_revenue")[:5]
        )

        # Top categories by revenue
        top_categories = list(
            seller_order_items
            .values("product__category__name")
            .annotate(
                category_name=F("product__category__name"),
                cat_revenue=Sum(line_total),
                cat_units=Sum("quantity"),
            )
            .order_by("-cat_revenue")
            .values("category_name", "cat_revenue", "cat_units")[:5]
        )

        # Recent 10 orders
        seller_order_ids = seller_order_items.values_list("order_id", flat=True).distinct()[:10]
        recent_orders = list(
            Order.objects.filter(id__in=seller_order_ids)
            .select_related("user")
            .order_by("-created_at")[:10]
            .values("id", "user__email", "status", "total_price", "payment_method", "created_at")
        )
        # Serialize datetime for JSON
        for o in recent_orders:
            o["created_at"] = o["created_at"].isoformat() if o.get("created_at") else None
            o["total_price"] = str(o["total_price"]) if o.get("total_price") else "0"

        # Monthly revenue (last 6 months)
        monthly_revenue = list(
            seller_order_items
            .filter(order__status__in=["processing", "shipped", "delivered"])
            .annotate(month=TruncMonth("order__created_at"))
            .values("month")
            .annotate(revenue=Sum(line_total), orders=Count("order", distinct=True))
            .order_by("month")
        )
        for m in monthly_revenue:
            m["month"] = m["month"].isoformat() if m.get("month") else None
            m["revenue"] = str(m["revenue"]) if m.get("revenue") else "0"

        # Low stock alerts (stock < 10)
        low_stock = list(
            Product.objects.filter(store=store, is_active=True, stock__lt=10)
            .order_by("stock")
            .values("id", "name", "stock", "category__name")[:10]
        )

        return Response({
            "store": StoreSerializer(store).data,
            "products": product_stats["total"],
            "active_products": product_stats["active"],
            "orders": order_stats["distinct_orders"] or 0,
            "units_sold": order_stats["units_sold"] or 0,
            "revenue": str(order_stats["revenue"] or 0),
            "top_products": top_products,
            "top_categories": top_categories,
            "recent_orders": recent_orders,
            "monthly_revenue": monthly_revenue,
            "low_stock_products": low_stock,
        })


class StoreViewSet(viewsets.ModelViewSet):
    serializer_class = StoreSerializer
    permission_classes = [StorePermission]
    lookup_field = "slug"
    pagination_class = None

    def get_queryset(self):
        queryset = Store.objects.filter(is_active=True).select_related("seller", "seller__user")
        if self.request.method in permissions.SAFE_METHODS:
            return queryset
        if self.request.user.effective_role == "admin":
            return Store.objects.select_related("seller", "seller__user")
        return queryset.filter(seller__user=self.request.user)

    def perform_create(self, serializer):
        seller_profile = self.request.user.seller_profile
        serializer.save(seller=seller_profile)
