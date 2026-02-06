"""
gRPC Service for Identity domain.

Provides gRPC endpoints for User, Organization, and API Key operations.
This service will be the primary interface for the Identity microservice.
"""
import logging
from typing import Optional
from uuid import UUID

import grpc
from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action

from apps.users.models import User
from apps.organizations.models import Organization
from apps.api_keys.models import APIKey

from common.grpc.serializers.identity import (
    UserProtoSerializer,
    UserCreateProtoSerializer,
    OrganizationProtoSerializer,
    OrganizationCreateProtoSerializer,
    ValidateAPIKeyRequestSerializer,
    ValidateAPIKeyResponseSerializer,
)

logger = logging.getLogger(__name__)


class UserGRPCService(
    mixins.AsyncListModelMixin,
    mixins.AsyncRetrieveModelMixin,
    mixins.AsyncCreateModelMixin,
    mixins.AsyncUpdateModelMixin,
    mixins.AsyncDestroyModelMixin,
    generics.GenericService,
):
    """
    gRPC Service for User operations.
    
    Provides CRUD operations for users and user-related queries.
    Used by other services for user validation and data retrieval.
    """
    queryset = User.objects.all()
    serializer_class = UserProtoSerializer
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'Create':
            return UserCreateProtoSerializer
        return UserProtoSerializer
    
    @grpc_action(
        request=[{"name": "email", "type": "string"}],
        response=UserProtoSerializer,
    )
    async def GetByEmail(self, request, context):
        """
        Get user by email address.
        
        Used by authentication services to look up users during login.
        """
        try:
            user = await User.objects.aget(email=request.email)
            serializer = UserProtoSerializer(user)
            return serializer.message
        except User.DoesNotExist:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"User with email {request.email} not found"
            )
    
    @grpc_action(
        request=[{"name": "organization_id", "type": "string"}],
        response=UserProtoSerializer,
        response_stream=True,
    )
    async def ListByOrganization(self, request, context):
        """
        List all users in an organization.
        
        Streams users for efficient handling of large organizations.
        """
        org_id = UUID(request.organization_id)
        async for user in User.objects.filter(organization_id=org_id).aiterator():
            serializer = UserProtoSerializer(user)
            yield serializer.message
    
    @grpc_action(
        request=[{"name": "user_id", "type": "string"}],
        response=[{"name": "exists", "type": "bool"}],
    )
    async def Exists(self, request, context):
        """
        Check if a user exists by ID.
        
        Lightweight existence check for validation purposes.
        """
        try:
            user_id = UUID(request.user_id)
            exists = await User.objects.filter(id=user_id).aexists()
            return {"exists": exists}
        except ValueError:
            return {"exists": False}


class OrganizationGRPCService(
    mixins.AsyncListModelMixin,
    mixins.AsyncRetrieveModelMixin,
    mixins.AsyncCreateModelMixin,
    mixins.AsyncUpdateModelMixin,
    generics.GenericService,
):
    """
    gRPC Service for Organization operations.
    
    Provides CRUD and query operations for organizations.
    Critical for multi-tenant data isolation.
    """
    queryset = Organization.objects.all()
    serializer_class = OrganizationProtoSerializer
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'Create':
            return OrganizationCreateProtoSerializer
        return OrganizationProtoSerializer
    
    @grpc_action(
        request=[{"name": "slug", "type": "string"}],
        response=OrganizationProtoSerializer,
    )
    async def GetBySlug(self, request, context):
        """
        Get organization by slug.
        
        Used for URL-based organization lookup.
        """
        try:
            org = await Organization.objects.aget(slug=request.slug)
            serializer = OrganizationProtoSerializer(org)
            return serializer.message
        except Organization.DoesNotExist:
            context.abort(
                grpc.StatusCode.NOT_FOUND,
                f"Organization with slug {request.slug} not found"
            )
    
    @grpc_action(
        request=[{"name": "organization_id", "type": "string"}],
        response=[{"name": "exists", "type": "bool"}],
    )
    async def Exists(self, request, context):
        """
        Check if an organization exists by ID.
        
        Lightweight existence check for tenant validation.
        """
        try:
            org_id = UUID(request.organization_id)
            exists = await Organization.objects.filter(id=org_id).aexists()
            return {"exists": exists}
        except ValueError:
            return {"exists": False}


class APIKeyGRPCService(generics.GenericService):
    """
    gRPC Service for API Key validation.
    
    Provides API key validation and permission checking
    for external API authentication.
    """
    
    @grpc_action(
        request=ValidateAPIKeyRequestSerializer,
        response=ValidateAPIKeyResponseSerializer,
    )
    async def Validate(self, request, context):
        """
        Validate an API key and return its permissions.
        
        Used by API gateway and other services to validate
        incoming API key authentication.
        """
        try:
            from apps.api_keys.services import validate_api_key
            
            result = await validate_api_key(request.api_key)
            
            if result.get('valid', False):
                return {
                    "is_valid": True,
                    "organization_id": str(result.get('organization_id', '')),
                    "permissions": result.get('permissions', []),
                    "error_message": None,
                }
            else:
                return {
                    "is_valid": False,
                    "organization_id": None,
                    "permissions": [],
                    "error_message": result.get('error', 'Invalid API key'),
                }
        except Exception as e:
            logger.error(f"API key validation error: {str(e)}")
            return {
                "is_valid": False,
                "organization_id": None,
                "permissions": [],
                "error_message": str(e),
            }
