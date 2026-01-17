
from rest_framework import serializers
from .models import Product, Category, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    category = serializers.StringRelatedField() 

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'category', 'price', 'stock', 'sold', 'ml', 'images', 'is_active', 'created_at']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent']





class ProductMiniSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
      
        fields = ('id', 'title', 'price', 'image', 'images', 'ml') 

    def get_image(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url 
        return None