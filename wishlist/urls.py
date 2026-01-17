
from django.urls import path
from .views import (
    WishlistAPIView,
    AddToWishlistAPIView,
    RemoveFromWishlistAPIView,
)

urlpatterns = [
    path('', WishlistAPIView.as_view()),
    path('add/', AddToWishlistAPIView.as_view()),
    path('remove/<int:product_id>/', RemoveFromWishlistAPIView.as_view()),
]
