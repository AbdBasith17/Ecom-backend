from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from rest_framework import status
import random
from .serializers import RegisterSerializer,UserAdminSerializer
from .models import User, EmailOTP
from .customtoken import CustomRefreshToken
from .authentication import CookieJWTAuthentication
from .otp import send_otp_email
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from django.utils import timezone
from datetime import timedelta





class Register(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp = str(random.randint(100000, 999999))
        expires = timezone.now() + timedelta(minutes=10)  
        EmailOTP.objects.create(user=user, otp=otp, expires_at=expires)

        return Response(
            {"message": "OTP sent to email", "email": user.email},
            status=status.HTTP_201_CREATED
        )


class VerifyOTP(APIView): 
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        otp = request.data.get("otp")

        if not email or not otp:
            return Response({"error": "Email and OTP required"}, status=400)

        user = get_object_or_404(User, email=email)
        otp_obj = EmailOTP.objects.filter(user=user).last()

        if not otp_obj:
            return Response({"error": "OTP not found"}, status=400)

        if otp_obj.is_expired():
            return Response({"error": "OTP expired"}, status=400)

        if otp_obj.otp != otp:
            return Response({"error": "Invalid OTP"}, status=400)

        user.is_active = True
        user.save()
        otp_obj.delete()

        return Response({"message": "Email verified"}, status=200)



class Login(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, email=email, password=password)

        if not user:
            return Response(
                {"error": "Invalid credentials"},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {"error": "Please verify your email"},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh = CustomRefreshToken.for_user(user)

        response = Response(
            {
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                }
            },
            status=status.HTTP_200_OK
        )

        response.set_cookie(
            "access",
            str(refresh.access_token),
            httponly=True,
            samesite="Lax",
            secure= False,
            max_age=60 * 15,  
        )

        response.set_cookie(
            "refresh",
            str(refresh),
            httponly=True,
            samesite="Lax",
            secure= False,
            max_age=60 * 60 * 24 * 7,  
        )

        return response


class Logout(APIView):
    
    permission_classes = [AllowAny] 

    def post(self, request):
        response = Response(
            {"message": "Logged out successfully"},
            status=status.HTTP_200_OK
        )

        refresh_token = request.COOKIES.get("refresh")

        if refresh_token:
            try:
                token = CustomRefreshToken(refresh_token)
                token.blacklist()   
            except Exception:
                pass  

        
        response.delete_cookie("access", samesite="Lax")
        response.delete_cookie("refresh", samesite="Lax")

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
        
        
        response.set_cookie(
            key="access",
            value=response.data["access"],
            httponly=True,
            samesite="Lax",
            secure=False,
            max_age=60 * 15,
        )
        
        
        del response.data["access"]
        return response
        

from rest_framework import generics, permissions

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
    



#pasword forget handling 

from django.contrib.auth import get_user_model

User = get_user_model()

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