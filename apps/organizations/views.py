from rest_framework.views import APIView
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from .models import Organization
from .serializers import UpdateOrganizationSerializer

class OrganizationView(APIView):
    permission_classes = [IsOwnerOrAdmin]
    def put(self, request):
        org = request.user.organization
        s = UpdateOrganizationSerializer(org, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)
    def delete(self, request):
        request.user.organization.delete()
        return Response(status=204)
