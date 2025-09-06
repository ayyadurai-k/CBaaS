from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileSerializer(serializers.ModelSerializer):
    organization = serializers.SerializerMethodField()
    profile_picture_url = serializers.ReadOnlyField()

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
            "profile_picture_url",
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


class ProfilePictureUploadSerializer(serializers.ModelSerializer):
    profile_picture = serializers.ImageField(required=True)
    
    class Meta:
        model = User
        fields = ["profile_picture"]
        
    def validate_profile_picture(self, value):
        """Validate uploaded profile picture"""
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError("Image size cannot exceed 5MB.")
        
        # Check file format
        allowed_formats = ['jpeg', 'jpg', 'png', 'webp']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_formats:
            raise serializers.ValidationError("Only JPEG, PNG, and WEBP images are allowed.")
        
        return value
