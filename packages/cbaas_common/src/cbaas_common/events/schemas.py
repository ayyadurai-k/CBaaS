"""Domain event schemas for CBaaS services."""
from pydantic import Field
from cbaas_common.events.base import BaseEvent


# ============================================================
# Knowledge Service Events
# ============================================================

class DocumentUploadedEvent(BaseEvent):
    """Fired when a document is uploaded and needs processing."""
    event_type: str = Field(default="document.uploaded")
    source_service: str = Field(default="knowledge")
    
    document_id: str
    organization_id: str
    file_name: str
    file_type: str
    size_bytes: int


class DocumentProcessedEvent(BaseEvent):
    """Fired when document processing (chunking, embedding) is complete."""
    event_type: str = Field(default="document.processed")
    source_service: str = Field(default="knowledge")
    
    document_id: str
    organization_id: str
    status: str  # "ready" or "failed"
    chunk_count: int = 0
    error_message: str | None = None


class DocumentDeletedEvent(BaseEvent):
    """Fired when a document is deleted."""
    event_type: str = Field(default="document.deleted")
    source_service: str = Field(default="knowledge")
    
    document_id: str
    organization_id: str


# ============================================================
# Identity Service Events
# ============================================================

class UserCreatedEvent(BaseEvent):
    """Fired when a new user is created."""
    event_type: str = Field(default="user.created")
    source_service: str = Field(default="identity")
    
    user_id: str
    organization_id: str | None
    email: str
    role: str


class UserDeletedEvent(BaseEvent):
    """Fired when a user is deleted. Other services should clean up related data."""
    event_type: str = Field(default="user.deleted")
    source_service: str = Field(default="identity")
    
    user_id: str
    organization_id: str | None
    email: str


class OrganizationUpdatedEvent(BaseEvent):
    """Fired when organization settings change."""
    event_type: str = Field(default="organization.updated")
    source_service: str = Field(default="identity")
    
    organization_id: str
    name: str
    updated_fields: list[str] = Field(default_factory=list)


class OrganizationDeletedEvent(BaseEvent):
    """Fired when an organization is deleted. Cascade cleanup required."""
    event_type: str = Field(default="organization.deleted")
    source_service: str = Field(default="identity")
    
    organization_id: str


# ============================================================
# Chat Service Events
# ============================================================

class ChatbotCreatedEvent(BaseEvent):
    """Fired when a new chatbot is created."""
    event_type: str = Field(default="chatbot.created")
    source_service: str = Field(default="chat")
    
    chatbot_id: str
    organization_id: str
    name: str


class ChatbotDeletedEvent(BaseEvent):
    """Fired when a chatbot is deleted."""
    event_type: str = Field(default="chatbot.deleted")
    source_service: str = Field(default="chat")
    
    chatbot_id: str
    organization_id: str


class ChatSessionStartedEvent(BaseEvent):
    """Fired when a new chat session begins."""
    event_type: str = Field(default="chat.session_started")
    source_service: str = Field(default="chat")
    
    session_id: str
    chatbot_id: str
    user_id: str | None  # None for anonymous API access
