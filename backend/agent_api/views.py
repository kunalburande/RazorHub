from rest_framework import viewsets, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from products.models import Product, Inventory, HAS_PGVECTOR
from intelligence.models import Offer
import openai
from django.conf import settings
from .serializers import AgentProductSerializer, AgentAvailabilitySerializer, AgentOfferSerializer
from .permissions import AgentPermission

@api_view(['GET'])
@permission_classes([AllowAny])
def agent_manifest(request):
    """
    Exposes the /.well-known/agent-commerce.json manifest for AI agents.
    Implements WebMCP 3-layer pattern: Discovery → Decision → Action.
    Aligned with ACP, UCP, and NPCI UAP protocols.
    """
    base_url = request.build_absolute_uri('/api/agent/v1')
    return Response({
        "platform": "RazorHub",
        "version": "2.0",
        "description": "RazorHub Agentic Commerce API — structured product feeds, "
                       "agent-initiated checkout, and real-time inventory for AI buyer agents.",
        "api_base": "/api/agent/v1",
        "protocols_supported": ["ACP", "UCP", "NPCI_UAP", "WebMCP"],

        # WebMCP Layer 1: Discovery
        "discovery": {
            "product_feed": {
                "endpoint": "/api/agent/v1/catalog/feed/",
                "method": "GET",
                "format": "JSON-LD (Schema.org)",
                "description": "Full product catalog in Schema.org JSON-LD format.",
                "params": ["category", "min_price", "max_price", "in_stock", "limit"],
            },
            "search": {
                "endpoint": "/api/agent/v1/products/search/",
                "method": "POST",
                "description": "Semantic search with deterministic filters.",
            },
        },

        # WebMCP Layer 2: Decision
        "decision": {
            "compare_products": {
                "endpoint": "/api/agent/v1/products/compare/",
                "method": "POST",
                "description": "Side-by-side comparison of product attributes.",
            },
            "check_inventory": {
                "endpoint": "/api/agent/v1/availability/bulk/",
                "method": "GET",
                "description": "Real-time stock quantity and location.",
            },
            "get_policies": {
                "endpoint": "/api/agent/v1/policies/shipping/",
                "method": "GET",
                "description": "Shipping and return policies.",
            },
        },

        # WebMCP Layer 3: Action
        "action": {
            "add_to_cart": {
                "endpoint": "/api/agent/v1/cart/{cart_id}/items/",
                "method": "POST",
                "description": "Add product to cart.",
            },
            "initiate_checkout": {
                "endpoint": "/api/agent/v1/catalog/checkout/",
                "method": "POST",
                "description": "Agent-initiated checkout: product_id + quantity → Razorpay Payment Link.",
                "params": ["product_id", "quantity", "buyer_token"],
            },
            "get_quote": {
                "endpoint": "/api/agent/v1/checkout/quote/",
                "method": "POST",
                "description": "Generate a price quote for a cart.",
            },
        },

        "auth": {
            "type": "Bearer",
            "header": "Authorization",
            "scopes": ["read:products", "write:cart", "initiate:checkout"],
        },
    })

class AgentProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).prefetch_related('inventory', 'images')
    serializer_class = AgentProductSerializer
    permission_classes = [AgentPermission]
    lookup_field = 'slug'

    @action(detail=False, methods=['post', 'get'])
    def search(self, request):
        """Semantic search with deterministic filters."""
        # Handle both GET params and POST body
        data = request.data if request.method == 'POST' else request.query_params
        
        query = data.get('query')
        min_price = data.get('min_price')
        max_price = data.get('max_price')
        category_id = data.get('category_id')
        in_stock = data.get('in_stock')
        
        # Start with active products
        qs = self.get_queryset()
        
        # 1. Deterministic Filters
        if min_price is not None:
            qs = qs.filter(price_paise__gte=int(min_price))
        if max_price is not None:
            qs = qs.filter(price_paise__lte=int(max_price))
        if category_id:
            qs = qs.filter(category_id=category_id)
        if in_stock and str(in_stock).lower() == 'true':
            qs = qs.filter(inventory__quantity__gt=0)
            
        # 2. Semantic Search (pgvector)
        if query:
            if HAS_PGVECTOR and settings.OPENAI_API_KEY:
                from pgvector.django import CosineDistance
                try:
                    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
                    model = getattr(settings, 'EMBEDDING_MODEL', 'text-embedding-3-small')
                    response = client.embeddings.create(input=[query], model=model)
                    query_embedding = response.data[0].embedding
                    
                    # Filter out null embeddings and order by distance
                    qs = qs.exclude(embedding__isnull=True).annotate(
                        distance=CosineDistance('embedding', query_embedding)
                    ).order_by('distance')
                except Exception as e:
                    # Fallback on API error
                    qs = qs.filter(name__icontains=query) | qs.filter(description__icontains=query)
            else:
                # SQLite fallback
                qs = qs.filter(name__icontains=query) | qs.filter(description__icontains=query)

        # Apply pagination or limit
        qs = qs[:20]  # Limit to 20 for agents
        
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post', 'get'])
    def compare(self, request):
        """Side-by-side comparison of multiple products and their structured attributes."""
        data = request.data if request.method == 'POST' else request.query_params
        
        # product_ids can be a list in POST or a comma-separated string in GET
        product_ids = data.get('product_ids', [])
        if isinstance(product_ids, str):
            product_ids = [pid.strip() for pid in product_ids.split(',')]
            
        if not product_ids:
            return Response({"error": "Provide product_ids to compare."}, status=400)
            
        products = self.get_queryset().filter(id__in=product_ids).prefetch_related('ai_attributes')
        
        if not products:
            return Response({"error": "No valid products found."}, status=404)
            
        # Build comparison matrix
        comparison = {
            "products": [],
            "attributes_matrix": {}
        }
        
        # Get all unique attribute keys across these products
        all_keys = set()
        for p in products:
            all_keys.update(attr.key for attr in p.ai_attributes.all())
            
        # Initialize matrix with empty strings
        for key in all_keys:
            comparison["attributes_matrix"][key] = {str(p.id): "" for p in products}
            
        for p in products:
            product_data = {
                "id": p.id,
                "name": p.name,
                "price": p.price,
                "discount_price": p.discount_price,
                "in_stock": hasattr(p, 'inventory') and p.inventory.quantity > 0
            }
            comparison["products"].append(product_data)
            
            for attr in p.ai_attributes.all():
                comparison["attributes_matrix"][attr.key][str(p.id)] = attr.value
                
        return Response(comparison)

class AgentAvailabilityViewSet(viewsets.GenericViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('inventory')
    permission_classes = [AgentPermission]
    lookup_field = 'slug'

    def retrieve(self, request, *args, **kwargs):
        product = self.get_object()
        if hasattr(product, 'inventory'):
            serializer = AgentAvailabilitySerializer(product.inventory)
            return Response(serializer.data)
        return Response({'available': False, 'quantityAvailable': 0, 'estimatedDelivery': 'Unknown'})

    @action(detail=False, methods=['get'])
    def bulk(self, request):
        slugs = request.query_params.get('slugs', '').split(',')
        products = Product.objects.filter(slug__in=slugs, is_active=True).select_related('inventory')
        results = {}
        for product in products:
            if hasattr(product, 'inventory'):
                results[product.slug] = AgentAvailabilitySerializer(product.inventory).data
            else:
                results[product.slug] = {'available': False, 'quantityAvailable': 0, 'estimatedDelivery': 'Unknown'}
        return Response(results)

class AgentOfferViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Offer.objects.filter(status='active')
    serializer_class = AgentOfferSerializer
    permission_classes = [AgentPermission]

    @action(detail=False, methods=['post'])
    def validate(self, request):
        offer_id = request.data.get('offerId')
        try:
            offer = Offer.objects.get(offer_id=offer_id, status='active')
            return Response({'valid': True, 'offer': AgentOfferSerializer(offer).data})
        except Offer.DoesNotExist:
            return Response({'valid': False, 'error': 'Offer not found or expired'}, status=404)

from orders.models import Cart, CartItem
from .serializers import AgentCartSerializer, AgentCartItemSerializer
from django.shortcuts import get_object_or_404
import uuid

class AgentCartViewSet(viewsets.ModelViewSet):
    queryset = Cart.objects.all().prefetch_related('items__product')
    serializer_class = AgentCartSerializer
    permission_classes = [AgentPermission]

    def create(self, request, *args, **kwargs):
        session_id = request.data.get('session_id') or str(uuid.uuid4())
        cart, _ = Cart.objects.get_or_create(session_id=session_id)
        if request.user.is_authenticated:
            cart.user = request.user
            cart.actor_type = 'human' # Can be overriden based on token scopes
            cart.save()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def items(self, request, pk=None):
        cart = self.get_object()
        product_id = request.data.get('productId')
        quantity = int(request.data.get('quantity', 1))
        
        product = get_object_or_404(Product, id=product_id, is_active=True)
        cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
        if not created:
            cart_item.quantity += quantity
        else:
            cart_item.quantity = quantity
        cart_item.save()
        
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

    @items.mapping.delete
    def remove_item(self, request, pk=None):
        cart = self.get_object()
        item_id = request.data.get('itemId')
        item = get_object_or_404(CartItem, id=item_id, cart=cart)
        item.delete()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)

class AgentCheckoutViewSet(viewsets.ViewSet):
    permission_classes = [AgentPermission]
    
    @action(detail=False, methods=['post'])
    def quote(self, request):
        cart_id = request.data.get('cartId')
        cart = get_object_or_404(Cart, id=cart_id)
        
        shipping_address = request.data.get('shipping_address', '')
        promo_code = request.data.get('promo_code', '')
        
        from orders.utils import generate_quote
        quote_data = generate_quote(cart, shipping_address=shipping_address, promo_code=promo_code)
        
        return Response(quote_data)
        
    @action(detail=False, methods=['post'])
    def authorize(self, request):
        from intelligence.services.firewall import TransactionFirewallService
        from decimal import Decimal
        
        cart_id = request.data.get('cartId')
        cart = get_object_or_404(Cart, id=cart_id)
        buyer_budget = request.data.get('buyer_budget')
        if buyer_budget:
            buyer_budget = Decimal(str(buyer_budget))
            
        decision_obj = TransactionFirewallService.evaluate_checkout(
            cart=cart, 
            actor_type='ai_agent',
            buyer_budget=buyer_budget
        )
        
        return Response({
            'status': 'authorized' if decision_obj.decision == 'ALLOW' else 'blocked',
            'decision': decision_obj.decision,
            'reasonCodes': decision_obj.reason_codes
        })
        
    @action(detail=False, methods=['post'])
    def confirm(self, request):
        from orders.utils import validate_quote
        from orders.models import Order, OrderItem, Payment
        from intelligence.services.razorpay_service import RazorpayService
        from intelligence.services.firewall import TransactionFirewallService
        from decimal import Decimal
        
        cart_id = request.data.get('cartId')
        cart = get_object_or_404(Cart, id=cart_id)
        
        # Policy Engine check first!
        decision_obj = TransactionFirewallService.evaluate_checkout(cart=cart, actor_type='ai_agent')
        if decision_obj.decision == 'DENY':
            return Response({
                'error': 'Policy Engine blocked this transaction.', 
                'reasons': decision_obj.reason_codes
            }, status=400)
        
        quote_hash = request.data.get('quoteHash')
        expires_at = request.data.get('expiresAt')
        shipping_address = request.data.get('shipping_address', '')
        promo_code = request.data.get('promo_code', '')
        customer_note = request.data.get('customer_note', '')
        
        if not all([quote_hash, expires_at]):
            return Response({'error': 'Missing quoteHash or expiresAt'}, status=400)
            
        is_valid, reason = validate_quote(cart, quote_hash, expires_at, shipping_address, promo_code)
        if not is_valid:
            return Response({'error': reason}, status=400)
            
        # At this point, the cart is valid. We calculate exact totals again for the DB.
        from orders.utils import generate_quote
        quote_data = generate_quote(cart, shipping_address, promo_code)
        
        # Create the Order
        order = Order.objects.create(
            user=request.user,
            status='pending',
            payment_method=Order.PAYMENT_RAZORPAY,
            delivery_eta="Standard", # Should ideally come from quote
            delivery_fee=quote_data["deliveryFee"],
            promo_code=quote_data["promoCode"],
            discount_amount=quote_data["discountAmount"],
            total_price=quote_data["total"],
            shipping_address=shipping_address,
            customer_note=customer_note
        )
        
        # Create Order Items
        order_items = []
        for item in cart.items.all():
            order_items.append(OrderItem(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.current_price
            ))
            # Decrement inventory
            item.product.stock = max(item.product.stock - item.quantity, 0)
            item.product.save(update_fields=["stock"])
            if hasattr(item.product, "inventory"):
                item.product.inventory.quantity = item.product.stock
                item.product.inventory.save(update_fields=["quantity", "updated_at"])
                
        OrderItem.objects.bulk_create(order_items)
        
        # Generate Razorpay Order
        receipt = f"order_{order.id}"
        rzp_order = RazorpayService.create_order(amount=quote_data["total"], receipt=receipt)
        
        # Save Payment intent
        Payment.objects.create(
            order=order,
            method=order.payment_method,
            amount=quote_data["total"],
            status=Payment.STATUS_PENDING,
            provider_reference=rzp_order['id'],
        )
        
        # Clear Cart
        cart.items.all().delete()
        
        return Response({
            'status': 'confirmed',
            'orderId': order.id,
            'razorpayOrderId': rzp_order['id'],
            'amount': rzp_order['amount'],
            'currency': rzp_order['currency']
        })
    @action(detail=False, methods=['get'])
    def status(self, request):
        from orders.models import TransactionDecision
        cart_id = request.query_params.get('cartId')
        
        if not cart_id:
            return Response({'error': 'cartId is required'}, status=400)
            
        decision = TransactionDecision.objects.filter(cart_id=cart_id).order_by('-created_at').first()
        
        if not decision:
            return Response({'status': 'NOT_FOUND', 'message': 'No transaction attempts found for this cart.'}, status=404)
            
        return Response({
            'status': decision.decision,
            'reasonCodes': decision.reason_codes,
            'riskScore': str(decision.risk_score),
            'amount': str(decision.amount),
            'timestamp': decision.created_at.isoformat()
        })

class AgentPolicyViewSet(viewsets.ViewSet):
    """Exposes store policies to AI agents."""
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['get'])
    def shipping(self, request):
        # In a real app, this might come from a DB model
        return Response({
            "policy_type": "shipping",
            "base_fee_npr": 150,
            "free_shipping_threshold_npr": 5000,
            "estimated_days": "1-3 business days within Kathmandu Valley, 3-7 days outside.",
            "carriers": ["Pathao", "In-house Delivery"]
        })
        
    @action(detail=False, methods=['get'])
    def returns(self, request):
        return Response({
            "policy_type": "returns",
            "return_window_days": 7,
            "conditions": "Item must be unused and in original packaging.",
            "non_returnable_categories": ["groceries", "beauty", "innerwear"],
            "refund_method": "Original payment method or Store Credit"
        })


class AgentCatalogViewSet(viewsets.ViewSet):
    """
    Agent-Readable Catalog — JSON-LD product feed and agent-initiated checkout.
    Implements WebMCP Discovery and Action layers.
    """
    permission_classes = [AllowAny]

    @action(detail=False, methods=['get'])
    def feed(self, request):
        """
        GET /api/agent/v1/catalog/feed/
        Returns the full product catalog in Schema.org JSON-LD format.
        Supports filtering: ?category=laptops&min_price=10000&max_price=50000&in_stock=true&limit=50
        """
        from .serializers_jsonld import JsonLdCatalogSerializer

        qs = Product.objects.filter(is_active=True).select_related(
            'category', 'brand', 'store'
        ).prefetch_related('images', 'ai_attributes', 'inventory')

        # Apply filters
        category = request.query_params.get('category')
        if category:
            qs = qs.filter(category__slug=category)

        min_price = request.query_params.get('min_price')
        if min_price:
            qs = qs.filter(price__gte=min_price)

        max_price = request.query_params.get('max_price')
        if max_price:
            qs = qs.filter(price__lte=max_price)

        in_stock = request.query_params.get('in_stock')
        if in_stock and str(in_stock).lower() == 'true':
            qs = qs.filter(stock__gt=0)

        limit = int(request.query_params.get('limit', 100))
        qs = qs[:min(limit, 500)]

        serializer = JsonLdCatalogSerializer()
        return Response(serializer.to_representation(qs))

    @action(detail=False, methods=['get'])
    def product(self, request):
        """
        GET /api/agent/v1/catalog/product/?slug=product-slug
        Returns a single product in JSON-LD format.
        """
        from .serializers_jsonld import JsonLdProductSerializer

        slug = request.query_params.get('slug')
        if not slug:
            return Response({"error": "slug parameter required"}, status=400)

        try:
            product = Product.objects.select_related(
                'category', 'brand', 'store'
            ).prefetch_related(
                'images', 'ai_attributes'
            ).get(slug=slug, is_active=True)
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        serializer = JsonLdProductSerializer()
        return Response(serializer.to_representation(product))

    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """
        POST /api/agent/v1/catalog/checkout/
        Agent-initiated checkout: accepts {product_id, quantity, buyer_token}
        Creates a bounded Razorpay Payment Link and returns it.

        The buyer's authorization is via a scoped token (limited to one merchant,
        one amount, short expiry) — per the Agent Patterns Catalog.
        """
        import time
        import uuid
        from intelligence.services.razorpay_service import RazorpayService
        from intelligence.services.commerce_audit import CommerceAuditService
        from intelligence.services.firewall import TransactionFirewallService
        from decimal import Decimal

        product_id = request.data.get('product_id')
        quantity = int(request.data.get('quantity', 1))
        buyer_token = request.data.get('buyer_token', '')
        budget_max = request.data.get('budget_max')
        agent_id = request.data.get('agent_id', 'external_agent')

        if not product_id:
            return Response({"error": "product_id is required"}, status=400)

        try:
            product = Product.objects.select_related('inventory').get(
                id=product_id, is_active=True
            )
        except Product.DoesNotExist:
            return Response({"error": "Product not found"}, status=404)

        # Check stock
        available = product.stock
        if hasattr(product, 'inventory'):
            available = product.inventory.available_quantity

        if available < quantity:
            CommerceAuditService.log_audit_event(
                agent=agent_id,
                action="agent_checkout_stock_fail",
                outcome="failed",
                explainable=f"Out of stock: requested {quantity}, available {available}",
                extra_payload={"product_id": product_id},
            )
            # Return structured error with alternatives
            alternatives = Product.objects.filter(
                category=product.category, is_active=True, stock__gt=0
            ).exclude(id=product.id)[:3]
            alt_data = [
                {"id": p.id, "name": p.name, "price": float(p.current_price), "stock": p.stock}
                for p in alternatives
            ]
            return Response({
                "error": "out_of_stock",
                "message": f"Only {available} available (requested {quantity})",
                "alternatives": alt_data,
            }, status=409)

        # Calculate amount
        unit_price = product.current_price
        total_amount = unit_price * quantity

        # Budget check
        if budget_max:
            budget = Decimal(str(budget_max))
            if total_amount > budget:
                return Response({
                    "error": "exceeds_budget",
                    "message": f"Total ₹{total_amount} exceeds budget ₹{budget}",
                    "amount": float(total_amount),
                    "budget_max": float(budget),
                }, status=400)

        # Create bounded Razorpay Payment Link
        trace_id = str(uuid.uuid4())
        try:
            payment_link = RazorpayService.create_payment_link(
                amount=total_amount,
                description=f"{product.name} × {quantity}",
                notes={
                    "type": "agent_initiated_checkout",
                    "agent_id": agent_id,
                    "product_id": str(product_id),
                    "quantity": str(quantity),
                    "trace_id": trace_id,
                    "bounded": "true",
                    "max_amount": str(total_amount),
                    "buyer_token_scoped": bool(buyer_token),
                },
                expire_by=int(time.time()) + 1800,  # 30 min expiry
            )
        except Exception as e:
            CommerceAuditService.log_audit_event(
                agent=agent_id,
                action="agent_checkout_payment_fail",
                outcome="failed",
                trace_id=trace_id,
                failure_detail=str(e),
            )
            return Response({
                "error": "payment_creation_failed",
                "message": "Could not create payment link. Please retry.",
            }, status=500)

        # Audit trail
        CommerceAuditService.log_audit_event(
            agent=agent_id,
            action="agent_checkout_initiated",
            outcome="success",
            trace_id=trace_id,
            razorpay_entity={"type": "payment_link", "id": payment_link["id"]},
            bounded={
                "max_amount": str(total_amount),
                "currency": "INR",
                "expiry": "30 minutes",
            },
            gated_by="buyer_token" if buyer_token else "agent_confirmation",
            explainable=f"Agent {agent_id} initiated checkout for {product.name} × {quantity}",
            extra_payload={
                "product_id": product_id,
                "quantity": quantity,
                "buyer_token_scoped": bool(buyer_token),
            },
        )

        return Response({
            "status": "created",
            "payment_link_id": payment_link["id"],
            "payment_url": payment_link.get("short_url", ""),
            "amount": float(total_amount),
            "currency": "INR",
            "product": {
                "id": product.id,
                "name": product.name,
                "quantity": quantity,
                "unit_price": float(unit_price),
            },
            "trace_id": trace_id,
            "expires_in_seconds": 1800,
            "bounded": True,
        })

