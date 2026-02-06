"""
gRPC Handlers for CBaaS microservices.

This module registers all gRPC services with the Django Socio gRPC server.
It is referenced by GRPC_FRAMEWORK['ROOT_HANDLERS_HOOK'] in settings.

Each domain (Identity, Chat, Knowledge) has its own handler function
for modular organization.
"""
import logging

from django_socio_grpc.services.app_handler_registry import AppHandlerRegistry

from common.grpc.services import (
    # Identity domain
    UserGRPCService,
    OrganizationGRPCService,
    APIKeyGRPCService,
    # Chat domain
    ChatbotGRPCService,
    # Knowledge domain
    DocumentGRPCService,
    DocumentChunkGRPCService,
    SearchGRPCService,
)

logger = logging.getLogger(__name__)


def identity_handlers(server):
    """
    Register Identity domain gRPC services.
    
    Services:
    - UserGRPCService: User CRUD and queries
    - OrganizationGRPCService: Organization CRUD and queries  
    - APIKeyGRPCService: API key validation
    """
    registry = AppHandlerRegistry("identity", server)
    registry.register(UserGRPCService)
    registry.register(OrganizationGRPCService)
    registry.register(APIKeyGRPCService)
    logger.info("Registered Identity domain gRPC services")


def chat_handlers(server):
    """
    Register Chat domain gRPC services.
    
    Services:
    - ChatbotGRPCService: Chatbot CRUD and document connections
    """
    registry = AppHandlerRegistry("chat", server)
    registry.register(ChatbotGRPCService)
    logger.info("Registered Chat domain gRPC services")


def knowledge_handlers(server):
    """
    Register Knowledge domain gRPC services.
    
    Services:
    - DocumentGRPCService: Document CRUD and processing
    - DocumentChunkGRPCService: Chunk retrieval
    - SearchGRPCService: Semantic search
    """
    registry = AppHandlerRegistry("knowledge", server)
    registry.register(DocumentGRPCService)
    registry.register(DocumentChunkGRPCService)
    registry.register(SearchGRPCService)
    logger.info("Registered Knowledge domain gRPC services")


def grpc_handlers(server):
    """
    Root gRPC handlers hook.
    
    This function is called by Django Socio gRPC to register all
    gRPC services. It is configured in GRPC_FRAMEWORK['ROOT_HANDLERS_HOOK'].
    
    Args:
        server: gRPC server instance to register services with
    """
    logger.info("Initializing CBaaS gRPC services...")
    
    # Register all domain handlers
    identity_handlers(server)
    chat_handlers(server)
    knowledge_handlers(server)
    
    logger.info("CBaaS gRPC services initialized successfully")
