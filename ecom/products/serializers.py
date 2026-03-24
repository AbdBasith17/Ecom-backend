from rest_framework import serializers
from .models import Product, Category, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent']

class ProductSerializer(serializers.ModelSerializer):
  
    images = ProductImageSerializer(many=True, read_only=True)
    
   
    category = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        required=False, 
        allow_null=True
    )
    

    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = [
            'id', 'title', 'description', 'category', 'category_name', 
            'price', 'stock', 'sold', 'ml', 'images', 'is_active', 'created_at'
        ]

    def create(self, validated_data):
        """
        Handles Product creation and multiple local image uploads.
        """
        
        images_data = self.context.get('view').request.FILES.getlist('uploaded_images')
        
        product = Product.objects.create(**validated_data)
        
        for image_data in images_data:
            ProductImage.objects.create(product=product, image=image_data)
            
        return product

    def update(self, instance, validated_data):
        """
        Handles Product updates and adds new local images if provided.
        """
        images_data = self.context.get('view').request.FILES.getlist('uploaded_images')

       
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        
        if images_data:
           
            
            for image_data in images_data:
                ProductImage.objects.create(product=instance, image=image_data)

        return instance

class ProductMiniSerializer(serializers.ModelSerializer):
    """
    Optimized serializer for shop listing pages.
    """
    image = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'title', 'price', 'image', 'ml')

    def get_image(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.image:
            request = self.context.get('request')
            if request is not None:
                return request.build_absolute_uri(first_image.image.url)
            return first_image.image.url
        return None