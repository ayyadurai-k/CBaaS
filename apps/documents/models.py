import uuid
from django.db import models

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
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    file_type = models.CharField(max_length=10, choices=FileType.choices)
    size_bytes = models.PositiveIntegerField()
    upload_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    url = models.URLField()

    class Meta:
        indexes = [
            models.Index(fields=["organization", "upload_date"]),
            models.Index(fields=["organization", "name"]),
        ]