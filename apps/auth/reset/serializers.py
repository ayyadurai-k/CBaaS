from rest_framework import serializers
from django.utils import timezone
from apps.users.models import User
from .models import PasswordResetToken

class ForgotSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()

class ResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()
    new_password = serializers.CharField(min_length=8)

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
            # prt - password reset token
            prt = PasswordResetToken.objects.filter(user=user, used=False).latest(
                "created_at"
            )
        except Exception:
            raise serializers.ValidationError("Invalid token")
        if not prt.matches(data["token"]) or prt.expires_at < timezone.now():
            raise serializers.ValidationError("Invalid token")
        data["user"], data["prt"] = user, prt
        return data
