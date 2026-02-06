from rest_framework import serializers
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from common.validators.files import ALLOWED_EXTS
from apps.documents.models import Document


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for document listing and detail views."""
    organization_name = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            "id",
            "organization_id",
            "organization_name",
            "name",
            "file_type",
            "size_bytes",
            "upload_date",
            "status",
            "url",
        ]
        read_only_fields = ["id", "organization_id", "upload_date", "status", "url"]

    def get_organization_name(self, obj):
        """Fetch organization name via Identity Service."""
        org = obj.get_organization()
        return org.name if org else None


class DocumentUploadSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    file = serializers.FileField(write_only=True)

    def validate(self, attrs):
        ext = (attrs["file"].name.split(".")[-1] or "").lower()
        if ext not in ALLOWED_EXTS:
            raise serializers.ValidationError("Unsupported file type")
        attrs["ext"] = ext
        return attrs

    def create(self, validated):
        request = self.context["request"]
        # Get organization_id from request context
        org = getattr(request, "organization", None) or request.user.organization
        org_id = org.id if org else request.user.organization_id
        
        f = validated["file"]
        path = default_storage.save(f"docs/{org_id}/{f.name}", ContentFile(f.read()))
        url = default_storage.url(path)
        
        doc = Document.objects.create(
            organization_id=org_id,
            name=validated["name"],
            file_type=validated["ext"],
            size_bytes=f.size,
            url=url,
        )
        
        # Trigger async processing via Knowledge Service
        from common.services import get_knowledge_service
        get_knowledge_service().trigger_document_processing(str(doc.id))
        
        return doc
