"""
gRPC Services module for CBaaS microservices.

Exports all gRPC services organized by domain.
"""
from common.grpc.services.identity import (
    UserGRPCService,
    OrganizationGRPCService,
    APIKeyGRPCService,
)

from common.grpc.services.chat import (
    ChatbotGRPCService,
)

from common.grpc.services.knowledge import (
    DocumentGRPCService,
    DocumentChunkGRPCService,
    SearchGRPCService,
)

__all__ = [
    # Identity domain
    'UserGRPCService',
    'OrganizationGRPCService',
    'APIKeyGRPCService',
    # Chat domain
    'ChatbotGRPCService',
    # Knowledge domain
    'DocumentGRPCService',
    'DocumentChunkGRPCService',
    'SearchGRPCService',
]
