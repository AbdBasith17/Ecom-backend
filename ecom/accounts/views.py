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

from drf_spectacular.utils import extend_schema, OpenApiExample

from .models import User, EmailOTP
from .serializers import RegisterSerializer, UserAdminSerializer
from .customtoken import CustomRefreshToken
from .authentication import CookieJWTAuthentication
from .otp import send_otp_email

User = get_user_model()

# --- COOKIE HELPER FOR PRODUCTION (VERCEL <-> EC2) ---
def set_jwt_cookies(response, refresh):
    """
    Standardized cookie setting for cross-site production.
    Samesite='None' and Secure=True are REQUIRED for Vercel to work with EC2.
    """
    cookie_settings = {
        "httponly": True,
        "samesite": "None",  # Required for cross-site cookies
        "secure": True,      # Required when samesite is None (Needs HTTPS)
    }
    
    # Set Access Token Cookie
    response.set_cookie(
        "access",
        str(refresh.access_token),
        max_age=60 * 15, # 15 Minutes
        **cookie_settings
    )
    
    # Set Refresh Token Cookie
    response.set_cookie(
        "refresh",
        str(refresh),
        max_age=60 * 60 * 24 * 7, # 7 Days
        **cookie_settings
    )
    return response

# --- AUTHENTICATION VIEWS ---

class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').lower().strip()
        
        existing_user = User.objects.filter(email=email).first()
        if existing_user:
            if existing_user.is_active:
                return Response({"error": "Email already exists"}, status=status.HTTP_400_BAD_REQUEST)
            else:
                existing_user.delete()

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                user = serializer.save()
                otp = str(random.randint(100000, 999999))
                expires = timezone.now() + timedelta(minutes=10)
                EmailOTP.objects.create(user=user, otp=otp, expires_at=expires)
                send_otp_email(user.email, otp)

            return Response(
                {"message": "OTP sent to email", "email": user.email},
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"error": f"Registration failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VerifyOTP(APIView): 
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email", "").lower().strip()
        otp = request.data.get("otp", "").strip()

        if not email or not otp:
            return Response({"error": "Email and OTP required"}, status=400)
 
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "User not found"}, status=404)

        otp_obj = EmailOTP.objects.filter(user=user).last()
        if not otp_obj:
            return Response({"error": "No OTP generated for this account"}, status=400)
 
        if otp_obj.is_expired():
            return Response({"error": "OTP expired. Please request a new one."}, status=400)
 
        if otp_obj.otp != otp:
            return Response({"error": "Invalid OTP"}, status=400)

        user.is_active = True
        user.save()
        EmailOTP.objects.filter(user=user).delete()

        return Response({"message": "Email verified successfully!"}, status=200)

@extend_schema(
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "password": {"type": "string"},
            },
            "required": ["email", "password"],
        }
    },
    responses={200: None},
)
class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response({"error": "Email and password required"}, status=400)

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({"error": "Invalid credentials"}, status=401)

        if not user.is_active:
            return Response({"error": "Please verify your email"}, status=403)

        refresh = CustomRefreshToken.for_user(user)
        response = Response({
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "role": user.role,
            }
        }, status=200)

        return set_jwt_cookies(response, refresh)
    
class GoogleSignInView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token is required"}, status=400)

        try:
            idinfo = id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_CLIENT_ID
            )
            email = idinfo['email'].lower().strip()
            full_name = idinfo.get('name', '')
            
            user, created = User.objects.get_or_create(email=email)
            if created or not user.name:
                user.name = full_name
            
            user.is_active = True 
            user.save()

            refresh = CustomRefreshToken.for_user(user)
            response = Response({
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                }
            }, status=200)

            return set_jwt_cookies(response, refresh)

        except Exception as e:
            return Response({"error": str(e)}, status=500)

class Logout(APIView):
    permission_classes = [AllowAny] 

    def post(self, request):
        response = Response({"message": "Logged out successfully"}, status=200)
        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            try:
                token = CustomRefreshToken(refresh_token)
                token.blacklist() 
            except Exception:
                pass  

        # Delete cookies with same production settings
        cookie_params = {"samesite": "None", "secure": True}
        response.delete_cookie("access", **cookie_params)
        response.delete_cookie("refresh", **cookie_params)

        return response

class Me(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "is_active": user.is_active,
        })

class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh")
        if not refresh_token:
            return Response({"error": "No refresh token"}, status=401)
        
        data = request.data.copy()
        data["refresh"] = refresh_token
        
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except (InvalidToken, TokenError):
            return Response({"error": "Invalid refresh token"}, status=401)

        response = Response(serializer.validated_data, status=200)
        
        # Extract token object to reuse helper
        new_refresh_str = serializer.validated_data.get("refresh", refresh_token)
        refresh_obj = RefreshToken(new_refresh_str)

        set_jwt_cookies(response, refresh_obj)
        
        # Hide tokens from response body
        if "refresh" in response.data: del response.data["refresh"]
        if "access" in response.data: del response.data["access"]
        
        return response

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