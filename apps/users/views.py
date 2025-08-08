from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework import serializers

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


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(ProfileSerializer(request.user).data)
