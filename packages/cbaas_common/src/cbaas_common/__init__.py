"""
CBaaS Common - Shared utilities for CBaaS microservices.

This package provides:
- Event schemas and publishing
- Exception handling utilities
- Logging configuration
- Model mixins
- Common validators
"""

__version__ = "0.1.0"

from cbaas_common.events.base import BaseEvent
from cbaas_common.events.publisher import EventPublisher

__all__ = [
    "__version__",
    "BaseEvent",
    "EventPublisher",
]
