from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "refresh": {"type": "string", "description": "JWT refresh token to blacklist"}
            },
            "required": ["refresh"]
        },
        responses={
            200: OpenApiResponse(
                description="Successfully logged out",
                response={
                    "type": "object",
                    "properties": {
                        "detail": {"type": "string"}
                    }
                },
                examples=[
                    OpenApiExample(
                        "Success",
                        value={"detail": "Successfully logged out"}
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Invalid or missing refresh token",
                examples=[
                    OpenApiExample(
                        "Missing token",
                        value={"detail": "refresh token required"}
                    ),
                    OpenApiExample(
                        "Invalid token",
                        value={"detail": "Invalid token"}
                    )
                ]
            ),
            401: OpenApiResponse(description="Authentication required")
        },
        examples=[
            OpenApiExample(
                "Logout Request",
                value={"refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."},
                request_only=True
            )
        ],
        tags=["Authentication"],
        summary="User Logout",
        description="Logout user by blacklisting the refresh token. Requires authentication with access token in Authorization header."
    )
    def post(self, request):
        token = request.data.get("refresh")
        if not token:
            return Response({"detail": "refresh token required"}, status=400)
        try:
            RefreshToken(token).blacklist()
            return Response({"detail": "Successfully logged out"}, status=200)
        except Exception as e:
            return Response({"detail": "Invalid token"}, status=400)