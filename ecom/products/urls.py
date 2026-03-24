from django.urls import path
from .views import (
    ProductListView,
    ProductDetailView,
    CategoryListView,
    AdminProductCreateView,
    AdminProductUpdateView,
    AdminProductDeleteView,
    BestSellerListView,
    AdminProductListView,
    ProductImageDeleteView,
    
)

urlpatterns = [
    
    path('products/', ProductListView.as_view(), name='product-list'),
    path('products/<int:pk>/', ProductDetailView.as_view(), name='product-detail'),
    path('categories/', CategoryListView.as_view(), name='category-list'),

    path('products/best-sellers/', BestSellerListView.as_view()),

    path('admin/products/list/', AdminProductListView.as_view()),
    path('admin/products/create/', AdminProductCreateView.as_view()),
    path('admin/products/<int:pk>/update/', AdminProductUpdateView.as_view()),
    path('admin/products/<int:pk>/delete/', AdminProductDeleteView.as_view()),

    path('admin/products/image/<int:pk>/delete/', ProductImageDeleteView.as_view()),

   
]
