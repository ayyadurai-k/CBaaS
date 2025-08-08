from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, throttling, serializers
from django.utils import timezone
from django.core.mail import send_mail
from apps.users.models import User
from .models import PasswordResetToken


class ScopedThrottle(throttling.ScopedRateThrottle):
    scope = None


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
            prt = PasswordResetToken.objects.filter(user=user, used=False).latest(
                "created_at"
            )
        except Exception:
            raise serializers.ValidationError("Invalid token")
        if not prt.matches(data["token"]) or prt.expires_at < timezone.now():
            raise serializers.ValidationError("Invalid token")
        data["user"], data["prt"] = user, prt
        return data


class ForgotView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedThrottle]
    throttle_scope = "password_reset"

    def post(self, request):
        s = ForgotSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=s.validated_data["email"])
        except User.DoesNotExist:
            return Response(status=204)
        raw, _ = PasswordResetToken.issue(user)
        send_mail("Password reset", f"Your reset token: {raw}", None, [user.email])
        return Response(status=204)


class VerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = VerifySerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=s.validated_data["email"])
            prt = PasswordResetToken.objects.filter(user=user, used=False).latest(
                "created_at"
            )
        except Exception:
            return Response({"valid": False})
        valid = (
            prt.matches(s.validated_data["token"]) and prt.expires_at > timezone.now()
        )
        return Response({"valid": bool(valid)})


class ResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = ResetSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        u, prt = s.validated_data["user"], s.validated_data["prt"]
        u.set_password(s.validated_data["new_password"])
        u.save(update_fields=["password"])
        prt.used = True
        prt.save(update_fields=["used"])
        return Response(status=204)
