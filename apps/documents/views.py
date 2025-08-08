from rest_framework import generics, permissions, serializers
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from common.validators.files import ALLOWED_EXTS
from common.security.permissions import ReadOnlyOrOwnerAdmin
from .models import Document

class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = "__all__"
        read_only_fields = ["id", "organization", "upload_date", "status", "url"]

class DocumentUploadSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    file = serializers.FileField()
    def validate(self, attrs):
        ext = (attrs["file"].name.split(".")[-1] or "").lower()
        if ext not in ALLOWED_EXTS:
            raise serializers.ValidationError("Unsupported file type")
        attrs["ext"] = ext
        return attrs
    def create(self, validated):
        request = self.context["request"]
        org = getattr(request, "organization", None) or request.user.organization
        f = validated["file"]
        path = default_storage.save(f"docs/{org.id}/{f.name}", ContentFile(f.read()))
        url = default_storage.url(path)
        doc = Document.objects.create(organization=org, name=validated["name"],
                                      file_type=validated["ext"], size_bytes=f.size, url=url)
        from .tasks import process_document
        process_document.delay(str(doc.id))
        return doc

class DocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name", "file_type", "status"]
    ordering_fields = ["upload_date", "name", "size_bytes"]
    def get_queryset(self):
        return Document.objects.all()
    def get_serializer_class(self):
        return DocumentUploadSerializer if self.request.method == "POST" else DocumentSerializer

class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOrOwnerAdmin]
    serializer_class = DocumentSerializer
    def get_queryset(self):
        return Document.objects.all()