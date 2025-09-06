from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "role",
            "phone_number",
            "created_at",
            "updated_at",
            "organization",
        ]

    def get_organization(self, obj):
        org = getattr(obj, "organization", None)
        if not org:
            return None
        return {
            "id": str(org.id),
            "name": org.name,
            "logo_url": org.logo_url,
            "created_at": org.created_at,
            "updated_at": org.updated_at,
        }


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "name",
            "phone_number",
        ]
        
    def validate_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Name must be at least 2 characters long.")
        return value.strip()
        
    def validate_phone_number(self, value):
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError("Phone number must be at least 10 digits.")
        return value.strip() if value else None
