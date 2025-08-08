import uuid, secrets
from django.db import models
from common.security.encryption import Encryptor

class APIKey(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "active"
        REVOKED = "revoked", "revoked"
    class Scope(models.TextChoices):
        FULL = "full-access", "full-access"
        READ_ONLY = "read-only", "read-only"
        UPLOAD_ONLY = "upload-only", "upload-only"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    key_encrypted = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    usage_count = models.PositiveIntegerField(default=0)
    quota = models.PositiveIntegerField(null=True, blank=True)
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.FULL)

    @staticmethod
    def generate_plaintext() -> str:
        return secrets.token_urlsafe(40)
    @property
    def key(self) -> str:
        return Encryptor.decrypt(self.key_encrypted)
    @key.setter
    def key(self, value: str):
        self.key_encrypted = Encryptor.encrypt(value)
    @classmethod
    def get_plaintext(cls, raw: str) -> "APIKey":
        for k in cls.objects.select_related("organization").filter(status=cls.Status.ACTIVE):
            if k.key == raw:
                return k
        raise cls.DoesNotExist