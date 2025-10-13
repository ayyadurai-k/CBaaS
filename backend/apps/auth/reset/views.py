import logging
from urllib.parse import urlencode
from django.conf import settings
from django.utils import timezone
from rest_framework import permissions, throttling, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from apps.users.models import User
from apps.auth.reset.serializers import ForgotSerializer, ResetSerializer, VerifySerializer
from apps.auth.reset.models import PasswordResetToken
from apps.auth.reset.tasks import send_password_reset_email_task

logger = logging.getLogger(__name__)


class PasswordResetThrottle(throttling.ScopedRateThrottle):
    scope = "password_reset"


class ForgotView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetThrottle]

    @extend_schema(
        request=ForgotSerializer,
        responses={
            200: OpenApiResponse(
                description="Reset email sent (or user doesn't exist - consistent response for security)",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"}
                    }
                },
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "If an account with this email exists, a reset link has been sent."}
                    )
                ]
            ),
            429: OpenApiResponse(description="Too many password reset requests")
        },
        examples=[
            OpenApiExample(
                "Forgot Password Request",
                value={"email": "user@example.com"},
                request_only=True
            )
        ],
        tags=["Authentication"],
        summary="Request Password Reset",
        description="Request a password reset email. Returns consistent response regardless of whether email exists (prevents user enumeration). Reset link is sent via email if account exists."
    )
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

            # Send email asynchronously via Celery task
            send_password_reset_email_task.delay(
                to_email=user.email,
                reset_url=reset_url,
                user_name=f"{user.name}".strip() or None,
            )
            logger.info(f"Password reset email task queued for {user.email}")
        else:
            # Fallback: log warning if FRONTEND_URL is not configured
            logger.warning("FRONTEND_URL not set; cannot send password reset email")

        return Response({"message": "If an accouant with this email exists, a reset link has been sent."}, status=status.HTTP_200_OK)


class VerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=VerifySerializer,
        responses={
            200: OpenApiResponse(
                description="Token verification result",
                response={
                    "type": "object",
                    "properties": {
                        "valid": {"type": "boolean"},
                        "message": {"type": "string"},
                        "expires_in_seconds": {"type": "integer", "description": "Seconds until token expires (only if valid)"}
                    }
                },
                examples=[
                    OpenApiExample(
                        "Valid Token",
                        value={
                            "valid": True,
                            "message": "Token is valid",
                            "expires_in_seconds": 1800
                        }
                    ),
                    OpenApiExample(
                        "Invalid Token",
                        value={
                            "valid": False,
                            "message": "Token has expired or is invalid"
                        }
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                "Verify Token Request",
                value={
                    "email": "user@example.com",
                    "token": "abc123xyz789"
                },
                request_only=True
            )
        ],
        tags=["Authentication"],
        summary="Verify Password Reset Token",
        description="Verify if a password reset token is valid and not expired. Check this before allowing user to set new password."
    )
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

    @extend_schema(
        request=ResetSerializer,
        responses={
            200: OpenApiResponse(
                description="Password successfully reset",
                response={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"}
                    }
                },
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"message": "Password has been reset successfully"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid token or validation error",
                examples=[
                    OpenApiExample(
                        "Invalid Token",
                        value={"non_field_errors": ["Invalid token"]}
                    ),
                    OpenApiExample(
                        "Weak Password",
                        value={"new_password": ["This password is too common."]}
                    )
                ]
            )
        },
        examples=[
            OpenApiExample(
                "Reset Password Request",
                value={
                    "email": "user@example.com",
                    "token": "abc123xyz789",
                    "new_password": "NewSecurePass123!"
                },
                request_only=True
            )
        ],
        tags=["Authentication"],
        summary="Reset Password",
        description="Reset user password using valid reset token. Token is consumed after use (single-use). Password must meet Django's validation requirements."
    )
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
