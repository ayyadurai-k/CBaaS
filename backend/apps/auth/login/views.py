from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, throttling
from rest_framework_simplejwt.tokens import RefreshToken
from apps.auth.login.serializers import LoginSerializer
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

class ScopedThrottle(throttling.ScopedRateThrottle):
    scope = None

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [ScopedThrottle]
    throttle_scope = "login"
    
    @extend_schema(
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                response={
                    "type": "object",
                    "properties": {
                        "access": {"type": "string", "description": "JWT access token"},
                        "refresh": {"type": "string", "description": "JWT refresh token"},
                        "user": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string", "format": "uuid"},
                                "email": {"type": "string", "format": "email"},
                                "name": {"type": "string"}
                            }
                        }
                    }
                },
                examples=[
                    OpenApiExample(
                        "Success Response",
                        value={
                            "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                            "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
                            "user": {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "email": "user@example.com",
                                "name": "John Doe"
                            }
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid credentials or validation error",
                examples=[
                    OpenApiExample(
                        "Invalid Credentials",
                        value={
                            "email": ["Invalid email or password."]
                        }
                    )
                ]
            ),
            429: OpenApiResponse(description="Too many login attempts")
        },
        examples=[
            OpenApiExample(
                "Login Request",
                value={
                    "email": "user@example.com",
                    "password": "yourpassword123"
                },
                request_only=True
            )
        ],
        tags=["Authentication"],
        summary="User Login",
        description="Authenticate user with email and password. Returns JWT access and refresh tokens."
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token), 
            "refresh": str(refresh),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
            }
        })
