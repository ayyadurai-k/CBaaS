from rest_framework import generics, status
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from .models import APIKey
from apps.api_keys.serializers import APIKeySerializer, APIKeyCreateSerializer

class APIKeyListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsOwnerOrAdmin]
    def get_queryset(self):
        return APIKey.objects.all()
    def get_serializer_class(self):
        return APIKeyCreateSerializer if self.request.method == "POST" else APIKeySerializer
    def create(self, request, *args, **kwargs):
        s = APIKeyCreateSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        key = s.save()
        data = APIKeySerializer(key).data
        data["plaintext"] = getattr(key, "plaintext", None)
        return Response(data, status=201)

class APIKeyRevokeView(generics.UpdateAPIView):
    permission_classes = [IsOwnerOrAdmin]
    queryset = APIKey.objects.all()
    def patch(self, request, *args, **kwargs):
        key = self.get_object()
        key.status = APIKey.Status.REVOKED
        key.save(update_fields=["status"])
        return Response(status=204)

class APIKeyDeleteView(generics.DestroyAPIView):
    permission_classes = [IsOwnerOrAdmin]
    queryset = APIKey.objects.all()
