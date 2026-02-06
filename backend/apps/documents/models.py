import uuid
from django.db import models
from django.conf import settings
from pgvector.django import VectorField


class Document(models.Model):
    class FileType(models.TextChoices):
        PDF = "pdf", "pdf"
        DOCX = "docx", "docx"
        TXT = "txt", "txt"
        MD = "md", "md"
        CSV = "csv", "csv"
    
    class Status(models.TextChoices):
        PROCESSING = "processing", "processing"
        READY = "ready", "ready"
        FAILED = "failed", "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Cross-service reference (Phase 1: soft reference to Identity Service)
    # In Phase 2+, this will be validated via Identity Service API
    organization_id = models.UUIDField(
        db_index=True,
        help_text="Reference to Organization in Identity Service"
    )
    
    name = models.CharField(max_length=200)
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    size_bytes = models.PositiveIntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    url = models.URLField()

    # Helper method for cross-service data access
    def get_organization(self):
        """Fetch organization data via Identity Service."""
        from common.services import get_identity_service
        return get_identity_service().get_organization(str(self.organization_id))

    def __str__(self) -> str:
        return f"{self.name} ({self.file_type})"

    class Meta:
        indexes = [
            models.Index(fields=["organization_id", "upload_date"]),
            models.Index(fields=["organization_id", "name"]),
        ]


class DocumentChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey("documents.Document", on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    # VectorField requires dimension known at model import time
    embedding = VectorField(dimensions=getattr(settings, "EMBEDDING_DIM", 1536))

    class Meta:
        unique_together = [("document", "chunk_index")]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
        ]
