"""
Chat Service Interface

This interface abstracts access to Chatbot and Chat Session data.
In Phase 1 (Modular Monolith), it uses Django ORM directly.
In Phase 2+, it will make HTTP calls to the Chat Service.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class ChatbotData:
    """Chatbot data returned by the Chat Service."""
    id: str
    organization_id: str
    name: str
    tone: str
    system_instructions: str
    llm_provider: Optional[str]
    llm_model: Optional[str]
    llm_is_active: bool


@dataclass
class ChatSessionData:
    """Chat session data returned by the Chat Service."""
    id: str
    chatbot_id: str
    user_id: Optional[str]
    created_at: str
    message_count: int


class ChatServiceInterface(ABC):
    """Abstract interface for Chat Service operations."""
    
    @abstractmethod
    def get_chatbot(self, chatbot_id: str) -> Optional[ChatbotData]:
        """Fetch a chatbot by ID."""
        pass
    
    @abstractmethod
    def get_chatbots_by_organization(self, organization_id: str) -> list[ChatbotData]:
        """Fetch all chatbots for an organization."""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[ChatSessionData]:
        """Fetch a chat session by ID."""
        pass
    
    @abstractmethod
    def chatbot_exists(self, chatbot_id: str) -> bool:
        """Check if a chatbot exists."""
        pass


class LocalChatService(ChatServiceInterface):
    """
    Local implementation using Django ORM.
    Used in Phase 1 (Modular Monolith).
    """
    
    def get_chatbot(self, chatbot_id: str) -> Optional[ChatbotData]:
        """Fetch a chatbot by ID using Django ORM."""
        from apps.chatbot.models import Chatbot
        
        try:
            chatbot = Chatbot.objects.get(id=chatbot_id)
            return ChatbotData(
                id=str(chatbot.id),
                organization_id=str(chatbot.organization_id),
                name=chatbot.name,
                tone=chatbot.tone,
                system_instructions=chatbot.system_instructions,
                llm_provider=chatbot.llm_provider,
                llm_model=chatbot.llm_model,
                llm_is_active=chatbot.llm_is_active,
            )
        except Chatbot.DoesNotExist:
            logger.warning(f"Chatbot not found: {chatbot_id}")
            return None
    
    def get_chatbots_by_organization(self, organization_id: str) -> list[ChatbotData]:
        """Fetch all chatbots for an organization."""
        from apps.chatbot.models import Chatbot
        
        chatbots = Chatbot.objects.filter(organization_id=organization_id)
        return [
            ChatbotData(
                id=str(chatbot.id),
                organization_id=str(chatbot.organization_id),
                name=chatbot.name,
                tone=chatbot.tone,
                system_instructions=chatbot.system_instructions,
                llm_provider=chatbot.llm_provider,
                llm_model=chatbot.llm_model,
                llm_is_active=chatbot.llm_is_active,
            )
            for chatbot in chatbots
        ]
    
    def get_session(self, session_id: str) -> Optional[ChatSessionData]:
        """Fetch a chat session by ID."""
        # Note: ChatSession model doesn't exist yet in the codebase
        # This is a placeholder for when it's implemented
        logger.warning("ChatSession model not implemented yet")
        return None
    
    def chatbot_exists(self, chatbot_id: str) -> bool:
        """Check if a chatbot exists."""
        from apps.chatbot.models import Chatbot
        return Chatbot.objects.filter(id=chatbot_id).exists()


# Singleton instance
_chat_service: Optional[ChatServiceInterface] = None


def get_chat_service() -> ChatServiceInterface:
    """Get the Chat Service instance."""
    global _chat_service
    if _chat_service is None:
        _chat_service = LocalChatService()
    return _chat_service


def set_chat_service(service: ChatServiceInterface) -> None:
    """Set a custom Chat Service instance (for testing or Phase 2)."""
    global _chat_service
    _chat_service = service
