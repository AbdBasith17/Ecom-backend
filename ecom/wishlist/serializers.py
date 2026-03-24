from rest_framework import serializers
from .models import WishlistItems
from products.serializers import ProductMiniSerializer


class  WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductMiniSerializer(read_only = True)

    class Meta:
        model = WishlistItems
        fields = ['id','product','added_at']


