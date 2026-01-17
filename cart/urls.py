from django.urls import path
from .views import (
    CartAPIView,
    AddToCartAPIView,
    UpdateCartAPIView,
    RemoveFromCartAPIView,
)

urlpatterns = [
    path("", CartAPIView.as_view()),
    path("add/", AddToCartAPIView.as_view()),
    path("update/<int:product_id>/", UpdateCartAPIView.as_view()),
    path("remove/<int:product_id>/", RemoveFromCartAPIView.as_view()),
]
