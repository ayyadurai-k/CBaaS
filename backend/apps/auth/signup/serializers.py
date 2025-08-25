from rest_framework import serializers
from django.db import transaction
from apps.users.models import User
from apps.organizations.models import Organization


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True, min_length=8)
    name = serializers.CharField(max_length=100)
    phone_number = serializers.CharField(max_length=15)
    organization_name = serializers.CharField(max_length=100)

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    @transaction.atomic
    def create(self, validated):
        org = Organization.objects.create(name=validated["organization_name"])
        user = User.objects.create_user(
            email=validated["email"],
            password=validated["password"],
            name=validated["name"],
            phone_number=validated["phone_number"],
            organization=org,
            role=User.Role.OWNER,
        )
        return user
