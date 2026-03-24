from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.Serializer):
    name = serializers.CharField(min_length=3, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=6)

    def validate_email(self, value):
        return value.lower().strip()

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            name=validated_data.get("name", ""),
            is_active=False  
        )
        return user


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        
        fields = ['id', 'name', 'email', 'is_active', 'role']