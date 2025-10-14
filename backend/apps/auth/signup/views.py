from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, throttling
from rest_framework_simplejwt.tokens import RefreshToken
from apps.auth.signup.serializers import SignupSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample


class ScopedThrottle(throttling.ScopedRateThrottle):
    scope = None


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedThrottle]
    throttle_scope = "login"

    @extend_schema(
        request=SignupSerializer,
        responses={
            201: OpenApiResponse(
                description="User successfully registered",
                response={
                    "type": "object",
                    "properties": {
                        "access": {"type": "string", "description": "JWT access token"},
                        "refresh": {"type": "string", "description": "JWT refresh token"}
                    }
                },
                examples=[
                    OpenApiExample(
                        "Success Response",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Passwords don't match",
                        value={
                            "non_field_errors": ["Passwords do not match."]
                        }
                    ),
                    OpenApiExample(
                        "Email already exists",
                        value={
                            "email": ["User with this email already exists."]
                        }
                    )
                ]
            ),
            429: OpenApiResponse(description="Too many signup attempts")
        },
        examples=[
            OpenApiExample(
                "Signup Request",
                value={
                    "email": "user@example.com",
                    "password": "SecurePass123!",
                    "confirm_password": "SecurePass123!",
                    "name": "John Doe",
                    "phone_number": "+1234567890",
                    "organization_name": "My Company"
                },
                request_only=True
            )
        ],
        tags=["Authentication"],
        summary="User Registration",
        description="Register a new user account with organization. Creates both user and organization, returning JWT tokens for immediate authentication."
    )
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=201,
        )
