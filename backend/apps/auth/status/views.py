from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample


class AuthStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="User is authenticated",
                response={
                    "type": "object",
                    "properties": {
                        "authenticated": {"type": "boolean"},
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
                        "Authenticated User",
                        value={
                            "authenticated": True,
                            "user": {
                                "id": "123e4567-e89b-12d3-a456-426614174000",
                                "email": "user@example.com",
                                "name": "John Doe"
                            }
                        }
                    )
                ]
            ),
            401: OpenApiResponse(description="Not authenticated")
        },
        tags=["Authentication"],
        summary="Check Authentication Status",
        description="Verify if the current user is authenticated and return user information. Requires valid JWT access token."
    )
    def get(self, request):
        """
        Check if the user is authenticated and return user info
        """
        user = request.user
        return Response({
            "authenticated": True,
            "user": {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
            }
        }, status=status.HTTP_200_OK)
