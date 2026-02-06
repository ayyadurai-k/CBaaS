"""
gRPC Client utilities for inter-service communication.

This module provides client classes for calling gRPC services
from other services in the microservices architecture.

In the monolith phase, these clients call local gRPC services.
In the microservices phase, they will connect to remote services.
"""
import logging
import os
from typing import Optional, Dict, Any, List
from uuid import UUID

import grpc
from django.conf import settings

logger = logging.getLogger(__name__)


def get_grpc_channel(service_name: str) -> grpc.Channel:
    """
    Get a gRPC channel for the specified service.
    
    In monolith mode, all services are on the same host.
    In microservices mode, each service has its own host.
    
    Args:
        service_name: Name of the service (identity, chat, knowledge)
        
    Returns:
        gRPC Channel to the service
    """
    # Get service address from environment or settings
    env_key = f"GRPC_{service_name.upper()}_ADDRESS"
    default_port = getattr(settings, 'GRPC_FRAMEWORK', {}).get('GRPC_CHANNEL_PORT', 50051)
    
    # In monolith mode, use localhost
    default_address = f"localhost:{default_port}"
    address = os.environ.get(env_key, default_address)
    
    # Create insecure channel for development
    # In production, use secure_channel with credentials
    if os.environ.get('GRPC_USE_TLS', 'false').lower() == 'true':
        # Load TLS credentials
        root_cert_path = os.environ.get('GRPC_ROOT_CERT_PATH')
        if root_cert_path:
            with open(root_cert_path, 'rb') as f:
                root_cert = f.read()
            credentials = grpc.ssl_channel_credentials(root_cert)
            return grpc.secure_channel(address, credentials)
    
    return grpc.insecure_channel(address)


class BaseGRPCClient:
    """
    Base class for gRPC clients.
    
    Provides common functionality like channel management,
    metadata handling, and error handling.
    """
    
    def __init__(self, service_name: str, stub_class: type):
        """
        Initialize the gRPC client.
        
        Args:
            service_name: Name of the service to connect to
            stub_class: gRPC stub class for the service
        """
        self.service_name = service_name
        self.stub_class = stub_class
        self._channel = None
        self._stub = None
    
    @property
    def channel(self) -> grpc.Channel:
        """Get or create the gRPC channel."""
        if self._channel is None:
            self._channel = get_grpc_channel(self.service_name)
        return self._channel
    
    @property
    def stub(self):
        """Get or create the gRPC stub."""
        if self._stub is None:
            self._stub = self.stub_class(self.channel)
        return self._stub
    
    def _get_metadata(self, auth_token: Optional[str] = None) -> List[tuple]:
        """
        Build gRPC metadata for the request.
        
        Args:
            auth_token: Optional JWT token for authentication
            
        Returns:
            List of metadata tuples
        """
        metadata = []
        
        if auth_token:
            metadata.append(('authorization', f'Bearer {auth_token}'))
        
        # Add service-to-service key if available
        service_key = os.environ.get('INTERNAL_SERVICE_KEY')
        if service_key:
            metadata.append(('x-service-key', service_key))
        
        return metadata
    
    def _handle_error(self, error: grpc.RpcError) -> None:
        """
        Handle gRPC errors.
        
        Args:
            error: gRPC RpcError to handle
        """
        code = error.code()
        details = error.details()
        
        logger.error(f"gRPC error calling {self.service_name}: {code} - {details}")
        
        if code == grpc.StatusCode.UNAVAILABLE:
            raise ConnectionError(f"Service {self.service_name} is unavailable")
        elif code == grpc.StatusCode.UNAUTHENTICATED:
            raise PermissionError(f"Authentication failed for {self.service_name}")
        elif code == grpc.StatusCode.NOT_FOUND:
            raise LookupError(details)
        else:
            raise RuntimeError(f"gRPC error: {code} - {details}")
    
    def close(self):
        """Close the gRPC channel."""
        if self._channel:
            self._channel.close()
            self._channel = None
            self._stub = None


class IdentityServiceClient(BaseGRPCClient):
    """
    gRPC client for Identity Service.
    
    Provides methods to interact with User, Organization,
    and API Key services.
    
    Usage:
        client = IdentityServiceClient()
        user = client.get_user(user_id)
        org = client.get_organization(org_id)
        is_valid = client.validate_api_key(api_key)
    """
    
    def __init__(self):
        # Note: In production, import the generated stub class
        # from grpc_generated.identity import identity_pb2_grpc
        # super().__init__('identity', identity_pb2_grpc.UserGRPCServiceStub)
        super().__init__('identity', None)  # Placeholder until proto generation
    
    def get_user(self, user_id: str, auth_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get user by ID.
        
        Args:
            user_id: UUID of the user
            auth_token: Optional JWT token
            
        Returns:
            User data dict or None if not found
        """
        # Implementation will use generated proto classes
        # For now, fall back to direct model access
        from apps.users.models import User
        try:
            user = User.objects.get(id=user_id)
            return {
                'id': str(user.id),
                'email': user.email,
                'name': user.name,
                'role': user.role,
                'is_active': user.is_active,
                'organization_id': str(user.organization_id) if user.organization_id else None,
            }
        except User.DoesNotExist:
            return None
    
    def get_organization(self, org_id: str, auth_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get organization by ID.
        
        Args:
            org_id: UUID of the organization
            auth_token: Optional JWT token
            
        Returns:
            Organization data dict or None if not found
        """
        from apps.organizations.models import Organization
        try:
            org = Organization.objects.get(id=org_id)
            return {
                'id': str(org.id),
                'name': org.name,
                'slug': org.slug,
                'created_at': org.created_at.isoformat(),
                'updated_at': org.updated_at.isoformat(),
            }
        except Organization.DoesNotExist:
            return None
    
    def validate_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Validate an API key.
        
        Args:
            api_key: The API key to validate
            
        Returns:
            Dict with is_valid, organization_id, permissions
        """
        # Implementation will use gRPC
        # For now, fall back to direct validation
        from apps.api_keys.services import validate_api_key as do_validate
        try:
            result = do_validate(api_key)
            return result
        except Exception as e:
            return {
                'is_valid': False,
                'error': str(e),
            }


class ChatServiceClient(BaseGRPCClient):
    """
    gRPC client for Chat Service.
    
    Provides methods to interact with Chatbot services.
    """
    
    def __init__(self):
        super().__init__('chat', None)  # Placeholder until proto generation
    
    def get_chatbot(self, chatbot_id: str, auth_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get chatbot by ID.
        
        Args:
            chatbot_id: UUID of the chatbot
            auth_token: Optional JWT token
            
        Returns:
            Chatbot data dict or None if not found
        """
        from apps.chatbot.models import Chatbot
        try:
            chatbot = Chatbot.objects.get(id=chatbot_id)
            return {
                'id': str(chatbot.id),
                'organization_id': str(chatbot.organization_id),
                'name': chatbot.name,
                'description': chatbot.description,
                'is_active': chatbot.is_active,
                'connected_document_ids': chatbot.connected_document_ids or [],
            }
        except Chatbot.DoesNotExist:
            return None
    
    def chatbot_exists(self, chatbot_id: str) -> bool:
        """
        Check if a chatbot exists.
        
        Args:
            chatbot_id: UUID of the chatbot
            
        Returns:
            True if chatbot exists
        """
        from apps.chatbot.models import Chatbot
        return Chatbot.objects.filter(id=chatbot_id).exists()


class KnowledgeServiceClient(BaseGRPCClient):
    """
    gRPC client for Knowledge Service.
    
    Provides methods to interact with Document and Search services.
    """
    
    def __init__(self):
        super().__init__('knowledge', None)  # Placeholder until proto generation
    
    def get_document(self, document_id: str, auth_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.
        
        Args:
            document_id: UUID of the document
            auth_token: Optional JWT token
            
        Returns:
            Document data dict or None if not found
        """
        from apps.documents.models import Document
        try:
            doc = Document.objects.get(id=document_id)
            return {
                'id': str(doc.id),
                'organization_id': str(doc.organization_id),
                'name': doc.name,
                'file_type': doc.file_type,
                'status': doc.status,
                'url': doc.url,
            }
        except Document.DoesNotExist:
            return None
    
    def semantic_search(
        self,
        query: str,
        organization_id: str,
        document_ids: Optional[List[str]] = None,
        top_k: int = 10,
        similarity_threshold: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search.
        
        Args:
            query: Search query
            organization_id: Organization to search in
            document_ids: Optional list of document IDs to filter
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of search results
        """
        # Implementation will use gRPC
        # For now, fall back to direct search
        from common.services.knowledge import LocalKnowledgeService
        service = LocalKnowledgeService()
        return service.semantic_search(
            query=query,
            organization_id=organization_id,
            document_ids=document_ids,
            top_k=top_k,
        )
    
    def trigger_document_processing(self, document_id: str) -> Dict[str, Any]:
        """
        Trigger document processing.
        
        Args:
            document_id: UUID of the document to process
            
        Returns:
            Dict with success status and task_id
        """
        from apps.documents.tasks import process_document
        try:
            task = process_document.delay(document_id)
            return {
                'success': True,
                'task_id': task.id,
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
            }


# Service client singletons
_identity_client = None
_chat_client = None
_knowledge_client = None


def get_identity_client() -> IdentityServiceClient:
    """Get the Identity service client singleton."""
    global _identity_client
    if _identity_client is None:
        _identity_client = IdentityServiceClient()
    return _identity_client


def get_chat_client() -> ChatServiceClient:
    """Get the Chat service client singleton."""
    global _chat_client
    if _chat_client is None:
        _chat_client = ChatServiceClient()
    return _chat_client


def get_knowledge_client() -> KnowledgeServiceClient:
    """Get the Knowledge service client singleton."""
    global _knowledge_client
    if _knowledge_client is None:
        _knowledge_client = KnowledgeServiceClient()
    return _knowledge_client
