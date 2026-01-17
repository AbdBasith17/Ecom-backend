from rest_framework import serializers
from .models import CartItem
from products.serializers import ProductMiniSerializer

class CartItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only = True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ("id", "product", "quantity", "subtotal")

    def get_subtotal(self, obj):
        return obj.product.price * obj.quantity
