from rest_framework import generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from common.security.permissions import IsOwnerOrAdmin
from apps.api_keys.models import APIKey
from apps.api_keys.serializers import APIKeySerializer, APIKeyCreateSerializer


class APIKeyListCreateView(generics.ListCreateAPIView):
    """
    List all API keys for the authenticated user's organization or create a new one.
    """
    permission_classes = [IsOwnerOrAdmin]
    queryset = APIKey.objects.all()  # Will be filtered by OrganizationFilterBackend

    def get_serializer_class(self):
        return (
            APIKeyCreateSerializer
            if self.request.method == "POST"
            else APIKeySerializer
        )

    @extend_schema(
        summary="List API keys",
        description="Retrieve all API keys belonging to the authenticated user's organization",
        responses={
            200: OpenApiResponse(
                description="List of API keys",
                response=APIKeySerializer(many=True),
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "count": 2,
                            "next": None,
                            "previous": None,
                            "results": [
                                {
                                    "id": "123e4567-e89b-12d3-a456-426614174000",
                                    "name": "Production API Key",
                                    "status": "active",
                                    "usage_count": 1523,
                                    "quota": 10000,
                                    "scope": "full-access",
                                    "created_at": "2024-01-15T10:30:00Z",
                                    "updated_at": "2024-01-20T14:22:00Z",
                                    "last_used_at": "2024-01-20T14:22:00Z",
                                    "expires_at": "2025-01-15T10:30:00Z",
                                    "allowed_ips": ["203.0.113.1", "203.0.113.2"],
                                    "rate_limit_per_minute": 60,
                                    "metadata": {"environment": "production"},
                                    "revoked_reason": ""
                                }
                            ]
                        }
                    )
                ]
            )
        },
        tags=["API Keys"]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Create API key",
        description="Create a new API key with optional security constraints (expiration, IP whitelist, rate limits)",
        request=APIKeyCreateSerializer,
        responses={
            201: OpenApiResponse(
                description="API key successfully created",
                response=APIKeySerializer,
                examples=[
                    OpenApiExample(
                        "Success",
                        value={
                            "id": "123e4567-e89b-12d3-a456-426614174001",
                            "name": "New API Key",
                            "status": "active",
                            "usage_count": 0,
                            "quota": 5000,
                            "scope": "read-only",
                            "created_at": "2024-01-21T09:15:00Z",
                            "updated_at": "2024-01-21T09:15:00Z",
                            "last_used_at": None,
                            "expires_at": "2024-12-31T23:59:59Z",
                            "allowed_ips": ["203.0.113.10"],
                            "rate_limit_per_minute": 30,
                            "metadata": {"purpose": "testing"},
                            "revoked_reason": "",
                            "api_key": "xk_AbCdEf123456...XyZ"  # Only shown once
                        }
                    )
                ]
            ),
            400: OpenApiResponse(
                description="Validation error",
                examples=[
                    OpenApiExample(
                        "Invalid IP",
                        value={"error": "Invalid IP address: 999.999.999.999"}
                    ),
                    OpenApiExample(
                        "Duplicate name",
                        value={"error": "API key with this name already exists."}
                    ),
                    OpenApiExample(
                        "Past expiration",
                        value={"error": "Expiration date must be in the future"}
                    )
                ]
            )
        },
        tags=["API Keys"]
    )
    def create(self, request, *args, **kwargs):
        serializer = APIKeyCreateSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        key = serializer.save()
        data = APIKeySerializer(key).data
        data["api_key"] = getattr(key, "_plaintext", None)
        return Response(data, status=status.HTTP_201_CREATED)


class APIKeyRevokeView(generics.UpdateAPIView):
    """
    Revoke an API key, preventing further usage.
    """
    permission_classes = [IsOwnerOrAdmin]
    queryset = APIKey.objects.all()  # Will be filtered by OrganizationFilterBackend

    @extend_schema(
        summary="Revoke API key",
        description="Revoke an API key to prevent further usage. Revoked keys cannot be re-activated.",
        request=None,
        responses={
            204: OpenApiResponse(description="API key successfully revoked"),
            404: OpenApiResponse(
                description="API key not found",
                examples=[
                    OpenApiExample(
                        "Not found",
                        value={"error": "Not found."}
                    )
                ]
            )
        },
        tags=["API Keys"]
    )
    def patch(self, request, *args, **kwargs):
        key = self.get_object()
        key.status = APIKey.Status.REVOKED
        key.save(update_fields=["status"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class APIKeyDeleteView(generics.DestroyAPIView):
    """
    Permanently delete an API key from the system.
    """
    permission_classes = [IsOwnerOrAdmin]
    queryset = APIKey.objects.all()  # Will be filtered by OrganizationFilterBackend

    @extend_schema(
        summary="Delete API key",
        description="Permanently delete an API key. This action cannot be undone.",
        responses={
            204: OpenApiResponse(description="API key successfully deleted"),
            404: OpenApiResponse(
                description="API key not found",
                examples=[
                    OpenApiExample(
                        "Not found",
                        value={"error": "Not found."}
                    )
                ]
            )
        },
        tags=["API Keys"]
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
