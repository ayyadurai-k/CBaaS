from rest_framework import generics, status
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from .models import APIKey
from rest_framework import serializers

class APIKeySerializer(serializers.ModelSerializer):
    plaintext = serializers.CharField(read_only=True)
    class Meta:
        model = APIKey
        fields = ["id","name","status","usage_count","quota","scope","created_at","plaintext"]
        read_only_fields = ["id","status","usage_count","created_at","plaintext"]

class APIKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    quota = serializers.IntegerField(required=False, min_value=1)
    scope = serializers.ChoiceField(choices=APIKey.Scope.choices, default=APIKey.Scope.FULL)
    def create(self, validated):
        org = self.context["request"].user.organization
        key = APIKey(organization=org, name=validated["name"], quota=validated.get("quota"), scope=validated["scope"])
        raw = APIKey.generate_plaintext()
        key.key = raw
        key.save()
        key.plaintext = raw
        return key

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