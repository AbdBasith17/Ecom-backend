
from rest_framework import generics
from .models import Product, Category
from .serializers import ProductSerializer, CategorySerializer
from .pagination import ProductPagination
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from rest_framework.permissions import IsAdminUser,AllowAny

class ProductListView(generics.ListAPIView):
    permission_classes = [AllowAny]
    queryset = Product.objects.filter(is_active=True)
    serializer_class = ProductSerializer
    pagination_class = ProductPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    filterset_fields = ['category']
    ordering_fields = ['price', 'created_at']
    search_fields = ['title', 'description']

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
