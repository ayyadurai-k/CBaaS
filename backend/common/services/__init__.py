"""
Service interfaces for cross-service communication.

In Phase 1 (Modular Monolith), these use Django ORM directly.
In Phase 2+, they will make HTTP/gRPC calls to external services.
"""
from common.services.identity import (
    get_identity_service,
    set_identity_service,
    IdentityServiceInterface,
    LocalIdentityService,
    UserData,
    OrganizationData,
    APIKeyData,
)
from common.services.chat import (
    get_chat_service,
    set_chat_service,
    ChatServiceInterface,
    LocalChatService,
    ChatbotData,
    ChatSessionData,
)
from common.services.knowledge import (
    get_knowledge_service,
    set_knowledge_service,
    KnowledgeServiceInterface,
    LocalKnowledgeService,
    DocumentData,
    SearchResult,
)

__all__ = [
    # Identity Service
    "get_identity_service",
    "set_identity_service",
    "IdentityServiceInterface",
    "LocalIdentityService",
    "UserData",
    "OrganizationData",
    "APIKeyData",
    # Chat Service
    "get_chat_service",
    "set_chat_service",
    "ChatServiceInterface",
    "LocalChatService",
    "ChatbotData",
    "ChatSessionData",
    # Knowledge Service
    "get_knowledge_service",
    "set_knowledge_service",
    "KnowledgeServiceInterface",
    "LocalKnowledgeService",
    "DocumentData",
    "SearchResult",
]
