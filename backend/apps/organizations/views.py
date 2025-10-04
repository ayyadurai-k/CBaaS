from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from django.db import transaction
from common.security.permissions import IsOwnerOrAdmin
from apps.organizations.serializers import (
    OrganizationSerializer,
    UpdateOrganizationSerializer,
    OrganizationLogoUploadSerializer
)
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)


class OrganizationView(APIView):
    permission_classes = [IsOwnerOrAdmin]
    
    def get(self, request):
        """Get organization details"""
        organization = request.user.organization
        if not organization:
            return Response({"detail": "No organization found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrganizationSerializer(organization, context={'request': request})
        return Response(serializer.data)
    
    def put(self, request):
        """Update organization name"""
        organization = request.user.organization
        if not organization:
            return Response({"detail": "No organization found"}, status=status.HTTP_404_NOT_FOUND)
            
        serializer = UpdateOrganizationSerializer(organization, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            # Return updated organization data
            org_serializer = OrganizationSerializer(organization, context={'request': request})
            return Response(org_serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request):
        """Delete organization and all associated data"""
        organization = request.user.organization
        if not organization:
            return Response({"detail": "No organization found"}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            with transaction.atomic():
                # Get all users in this organization before deletion
                org_users = User.objects.filter(organization=organization)
                user_ids = list(org_users.values_list('id', flat=True))
                
                # Blacklist all JWT tokens for users in this organization
                self._blacklist_organization_tokens(user_ids)
                
                # Log the deletion for audit purposes
                logger.info(f"Deleting organization {organization.id} ({organization.name}) with {org_users.count()} users")
                
                # Delete organization (CASCADE will handle users and related data)
                organization_name = organization.name
                organization.delete()
                
                logger.info(f"Successfully deleted organization '{organization_name}' and all associated data")
                
                return Response({
                    "detail": "Organization and all associated data have been permanently deleted",
                    "message": "All user sessions have been terminated"
                }, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Failed to delete organization {organization.id}: {str(e)}")
            return Response({
                "detail": "Failed to delete organization",
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _blacklist_organization_tokens(self, user_ids):
        """Blacklist all JWT tokens for users in the organization"""
        try:
            # Get all outstanding tokens for these users
            outstanding_tokens = OutstandingToken.objects.filter(user_id__in=user_ids)
            
            # Blacklist each token
            for token in outstanding_tokens:
                if not BlacklistedToken.objects.filter(token=token).exists():
                    BlacklistedToken.objects.create(token=token)
            
            logger.info(f"Blacklisted {outstanding_tokens.count()} tokens for {len(user_ids)} users")
            
        except Exception as e:
            logger.error(f"Error blacklisting tokens: {str(e)}")
            # Don't raise exception - continue with deletion even if token blacklisting fails


class OrganizationLogoUploadView(APIView):
    """Upload or update organization logo"""
    permission_classes = [IsOwnerOrAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        """Upload new organization logo"""
        organization = request.user.organization
        if not organization:
            return Response({"detail": "No organization found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = OrganizationLogoUploadSerializer(organization, data=request.data, partial=True)
        if serializer.is_valid():
            # Delete old logo if exists
            if organization.logo:
                organization.logo.delete(save=False)
            
            serializer.save()
            # Return updated organization data
            org_serializer = OrganizationSerializer(organization, context={'request': request})
            return Response(org_serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        """Remove current organization logo"""
        organization = request.user.organization
        if not organization:
            return Response({"detail": "No organization found"}, status=status.HTTP_404_NOT_FOUND)
            
        if organization.logo:
            organization.logo.delete(save=False)
            organization.logo = None
            organization.save()
            org_serializer = OrganizationSerializer(organization, context={'request': request})
            return Response(org_serializer.data, status=status.HTTP_200_OK)
        return Response({"detail": "No logo to delete"}, status=status.HTTP_404_NOT_FOUND)
