from django.urls import path
from .views import CreateRazorpayOrderAPIView, VerifyPaymentAPIView #razorpay_webhook



urlpatterns = [
    
    path("create-razorpay-order/", CreateRazorpayOrderAPIView.as_view(), name="create-razorpay-order"),

    
    path("verify/", VerifyPaymentAPIView.as_view(), name="verify-payment"),

    
    # path("webhook/", razorpay_webhook, name="razorpay-webhook"),
]
