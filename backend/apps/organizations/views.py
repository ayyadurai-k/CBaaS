from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from common.security.permissions import IsOwnerOrAdmin
from apps.organizations.serializers import (
    OrganizationSerializer,
    UpdateOrganizationSerializer,
    OrganizationLogoUploadSerializer
)


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
        """Delete organization"""
        organization = request.user.organization
        if not organization:
            return Response({"detail": "No organization found"}, status=status.HTTP_404_NOT_FOUND)
            
        organization.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


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
