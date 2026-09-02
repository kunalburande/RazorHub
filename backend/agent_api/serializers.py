from rest_framework import serializers
from products.models import Product, Inventory
from intelligence.models import ProductRelationship, Offer

class AgentPriceSerializer(serializers.Serializer):
    listPrice = serializers.DecimalField(max_digits=12, decimal_places=2, source='price')
    salePrice = serializers.DecimalField(max_digits=12, decimal_places=2, source='current_price')
    discount = serializers.SerializerMethodField()
    currency = serializers.CharField(default='INR')
    
    def get_discount(self, obj):
        if obj.discount_price and obj.discount_price < obj.price:
            return obj.price - obj.discount_price
        return 0.0

class AgentAvailabilitySerializer(serializers.ModelSerializer):
    available = serializers.BooleanField(source='product.is_active') # basic availability
    quantityAvailable = serializers.IntegerField(source='quantity')
    estimatedDelivery = serializers.SerializerMethodField()
    
    class Meta:
        model = Inventory
        fields = ['available', 'quantityAvailable', 'estimatedDelivery']
        
    def get_estimatedDelivery(self, obj):
        return obj.product.delivery_time_estimate

class AgentRelationshipSerializer(serializers.ModelSerializer):
    targetProductId = serializers.IntegerField(source='target_product_id')
    relationshipType = serializers.CharField(source='relationship_type')
    
    class Meta:
        model = ProductRelationship
        fields = ['targetProductId', 'relationshipType', 'confidence']

class AgentOfferSerializer(serializers.ModelSerializer):
    offerId = serializers.CharField(source='offer_id')
    offerType = serializers.CharField(source='offer_type')
    productIds = serializers.SerializerMethodField()
    expiresAt = serializers.DateTimeField(source='expires_at')
    
    class Meta:
        model = Offer
        fields = ['offerId', 'offerType', 'productIds', 'price', 'original_price', 'discount', 'confidence', 'expiresAt']
        
    def get_productIds(self, obj):
        return [p.id for p in obj.products.all()]

class AgentProductSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source='id')
    price = AgentPriceSerializer(source='*')
    availability = serializers.SerializerMethodField()
    relationships = serializers.SerializerMethodField()
    offers = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['productId', 'name', 'slug', 'description', 'price', 'availability', 'relationships', 'offers']
        
    def get_availability(self, obj):
        if hasattr(obj, 'inventory'):
            return AgentAvailabilitySerializer(obj.inventory).data
        return None
        
    def get_relationships(self, obj):
        relationships = ProductRelationship.objects.filter(source_product=obj)
        return AgentRelationshipSerializer(relationships, many=True).data
        
    def get_offers(self, obj):
        offers = Offer.objects.filter(products=obj, status='active')
        return AgentOfferSerializer(offers, many=True).data

from orders.models import Cart, CartItem

class AgentCartItemSerializer(serializers.ModelSerializer):
    productId = serializers.IntegerField(source='product_id')
    price = serializers.DecimalField(source='product.current_price', max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = ['id', 'productId', 'quantity', 'price', 'added_at']

class AgentCartSerializer(serializers.ModelSerializer):
    items = AgentCartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'session_id', 'items', 'total', 'created_at', 'updated_at']
        
    def get_total(self, obj):
        total = sum(item.product.current_price * item.quantity for item in obj.items.all())
        return total

