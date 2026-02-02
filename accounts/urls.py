from django.urls import path
from .views import (
    Register,
    VerifyOTP, 
    Login, 
    Logout,
    Me,
    CookieTokenRefreshView,
    UserListView,
    UserStatusUpdateView,
    ForgotPasswordConfirm,
    ForgotPasswordRequest
)



urlpatterns = [
    path("register/", Register.as_view()),
    path("verify-otp/", VerifyOTP.as_view()),
    path("login/", Login.as_view()),
    path("logout/", Logout.as_view()),
    path("me/", Me.as_view()),
    path("token/refresh/", CookieTokenRefreshView.as_view()),


    path('admin/users/', UserListView.as_view(), name='user-list'),
    path('admin/users/update/<int:pk>/', UserStatusUpdateView.as_view(), name='user-update'),

    path('forgot-password-request/', ForgotPasswordRequest.as_view(), name='forgot-password-request'),
    path('forgot-password-confirm/', ForgotPasswordConfirm.as_view(), name='forgot-password-confirm'),
]
