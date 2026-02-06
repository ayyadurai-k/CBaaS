"""Base event class for all domain events."""
from abc import ABC
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field
import uuid


class BaseEvent(BaseModel, ABC):
    """
    Base class for all domain events.
    
    Events are immutable records of something that happened in the system.
    They are used for async communication between services.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = Field(default="base_event")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_service: str = Field(default="unknown")
    correlation_id: str | None = Field(default=None)
    
    class Config:
        frozen = True  # Events are immutable
    
    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return self.model_dump(mode="json")
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BaseEvent":
        """Create event from dictionary."""
        return cls.model_validate(data)
