"""
Event publisher for local and distributed event handling.

In Phase 1 (Modular Monolith), this uses local in-memory handlers.
In Phase 2+, this will be upgraded to use RabbitMQ/Redis Pub-Sub.
"""
import logging
from typing import Callable, Type
from collections import defaultdict
from cbaas_common.events.base import BaseEvent

logger = logging.getLogger(__name__)

# Type alias for event handlers
EventHandler = Callable[[BaseEvent], None]


class EventPublisher:
    """
    Local event publisher for the modular monolith phase.
    
    Usage:
        publisher = EventPublisher()
        
        # Register handlers
        @publisher.subscribe(DocumentUploadedEvent)
        def handle_document_uploaded(event: DocumentUploadedEvent):
            # Process the event
            pass
        
        # Publish events
        publisher.publish(DocumentUploadedEvent(
            document_id="123",
            organization_id="456",
            file_name="doc.pdf",
            file_type="pdf",
            size_bytes=1024
        ))
    """
    
    _instance: "EventPublisher | None" = None
    
    def __new__(cls) -> "EventPublisher":
        """Singleton pattern to ensure one event bus per application."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._handlers = defaultdict(list)
            cls._instance._async_mode = False
        return cls._instance
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
    
    def subscribe(
        self, 
        event_type: Type[BaseEvent]
    ) -> Callable[[EventHandler], EventHandler]:
        """
        Decorator to subscribe a handler to an event type.
        
        Args:
            event_type: The event class to subscribe to
            
        Returns:
            Decorator function
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self._handlers[event_type.__name__].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to {event_type.__name__}")
            return handler
        return decorator
    
    def register_handler(
        self, 
        event_type: Type[BaseEvent], 
        handler: EventHandler
    ) -> None:
        """
        Programmatically register a handler for an event type.
        
        Args:
            event_type: The event class to handle
            handler: The handler function
        """
        self._handlers[event_type.__name__].append(handler)
        logger.debug(f"Registered handler for {event_type.__name__}")
    
    def publish(self, event: BaseEvent) -> None:
        """
        Publish an event to all registered handlers.
        
        In the modular monolith phase, handlers are called synchronously.
        In the microservices phase, this will publish to a message broker.
        
        Args:
            event: The event to publish
        """
        event_type_name = type(event).__name__
        handlers = self._handlers.get(event_type_name, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for {event_type_name}")
            return
        
        logger.info(
            f"Publishing {event_type_name}",
            extra={"event_id": event.event_id, "event_type": event.event_type}
        )
        
        for handler in handlers:
            try:
                handler(event)
                logger.debug(f"Handler {handler.__name__} processed {event_type_name}")
            except Exception as e:
                logger.error(
                    f"Handler {handler.__name__} failed for {event_type_name}: {e}",
                    exc_info=True
                )
                # In production, you might want to:
                # - Retry the handler
                # - Send to a dead-letter queue
                # - Alert on repeated failures
    
    def get_handlers(self, event_type: Type[BaseEvent]) -> list[EventHandler]:
        """Get all handlers for an event type."""
        return self._handlers.get(event_type.__name__, [])
    
    def clear_handlers(self, event_type: Type[BaseEvent] | None = None) -> None:
        """
        Clear handlers for a specific event type or all handlers.
        
        Args:
            event_type: If provided, clear only handlers for this type.
                       If None, clear all handlers.
        """
        if event_type:
            self._handlers[event_type.__name__] = []
        else:
            self._handlers.clear()


# Global event publisher instance
event_publisher = EventPublisher()
