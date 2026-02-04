from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .services import (
    get_or_create_cart,
    add_to_cart,
    remove_from_cart,
    update_cart_item
)
from .serializers import CartItemSerializer


class CartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        
        serializer = CartItemSerializer(
            cart.items.all(), 
            many=True,
            context={'request': request} 
        )
        return Response(serializer.data)

class AddToCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = int(request.data.get("quantity", 1))

        if not product_id:
            return Response(
                {"detail": "product_id required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        item = add_to_cart(request.user, product_id, quantity)
        return Response(
            CartItemSerializer(item).data,
            status=status.HTTP_201_CREATED
        )


class UpdateCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, product_id):
        try:
            quantity = int(request.data.get("quantity", 1))
        except (ValueError, TypeError):
            return Response({"detail": "Invalid quantity"}, status=400)

        item = update_cart_item(request.user, product_id, quantity)

       
        if item is None:
            return Response(
                {"detail": "Item removed or not found"}, 
                status=status.HTTP_204_NO_CONTENT
            )

       
        serializer = CartItemSerializer(item, context={'request': request})
        return Response(serializer.data)
    

class RemoveFromCartAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, product_id):
        remove_from_cart(request.user, product_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
