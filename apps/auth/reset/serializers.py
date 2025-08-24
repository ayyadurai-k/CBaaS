from django.utils import timezone
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from apps.users.models import User
from .models import PasswordResetToken
from django.core.exceptions import ValidationError as DjangoValidationError


class ForgotSerializer(serializers.Serializer):
    email = serializers.EmailField()


class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField(trim_whitespace=False)


class ResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField(trim_whitespace=False)
    new_password = serializers.CharField(min_length=8, write_only=True, trim_whitespace=False)

    def validate(self, data):
        email = data.get("email")
        token_raw = data.get("token")
        try:
            user = User.objects.get(email=email)
            prt = (
                PasswordResetToken.objects
                .filter(user=user, used=False)
                .latest("created_at")
            )
        except Exception:
            raise serializers.ValidationError("Invalid token")

        # Validate token & expiry without consuming it
        if not prt.matches(token_raw) or prt.expires_at <= timezone.now():
            raise serializers.ValidationError("Invalid token")

        # Validate password strength against Django validators
        try:
            validate_password(data["new_password"], user=user)
        except DjangoValidationError as e:
            raise serializers.ValidationError({"new_password": e.messages})

        data["user"] = user
        data["prt"] = prt
        return data
