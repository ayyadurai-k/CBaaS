from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import timedelta
from typing import Optional, Tuple

from django.conf import settings
from django.db import IntegrityError, models, transaction
from django.utils import timezone

from apps.users.models import User

logger = logging.getLogger(__name__)


class PasswordResetToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    token = models.CharField(max_length=64, unique=True, db_index=True)  # sha256 hex
    expires_at = models.DateTimeField(db_index=True)
    used = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "used", "created_at"]),
            models.Index(fields=["user", "used", "expires_at"]),
        ]

    @staticmethod
    def issue(
        user: User, ttl_seconds: Optional[int] = None
    ) -> Tuple[str, "PasswordResetToken"]:
        """
        Invalidate older tokens for this user, then create a fresh one.
        Returns (raw_token, token_obj).
        """
        default_ttl = int(getattr(settings, "PASSWORD_RESET_TOKEN_TTL_SECONDS", 3600))
        ttl: int = default_ttl if ttl_seconds is None else int(ttl_seconds)

        with transaction.atomic():
            # Invalidate all prior unused tokens to ensure single valid token per user.
            PasswordResetToken.objects.filter(user=user, used=False).update(used=True)

            # Generate a new unique token; retry on rare hash collision.
            for _ in range(5):
                raw = secrets.token_urlsafe(48)
                token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
                try:
                    obj = PasswordResetToken.objects.create(
                        user=user,
                        token=token_hash,
                        expires_at=timezone.now() + timedelta(seconds=ttl),
                    )
                    return raw, obj
                except IntegrityError:
                    logger.warning("PasswordResetToken hash collision; retrying.")
            # If all retries failed (extremely unlikely), raise.
            raise IntegrityError("Unable to issue a unique password reset token.")

    def matches(self, raw: str) -> bool:
        # constant-time compare
        return secrets.compare_digest(
            hashlib.sha256(raw.encode("utf-8")).hexdigest(), self.token
        )

    def __str__(self) -> str:  # pragma: no cover (debug convenience)
        return f"PasswordResetToken(user={self.user.id}, used={self.used})"
