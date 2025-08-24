from rest_framework.views import APIView
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from apps.organizations.serializers import UpdateOrganizationSerializer

class OrganizationView(APIView):
    permission_classes = [IsOwnerOrAdmin]
    def put(self, request):
        organization = request.user.organization
        serializer = UpdateOrganizationSerializer(organization, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    def delete(self, request):
        request.user.organization.delete()
        return Response(status=204)
