import logging
from urllib.parse import urlencode
from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, throttling, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.models import User
from apps.auth.reset.serializers import ForgotSerializer, ResetSerializer, VerifySerializer
from apps.auth.reset.models import PasswordResetToken
from common.services.email import postmark_service

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
            # Return consistent response to avoid user enumeration
            return Response({"message": "If an account with this email exists, a reset link has been sent."}, status=status.HTTP_200_OK)

        raw, _ = PasswordResetToken.issue(user)

        # Prefer a secure link over raw tokens in emails.
        frontend_url = getattr(settings, "FRONTEND_URL", None)

        if frontend_url:
            query = urlencode({"token": raw, "email": user.email})
            reset_url = f"{frontend_url.rstrip('/')}/reset-password?{query}"
            
            # Send email via Postmark with professional template
            result = postmark_service.send_password_reset_email(
                to_email=user.email,
                reset_url=reset_url,
                user_name=f"{user.first_name} {user.last_name}".strip() or None
            )
            
            if not result.get("success"):
                # Log the error but don't expose it to the client
                logger.error(f"Failed to send password reset email to {user.email}: {result.get('error')}")
        else:
            # Fallback: log warning if FRONTEND_URL is not configured
            logger.warning("FRONTEND_URL not set; cannot send password reset email")

        return Response({"message": "If an account with this email exists, a reset link has been sent."}, status=status.HTTP_200_OK)


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
            return Response({"valid": False, "message": "Invalid token"})

        now = timezone.now()
        valid = prt.matches(token_raw) and prt.expires_at > now
        if not valid:
            return Response({"valid": False, "message": "Token has expired or is invalid"})

        expires_in = int((prt.expires_at - now).total_seconds())
        return Response({"valid": True, "message": "Token is valid", "expires_in_seconds": max(0, expires_in)})


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

        return Response({"message": "Password has been reset successfully"}, status=status.HTTP_200_OK)
