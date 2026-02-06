"""
Proto Serializers module for gRPC services.

Exports all proto serializers organized by service domain.
"""
from common.grpc.serializers.identity import (
    UserProtoSerializer,
    UserCreateProtoSerializer,
    OrganizationProtoSerializer,
    OrganizationCreateProtoSerializer,
    ValidateAPIKeyRequestSerializer,
    ValidateAPIKeyResponseSerializer,
)

from common.grpc.serializers.chat import (
    ChatbotProtoSerializer,
    ChatbotCreateProtoSerializer,
    ChatbotUpdateProtoSerializer,
    ChatbotExistsRequestSerializer,
    ChatbotExistsResponseSerializer,
    ConnectDocumentRequestSerializer,
    ConnectDocumentResponseSerializer,
)

from common.grpc.serializers.knowledge import (
    DocumentProtoSerializer,
    DocumentCreateProtoSerializer,
    DocumentChunkProtoSerializer,
    SemanticSearchRequestSerializer,
    SearchResultSerializer,
    SemanticSearchResponseSerializer,
    TriggerProcessingRequestSerializer,
    TriggerProcessingResponseSerializer,
)

__all__ = [
    # Identity
    'UserProtoSerializer',
    'UserCreateProtoSerializer', 
    'OrganizationProtoSerializer',
    'OrganizationCreateProtoSerializer',
    'ValidateAPIKeyRequestSerializer',
    'ValidateAPIKeyResponseSerializer',
    # Chat
    'ChatbotProtoSerializer',
    'ChatbotCreateProtoSerializer',
    'ChatbotUpdateProtoSerializer',
    'ChatbotExistsRequestSerializer',
    'ChatbotExistsResponseSerializer',
    'ConnectDocumentRequestSerializer',
    'ConnectDocumentResponseSerializer',
    # Knowledge
    'DocumentProtoSerializer',
    'DocumentCreateProtoSerializer',
    'DocumentChunkProtoSerializer',
    'SemanticSearchRequestSerializer',
    'SearchResultSerializer',
    'SemanticSearchResponseSerializer',
    'TriggerProcessingRequestSerializer',
    'TriggerProcessingResponseSerializer',
]
