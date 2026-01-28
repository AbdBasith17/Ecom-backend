from django.urls import path
from .views import PlaceOrderAPIView, CancelOrderAPIView, CheckoutSummaryAPIView

urlpatterns = [

    path("create/", PlaceOrderAPIView.as_view()),
    path("checkout/summary/", CheckoutSummaryAPIView.as_view()),
    path("cancel/<int:pk>/", CancelOrderAPIView.as_view()),
]