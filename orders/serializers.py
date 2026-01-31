from rest_framework import serializers
from .models import Order, OrderItem

# orders/serializers.py
class OrderItemSerializer(serializers.ModelSerializer):
    # Changed to .title based on your previous product sorting logic
    product_name = serializers.ReadOnlyField(source='product.title') 
    
    class Meta:
        model = OrderItem
        fields = ["product_name", "quantity", "price"]

class OrderSerializer(serializers.ModelSerializer):
    # These now match your Address model exactly
    shipping_address = serializers.ReadOnlyField(source='address.address_line')
    address_name = serializers.ReadOnlyField(source='address.full_name')
    phone = serializers.ReadOnlyField(source='address.phone')
    city = serializers.ReadOnlyField(source='address.city')
    pincode = serializers.ReadOnlyField(source='address.pincode')
    
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            "id", "user", "address_name", "phone", "shipping_address", 
            "city", "pincode", "total_amount", "payment_method", 
            "status", "created_at", "items"
        ]