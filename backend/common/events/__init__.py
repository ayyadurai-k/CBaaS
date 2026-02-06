"""
Event handlers for CBaaS.

This module registers all event handlers for the application.
In Phase 1, events are handled synchronously via local event bus.
In Phase 2+, this will be replaced with message broker consumers.
"""
import logging
from cbaas_common.events import (
    EventPublisher,
    DocumentUploadedEvent,
    DocumentProcessedEvent,
    UserDeletedEvent,
    OrganizationUpdatedEvent,
)

logger = logging.getLogger(__name__)

# Get the global event publisher
event_publisher = EventPublisher()


# ============================================================
# Knowledge Service Event Handlers
# ============================================================

@event_publisher.subscribe(DocumentUploadedEvent)
def handle_document_uploaded(event: DocumentUploadedEvent):
    """
    Handle document uploaded event.
    Trigger embedding generation for the document.
    """
    logger.info(
        f"Document uploaded: {event.document_id} ({event.file_name})",
        extra={"event_id": event.event_id, "organization_id": event.organization_id}
    )
    # The actual processing is already triggered by the upload serializer
    # This handler is for additional side effects (logging, notifications, etc.)


@event_publisher.subscribe(DocumentProcessedEvent)
def handle_document_processed(event: DocumentProcessedEvent):
    """
    Handle document processed event.
    Update any caches or notify users.
    """
    if event.status == "ready":
        logger.info(
            f"Document processed successfully: {event.document_id} "
            f"({event.chunk_count} chunks)",
            extra={"event_id": event.event_id}
        )
    else:
        logger.error(
            f"Document processing failed: {event.document_id} - {event.error_message}",
            extra={"event_id": event.event_id}
        )


# ============================================================
# Identity Service Event Handlers
# ============================================================

@event_publisher.subscribe(UserDeletedEvent)
def handle_user_deleted(event: UserDeletedEvent):
    """
    Handle user deleted event.
    Clean up user-related data in Chat and Knowledge services.
    """
    logger.info(
        f"User deleted: {event.user_id} ({event.email})",
        extra={"event_id": event.event_id}
    )
    # TODO: In Phase 2, this would trigger cleanup in other services
    # For now, cascade delete handles most cleanup via FK constraints


@event_publisher.subscribe(OrganizationUpdatedEvent)
def handle_organization_updated(event: OrganizationUpdatedEvent):
    """
    Handle organization updated event.
    Invalidate caches for organization data.
    """
    logger.info(
        f"Organization updated: {event.organization_id} - {event.updated_fields}",
        extra={"event_id": event.event_id}
    )
    # TODO: Invalidate any cached organization data


def register_all_handlers():
    """
    Explicitly register all event handlers.
    Called during Django app initialization.
    """
    # Handlers are already registered via decorators above
    # This function ensures the module is imported
    logger.info("Event handlers registered successfully")


# Auto-register handlers when module is imported
register_all_handlers()
