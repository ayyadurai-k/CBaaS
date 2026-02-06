"""Event system for decoupled microservice communication."""
from cbaas_common.events.base import BaseEvent
from cbaas_common.events.schemas import (
    DocumentUploadedEvent,
    DocumentProcessedEvent,
    UserDeletedEvent,
    OrganizationUpdatedEvent,
)
from cbaas_common.events.publisher import EventPublisher

__all__ = [
    "BaseEvent",
    "DocumentUploadedEvent",
    "DocumentProcessedEvent",
    "UserDeletedEvent",
    "OrganizationUpdatedEvent",
    "EventPublisher",
]
