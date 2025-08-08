import uuid, secrets, hmac, hashlib
from django.db import models
from django.conf import settings
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
    key_hmac = models.CharField(max_length=64, unique=True, db_index=True, null=True, blank=True)  # NEW
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    usage_count = models.PositiveIntegerField(default=0)
    quota = models.PositiveIntegerField(null=True, blank=True)
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.FULL)

    @staticmethod
    def generate_plaintext() -> str:
        return secrets.token_urlsafe(40)

    @staticmethod
    def _hmac(raw: str) -> str:
        secret = getattr(settings, "API_KEY_HMAC_SECRET", "") or ""
        if not secret:
            # fallback to encryption key if not provided (still better than nothing)
            secret = getattr(settings, "ENCRYPTION_SECRET_KEY", "")
        mac = hmac.new(secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()
        return mac

    @property
    def key(self) -> str:
        return Encryptor.decrypt(self.key_encrypted)

    @key.setter
    def key(self, value: str):
        self.key_encrypted = Encryptor.encrypt(value)
        self.key_hmac = self._hmac(value)

    @classmethod
    def get_by_plaintext(cls, raw: str) -> "APIKey":
        return cls.objects.select_related("organization").get(key_hmac=cls._hmac(raw))
