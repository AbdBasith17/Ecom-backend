from django.urls import path
from accounts.views import RegisterView,VerifyOTPView,LoginView,CustomTokenObtainView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", VerifyOTPView.as_view(), name="verify-otp"),
    # path("login/", LoginView.as_view(), name="login"),
    path("login/", CustomTokenObtainView.as_view(), name="custom_login"),
]
