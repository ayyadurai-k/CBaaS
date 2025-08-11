import uuid, hashlib, secrets
from django.db import models
from django.utils import timezone
from apps.users.models import User


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)  # sha256
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    @staticmethod
    def issue(user, ttl_seconds: int = 3600):
        raw = secrets.token_urlsafe(48)
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        obj = PasswordResetToken.objects.create(
            user=user,
            token=token_hash,
            expires_at=timezone.now() + timezone.timedelta(seconds=ttl_seconds),
        )
        return raw, obj

    def matches(self, raw: str) -> bool:
        return hashlib.sha256(raw.encode()).hexdigest() == self.token
