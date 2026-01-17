from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import WishlistItems
from .serializers import WishlistItemSerializer
from .services import get_or_create_wishlist
from products.models import Product


class AddToWishlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")

    
        if not product_id:
            return Response(
                {'detail': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        
        product = Product.objects.filter(id=product_id, is_active=True).first()

        if not product:
            return Response(
                {'detail': 'product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
     
        wishlist = get_or_create_wishlist(request.user)

      
        item, created = WishlistItems.objects.get_or_create(
            wishlist=wishlist,
            product=product
        )

       
        if not created:
            return Response(
                {'detail': 'Product already in wishlist'},
                status=status.HTTP_200_OK
            )

        serializer = WishlistItemSerializer(item, context={'request': request})
        
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED
        )

class RemoveFromWishlistAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def delete(self,request ,product_id):
        wishlist= get_or_create_wishlist(request.user)

        deleted, _ = WishlistItems.objects.filter(
            wishlist = wishlist,
            product_id = product_id
        ).delete()

        if not deleted:
            return Response(
                {'detail': 'Product not in wishlist'},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(
            {'detail': 'Removed from wishlist'},
            status=status.HTTP_204_NO_CONTENT
        )
             

class WishlistAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        wishlist = get_or_create_wishlist(request.user)
        
        serializer = WishlistItemSerializer(
            wishlist.items.all(),
            many=True,
            context={'request': request} 
        )
        return Response(serializer.data)
