"""
gRPC Service for Chat domain.

Provides gRPC endpoints for Chatbot operations.
This service will be the primary interface for the Chat microservice.
"""
import logging
from typing import List
from uuid import UUID

from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action

from apps.chatbot.models import Chatbot

from common.grpc.serializers.chat import (
    ChatbotProtoSerializer,
    ChatbotCreateProtoSerializer,
    ChatbotUpdateProtoSerializer,
    ChatbotExistsRequestSerializer,
    ChatbotExistsResponseSerializer,
    ConnectDocumentRequestSerializer,
    ConnectDocumentResponseSerializer,
)

logger = logging.getLogger(__name__)


class ChatbotGRPCService(
    mixins.AsyncListModelMixin,
    mixins.AsyncRetrieveModelMixin,
    mixins.AsyncCreateModelMixin,
    mixins.AsyncUpdateModelMixin,
    mixins.AsyncDestroyModelMixin,
    generics.GenericService,
):
    """
    gRPC Service for Chatbot operations.
    
    Provides CRUD operations for chatbots and chatbot-related queries.
    Used by Knowledge service for document-chatbot connections.
    """
    queryset = Chatbot.objects.all()
    serializer_class = ChatbotProtoSerializer
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'Create':
            return ChatbotCreateProtoSerializer
        elif self.action in ['Update', 'PartialUpdate']:
            return ChatbotUpdateProtoSerializer
        return ChatbotProtoSerializer
    
    @grpc_action(
        request=[{"name": "organization_id", "type": "string"}],
        response=ChatbotProtoSerializer,
        response_stream=True,
    )
    async def ListByOrganization(self, request, context):
        """
        List all chatbots for an organization.
        
        Streams chatbots for efficient handling.
        """
        org_id = UUID(request.organization_id)
        async for chatbot in Chatbot.objects.filter(organization_id=org_id).aiterator():
            serializer = ChatbotProtoSerializer(chatbot)
            yield serializer.message
    
    @grpc_action(
        request=ChatbotExistsRequestSerializer,
        response=ChatbotExistsResponseSerializer,
    )
    async def Exists(self, request, context):
        """
        Check if a chatbot exists and return its active status.
        
        Lightweight existence check for validation.
        """
        try:
            chatbot_id = UUID(str(request.chatbot_id))
            chatbot = await Chatbot.objects.filter(id=chatbot_id).afirst()
            
            if chatbot:
                return {
                    "exists": True,
                    "is_active": chatbot.is_active,
                }
            return {
                "exists": False,
                "is_active": False,
            }
        except ValueError:
            return {
                "exists": False,
                "is_active": False,
            }
    
    @grpc_action(
        request=ConnectDocumentRequestSerializer,
        response=ConnectDocumentResponseSerializer,
    )
    async def ConnectDocuments(self, request, context):
        """
        Connect documents to a chatbot.
        
        Updates the chatbot's connected_document_ids list.
        Called by Knowledge service when documents are ready.
        """
        try:
            chatbot_id = UUID(str(request.chatbot_id))
            chatbot = await Chatbot.objects.aget(id=chatbot_id)
            
            # Get current document IDs
            current_ids = set(str(uid) for uid in (chatbot.connected_document_ids or []))
            
            # Add new document IDs
            new_ids = [str(uid) for uid in request.document_ids]
            current_ids.update(new_ids)
            
            # Update chatbot
            chatbot.connected_document_ids = list(current_ids)
            await chatbot.asave()
            
            return {
                "success": True,
                "connected_count": len(chatbot.connected_document_ids),
                "message": f"Successfully connected {len(new_ids)} documents",
            }
        except Chatbot.DoesNotExist:
            return {
                "success": False,
                "connected_count": 0,
                "message": f"Chatbot {request.chatbot_id} not found",
            }
        except Exception as e:
            logger.error(f"Error connecting documents: {str(e)}")
            return {
                "success": False,
                "connected_count": 0,
                "message": str(e),
            }
    
    @grpc_action(
        request=[
            {"name": "chatbot_id", "type": "string"},
            {"name": "document_ids", "type": "repeated string"},
        ],
        response=ConnectDocumentResponseSerializer,
    )
    async def DisconnectDocuments(self, request, context):
        """
        Disconnect documents from a chatbot.
        
        Removes document IDs from the chatbot's connected list.
        """
        try:
            chatbot_id = UUID(request.chatbot_id)
            chatbot = await Chatbot.objects.aget(id=chatbot_id)
            
            # Get current document IDs
            current_ids = set(str(uid) for uid in (chatbot.connected_document_ids or []))
            
            # Remove specified document IDs
            remove_ids = set(request.document_ids)
            current_ids -= remove_ids
            
            # Update chatbot
            chatbot.connected_document_ids = list(current_ids)
            await chatbot.asave()
            
            return {
                "success": True,
                "connected_count": len(chatbot.connected_document_ids),
                "message": f"Successfully disconnected {len(remove_ids)} documents",
            }
        except Chatbot.DoesNotExist:
            return {
                "success": False,
                "connected_count": 0,
                "message": f"Chatbot {request.chatbot_id} not found",
            }
        except Exception as e:
            logger.error(f"Error disconnecting documents: {str(e)}")
            return {
                "success": False,
                "connected_count": 0,
                "message": str(e),
            }
    
    @grpc_action(
        request=[{"name": "document_id", "type": "string"}],
        response=ChatbotProtoSerializer,
        response_stream=True,
    )
    async def ListByDocument(self, request, context):
        """
        List all chatbots connected to a specific document.
        
        Used by Knowledge service to notify chatbots of document changes.
        """
        doc_id = request.document_id
        
        # Find chatbots with this document ID in their connected list
        async for chatbot in Chatbot.objects.all().aiterator():
            if chatbot.connected_document_ids and doc_id in [str(uid) for uid in chatbot.connected_document_ids]:
                serializer = ChatbotProtoSerializer(chatbot)
                yield serializer.message
