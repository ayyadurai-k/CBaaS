import uuid, secrets, hmac, hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone
from common.security.encryption import Encryptor


class APIKey(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        REVOKED = "revoked", "Revoked"
        EXPIRED = "expired", "Expired"

    class Scope(models.TextChoices):
        FULL = "full-access", "Full Access"
        READ_ONLY = "read-only", "Read Only"
        UPLOAD_ONLY = "upload-only", "Upload Only"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization", 
        on_delete=models.CASCADE,
        related_name="api_keys"
    )
    name = models.CharField(max_length=100, unique=True)
    key_encrypted = models.CharField(max_length=255)
    key_hmac = models.CharField(
        max_length=64, unique=True, db_index=True, null=True, blank=True
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="Optional expiration date")
    
    # Status and quotas
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.ACTIVE
    )
    usage_count = models.PositiveIntegerField(default=0)
    quota = models.PositiveIntegerField(null=True, blank=True, help_text="Max requests allowed")
    
    # Permissions and security
    scope = models.CharField(max_length=20, choices=Scope.choices, default=Scope.FULL)
    allowed_ips = models.JSONField(
        default=list, 
        blank=True,
        help_text="List of allowed IP addresses. Empty = allow all"
    )
    rate_limit_per_minute = models.PositiveIntegerField(
        null=True, 
        blank=True,
        help_text="Custom rate limit for this key (overrides default)"
    )
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True, help_text="Custom metadata")
    revoked_reason = models.TextField(blank=True, help_text="Reason for revocation")

    _plaintext: str | None = None

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', '-created_at']),
            models.Index(fields=['status', '-last_used_at']),
            models.Index(fields=['expires_at']),
        ]
        verbose_name = "API Key"
        verbose_name_plural = "API Keys"

    def __str__(self):
        return f"{self.name} ({self.organization.name})"

    @staticmethod
    def generate_plaintext() -> str:
        """Generate a secure random API key"""
        return secrets.token_urlsafe(40)

    @staticmethod
    def _hmac(raw: str) -> str:
        """Generate HMAC hash for constant-time lookup"""
        secret = getattr(settings, "API_KEY_HMAC_SECRET", "") or ""
        if not secret:
            # fallback to encryption key if not provided (still better than nothing)
            secret = getattr(settings, "ENCRYPTION_SECRET_KEY", "")
        mac = hmac.new(
            secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return mac

    @property
    def key(self) -> str:
        """Decrypt and return the plaintext key"""
        return Encryptor.decrypt(self.key_encrypted)

    @key.setter
    def key(self, value: str):
        """Encrypt and store the key with HMAC"""
        self.key_encrypted = Encryptor.encrypt(value)
        self.key_hmac = self._hmac(value)

    @classmethod
    def get_by_plaintext(cls, raw: str) -> "APIKey":
        """
        Lookup API key by plaintext value using HMAC.
        Raises DoesNotExist if not found.
        """
        return cls.objects.select_related("organization").get(key_hmac=cls._hmac(raw))

    def is_expired(self) -> bool:
        """Check if the key has expired"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def is_ip_allowed(self, ip_address: str) -> bool:
        """
        Check if the given IP address is allowed to use this key.
        Returns True if no IP restrictions are configured.
        """
        if not self.allowed_ips:
            return True  # No restrictions
        return ip_address in self.allowed_ips

    def is_quota_exceeded(self) -> bool:
        """Check if the usage quota has been exceeded"""
        if self.quota is None:
            return False
        return self.usage_count >= self.quota

    def can_be_used(self) -> tuple[bool, str]:
        """
        Comprehensive validation of whether this key can be used.
        Returns (is_valid, error_message)
        """
        if self.status == self.Status.REVOKED:
            reason = f" Reason: {self.revoked_reason}" if self.revoked_reason else ""
            return False, f"API key has been revoked.{reason}"
        
        if self.status == self.Status.EXPIRED:
            return False, "API key has expired"
        
        if self.is_expired():
            # Auto-update status if expired
            self.status = self.Status.EXPIRED
            self.save(update_fields=['status'])
            return False, "API key has expired"
        
        if self.is_quota_exceeded():
            return False, f"API key quota exceeded. Used {self.usage_count} of {self.quota} requests."
        
        return True, ""

    def record_usage(self, increment: int = 1):
        """
        Atomically increment usage count and update last_used_at.
        Thread-safe using F() expression.
        """
        from django.db.models import F
        type(self).objects.filter(pk=self.pk).update(
            usage_count=F("usage_count") + increment,
            last_used_at=timezone.now()
        )

    def revoke(self, reason: str = ""):
        """Revoke this API key with an optional reason"""
        self.status = self.Status.REVOKED
        self.revoked_reason = reason
        self.save(update_fields=['status', 'revoked_reason'])


class APIKeyUsageLog(models.Model):
    """
    Detailed logging of API key usage for analytics and security auditing.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    api_key = models.ForeignKey(
        APIKey, 
        on_delete=models.CASCADE,
        related_name="usage_logs"
    )
    
    # Request details
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    
    # Response details
    status_code = models.PositiveSmallIntegerField()
    response_time_ms = models.PositiveIntegerField(help_text="Response time in milliseconds")
    
    # Usage metrics
    tokens_used = models.PositiveIntegerField(default=0, help_text="LLM tokens consumed")
    documents_searched = models.PositiveSmallIntegerField(default=0)
    
    # Additional context
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['api_key', '-timestamp']),
            models.Index(fields=['endpoint', '-timestamp']),
            models.Index(fields=['ip_address', '-timestamp']),
            models.Index(fields=['-timestamp']),
        ]
        verbose_name = "API Key Usage Log"
        verbose_name_plural = "API Key Usage Logs"

    def __str__(self):
        return f"{self.api_key.name} - {self.method} {self.endpoint} at {self.timestamp}"

