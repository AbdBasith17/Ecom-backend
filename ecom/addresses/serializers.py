from rest_framework import serializers
from .models import Address


class AddressSerializer(serializers.ModelSerializer):
    user_name = serializers.ReadOnlyField(source='user.get_full_name')

    class Meta:
        model = Address
        fields = ["id", "user_name", "phone", "address_line", "city", "state", "pincode", "is_default"]
        read_only_fields = ["user"]
