
from rest_framework import generics,permissions
from .models import Product, Category ,ProductImage
from .serializers import ProductSerializer, CategorySerializer
from .pagination import ProductPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from rest_framework.permissions import IsAdminUser,AllowAny

from rest_framework import filters

class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    
    # COMBINE ALL FILTERS HERE IN ONE LIST
    filter_backends = [
        DjangoFilterBackend, 
        OrderingFilter, 
        SearchFilter
    ]

    filterset_fields = ['category']
    ordering_fields = ['price', 'created_at', 'title']  
    search_fields = ['title', 'description']
    ordering = ['-created_at']

class ProductDetailView(generics.RetrieveAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer

class BestSellerListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    serializer_class = ProductSerializer
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).order_by('-sold')[:4]    



class CategoryListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer




class AdminProductListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = Product.objects.all().order_by('-id') 
    serializer_class = ProductSerializer
   
    filter_backends = [SearchFilter]
    search_fields = ['title']    


class AdminProductCreateView(generics.CreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]


class AdminProductUpdateView(generics.UpdateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAdminUser]


class AdminProductDeleteView(generics.DestroyAPIView):
    queryset = Product.objects.all()
    permission_classes = [IsAdminUser]


class ProductImageDeleteView(generics.DestroyAPIView):
    queryset = ProductImage.objects.all()
    permission_classes = [permissions.IsAdminUser]