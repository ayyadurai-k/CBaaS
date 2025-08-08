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
