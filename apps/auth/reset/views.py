import logging
from urllib.parse import urlencode
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from rest_framework import permissions, throttling, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from .models import PasswordResetToken
from .serializers import ForgotSerializer, VerifySerializer, ResetSerializer

logger = logging.getLogger(__name__)


class PasswordResetThrottle(throttling.ScopedRateThrottle):
    scope = "password_reset"


class ForgotView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetThrottle]

    def post(self, request):
        serializer = ForgotSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Always return 204 to avoid user enumeration
            return Response(status=status.HTTP_204_NO_CONTENT)

        raw, _ = PasswordResetToken.issue(user)

        # Prefer a secure link over raw tokens in emails.
        frontend_url = getattr(settings, "FRONTEND_URL", None)
        subject = "Password reset"
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", None)

        if frontend_url:
            query = urlencode({"token": raw, "email": user.email})
            reset_url = f"{frontend_url.rstrip('/')}/reset-password?{query}"
            body = f"Use the link below to reset your password:\n\n{reset_url}\n\n" \
                   f"If you did not request this, you can ignore this email."
        else:
            # Fallback only if FRONTEND_URL is not configured; still functional.
            logger.warning("FRONTEND_URL not set; sending raw token as fallback.")
            body = (
                "A password reset was requested for your account.\n\n"
                f"Your reset token: {raw}\n\n"
                "If you did not request this, you can ignore this email."
            )

        try:
            send_mail(subject, body, from_email, [user.email])
        except Exception:
            # Do not leak mailer failures to clients; log internally.
            logger.exception("Failed to send password reset email for %s", user.email)

        return Response(status=status.HTTP_204_NO_CONTENT)


class VerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        s = VerifySerializer(data=request.data)
        s.is_valid(raise_exception=True)

        email = s.validated_data["email"]
        token_raw = s.validated_data["token"]

        try:
            user = User.objects.get(email=email)
            prt = (
                PasswordResetToken.objects
                .filter(user=user, used=False)
                .latest("created_at")
            )
        except Exception:
            return Response({"valid": False})

        now = timezone.now()
        valid = prt.matches(token_raw) and prt.expires_at > now
        if not valid:
            return Response({"valid": False})

        expires_in = int((prt.expires_at - now).total_seconds())
        return Response({"valid": True, "expires_in_seconds": max(0, expires_in)})


class ResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        prt = serializer.validated_data["prt"]
        new_password = serializer.validated_data["new_password"]
        now = timezone.now()

        # Atomic, single-consume update: prevents race-based replay
        updated = (
            PasswordResetToken.objects
            .filter(id=prt.id, used=False, expires_at__gt=now)
            .update(used=True)
        )
        if updated != 1:
            # Token was consumed/expired between validation and update.
            raise ValidationError("Invalid token")

        # Set password (Django salts + hashes)
        user.set_password(new_password)
        user.save(update_fields=["password"])

        return Response(status=status.HTTP_204_NO_CONTENT)
