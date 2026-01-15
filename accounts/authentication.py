# accounts/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.authentication import CSRFCheck
from rest_framework import exceptions

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # 1. Get the token from the cookie named 'access'
        raw_token = request.COOKIES.get('access')
        
        if raw_token is None:
            return None

        # 2. Validate the token
        try:
            validated_token = self.get_validated_token(raw_token)
        except:
            return None

        # 3. Return the user and the token
        return self.get_user(validated_token), validated_token