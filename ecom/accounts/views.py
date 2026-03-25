import random
from datetime import timedelta
from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status, generics, permissions
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from .models import User, EmailOTP
from .serializers import RegisterSerializer, UserAdminSerializer
from .customtoken import CustomRefreshToken
from .authentication import CookieJWTAuthentication
from .otp import send_otp_email

User = get_user_model()

# --- UNIFIED COOKIE HELPER ---
def set_jwt_cookies(response, refresh):
    cookie_settings = {
        "httponly": True,
        "samesite": "None", # Required for Vercel -> EC2
        "secure": True,     # Required for SameSite=None
        "path": "/",
    }
    response.set_cookie("access", str(refresh.access_token), max_age=60*15, **cookie_settings)
    response.set_cookie("refresh", str(refresh), max_age=60*60*24*7, **cookie_settings)
    return response

# --- VIEWS ---

class Login(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)
        if not user.is_active:
            return Response({"error": "Please verify email"}, status=403)
        
        refresh = CustomRefreshToken.for_user(user)
        response = Response({
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
        }, status=200)
        return set_jwt_cookies(response, refresh)

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"error": "No refresh token"}, status=401)
        
        serializer = self.get_serializer(data={"refresh": refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
            new_refresh_str = serializer.validated_data.get("refresh") or refresh_token
            refresh_obj = RefreshToken(new_refresh_str)
            response = Response({"message": "Token refreshed"}, status=200)
            return set_jwt_cookies(response, refresh_obj)
        except (InvalidToken, TokenError):
            return Response({"error": "Invalid token"}, status=401)

class Logout(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        response = Response({"message": "Logged out"}, status=200)
        refresh_token = request.COOKIES.get("refresh")
        if refresh_token:
            try:
                CustomRefreshToken(refresh_token).blacklist()
            except: pass
        
        params = {"samesite": "None", "secure": True, "path": "/"}
        response.delete_cookie("access", **params)
        response.delete_cookie("refresh", **params)
        return response

class Me(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response({
            "id": request.user.id,
            "name": request.user.name,
            "email": request.user.email,
            "role": request.user.role,
        })

class GoogleSignInView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        token = request.data.get("token")
        try:
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
            user, _ = User.objects.get_or_create(email=idinfo['email'].lower().strip())
            user.name = idinfo.get('name', user.name)
            user.is_active = True
            user.save()
            return set_jwt_cookies(Response({"user": {"id": user.id, "name": user.name}}, status=200), CustomRefreshToken.for_user(user))
        except Exception as e:
            return Response({"error": str(e)}, status=500)



# --- ADMIN VIEWS ---

class UserListView(generics.ListAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all().order_by('-id')
    serializer_class = UserAdminSerializer 

class UserStatusUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAdminUser]
    queryset = User.objects.all()
    serializer_class = UserAdminSerializer
    
    def patch(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('is_active')
        if new_status is not None:
            instance.is_active = new_status
            instance.save()
            return Response({"message": "Status updated successfully"}, status=200)
        return Response({"error": "is_active field required"}, status=400)

# --- PASSWORD FORGOT VIEWS ---

class ForgotPasswordRequest(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        user = User.objects.filter(email=email).first()
        
        if user:
            EmailOTP.objects.filter(user=user).delete()
            otp = str(random.randint(100000, 999999))
            expires = timezone.now() + timedelta(minutes=10)
            EmailOTP.objects.create(user=user, otp=otp, expires_at=expires)
            send_otp_email(user.email, otp)
        
        return Response({"message": "If an account exists, an OTP has been sent."}, status=200)

class ForgotPasswordConfirm(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").strip()
        otp = request.data.get("otp", "").strip()
        new_password = request.data.get("new_password", "")

        if len(new_password) < 8:
            return Response({"error": "Password must be at least 8 characters."}, status=400)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Invalid request."}, status=400)

        otp_obj = EmailOTP.objects.filter(user=user, otp=otp).last()
        if not otp_obj or otp_obj.is_expired():
            return Response({"error": "Invalid or expired OTP."}, status=400)

        user.set_password(new_password)
        user.save()
        otp_obj.delete()
        
        return Response({"message": "Password reset successfully."}, status=200)