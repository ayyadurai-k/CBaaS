from rest_framework import serializers
from .models import Organization

class OrganizationSerializer(serializers.ModelSerializer):
    logo_url = serializers.ImageField(source='logo', read_only=True)
    
    class Meta:
        model = Organization
        fields = ["id", "name", "slug", "logo_url", "created_at", "updated_at"]
        read_only_fields = ["id", "slug", "created_at", "updated_at"]


class UpdateOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name"]
        
    def validate_name(self, value):
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Organization name must be at least 2 characters long.")
        return value.strip()


class OrganizationLogoUploadSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(required=True)
    
    class Meta:
        model = Organization
        fields = ["logo"]
        
    def validate_logo(self, value):
        """Validate uploaded organization logo"""
        # Check file size (max 5MB)
        max_size = 5 * 1024 * 1024  # 5MB in bytes
        if value.size > max_size:
            raise serializers.ValidationError("Logo size cannot exceed 5MB.")
        
        # Check file format
        allowed_formats = ['jpeg', 'jpg', 'png', 'webp']
        file_extension = value.name.split('.')[-1].lower()
        if file_extension not in allowed_formats:
            raise serializers.ValidationError("Only JPEG, PNG, and WEBP images are allowed.")
        
        return value
