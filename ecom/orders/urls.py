from django.urls import path
from .views import (
    PlaceOrderAPIView,
    CancelOrderAPIView, 
    CheckoutSummaryAPIView,
    UserOrderListAPIView,
    AdminOrderListAPIView,
    AdminUpdateOrderStatusAPIView,
    )


urlpatterns = [

    path("create/", PlaceOrderAPIView.as_view()),
    path("checkout/summary/", CheckoutSummaryAPIView.as_view()),
    path("cancel/<int:pk>/", CancelOrderAPIView.as_view()),
    path("my-orders/", UserOrderListAPIView.as_view()),
    path("admin/list/", AdminOrderListAPIView.as_view()),
    path("admin/update-status/<int:pk>/", AdminUpdateOrderStatusAPIView.as_view()),
]