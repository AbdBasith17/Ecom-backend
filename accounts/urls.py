from django.urls import path
from .views import Register, VerifyOTP, Login, Logout, Me, CookieTokenRefreshView

urlpatterns = [
    path("register/", Register.as_view()),
    path("verify-otp/", VerifyOTP.as_view()),
    path("login/", Login.as_view()),
    path("logout/", Logout.as_view()),
    path("me/", Me.as_view()),
    path("token/refresh/", CookieTokenRefreshView.as_view()),
]
