from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from accounts.serializers import RegisterSerializer
from accounts.services.otp import send_email_otp


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            send_email_otp(user)

            return Response(
                {"message": "OTP sent to email"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    



from accounts.serializers import VerifyOTPSerializer


class VerifyOTPView(APIView):
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            otp_obj = serializer.validated_data['otp_obj']

            otp_obj.is_used = True
            otp_obj.save()

           
            user.is_active = True
            user.save()

            return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

#loggginn
from accounts.serializers import LoginSerializer
from rest_framework_simplejwt.tokens import RefreshToken

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            tokens = serializer.create_tokens(user)

            return Response({
                "message": "Login successful",
                "access": tokens['access'],
                "refresh": tokens['refresh']
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    


from .serializers import CustomTokenObtainSerializer

class CustomTokenObtainView(APIView):
    def post(self, request):
        serializer = CustomTokenObtainSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



