from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from products.models import Product
from products.serializers import ProductListSerializer
from .models import Wishlist

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_wishlist(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    products = wishlist.products.all().select_related('category', 'brand', 'store')
    serializer = ProductListSerializer(products, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def toggle_wishlist(request):
    product_ref = request.data.get('product') or request.data.get('slug') or request.data.get('id')
    if not product_ref:
        return Response({'detail': 'Product identifier (id or slug) is required.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if str(product_ref).isdigit():
        product = get_object_or_404(Product, id=int(product_ref))
    else:
        product = get_object_or_404(Product, slug=str(product_ref))
        
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    
    if wishlist.products.filter(id=product.id).exists():
        wishlist.products.remove(product)
        is_in_wishlist = False
    else:
        wishlist.products.add(product)
        is_in_wishlist = True
        
    return Response({
        'status': 'success',
        'is_in_wishlist': is_in_wishlist,
        'product_id': product.id,
        'count': wishlist.products.count()
    })

@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def remove_from_wishlist(request, product_id):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    wishlist.products.remove(product_id)
    return Response({'status': 'removed', 'count': wishlist.products.count()})
