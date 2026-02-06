"""
Model mixins for consistent model structure across services.

These are Pydantic-based mixins for service-to-service DTOs.
For Django models, use Django model mixins in your service.
"""
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class UUIDMixin(BaseModel):
    """Mixin that provides UUID primary key."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))


class TimestampMixin(BaseModel):
    """Mixin that provides created_at and updated_at timestamps."""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BaseModelMixin(UUIDMixin, TimestampMixin):
    """Combined mixin with UUID and timestamps."""
    pass


# ============================================================
# Service DTOs (Data Transfer Objects)
# These are used for cross-service communication
# ============================================================

class UserDTO(BaseModelMixin):
    """User data transfer object for cross-service communication."""
    email: str
    name: str
    role: str
    organization_id: str | None = None
    is_active: bool = True


class OrganizationDTO(BaseModelMixin):
    """Organization data transfer object for cross-service communication."""
    name: str
    slug: str
    logo_url: str | None = None


class ChatbotDTO(BaseModelMixin):
    """Chatbot data transfer object for cross-service communication."""
    name: str
    organization_id: str
    tone: str
    llm_provider: str | None = None
    llm_model: str | None = None
    is_active: bool = True


class DocumentDTO(BaseModelMixin):
    """Document data transfer object for cross-service communication."""
    name: str
    organization_id: str
    file_type: str
    size_bytes: int
    status: str
    url: str
