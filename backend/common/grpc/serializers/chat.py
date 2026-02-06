"""
Proto Serializers for Chat Service domain.

These serializers handle Chatbot-related gRPC communication.
"""
from django_socio_grpc import proto_serializers
from rest_framework import serializers

from apps.chatbot.models import Chatbot


class ChatbotProtoSerializer(proto_serializers.ModelProtoSerializer):
    """
    Proto serializer for Chatbot model.
    
    Exposes chatbot configuration for cross-service communication.
    """
    connected_document_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Chatbot
        fields = [
            'id',
            'organization_id',
            'name',
            'description',
            'instructions',
            'model_name',
            'temperature',
            'max_tokens',
            'is_active',
            'created_at',
            'updated_at',
            'connected_document_ids',
            'connected_document_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'connected_document_count']
    
    def get_connected_document_count(self, obj) -> int:
        """Return the number of connected documents."""
        if obj.connected_document_ids:
            return len(obj.connected_document_ids)
        return 0


class ChatbotCreateProtoSerializer(proto_serializers.ModelProtoSerializer):
    """Proto serializer for creating chatbots via gRPC."""
    organization_id = serializers.UUIDField()
    connected_document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list
    )
    
    class Meta:
        model = Chatbot
        fields = [
            'name',
            'description',
            'instructions',
            'model_name',
            'temperature',
            'max_tokens',
            'organization_id',
            'connected_document_ids',
        ]


class ChatbotUpdateProtoSerializer(proto_serializers.ModelProtoSerializer):
    """Proto serializer for updating chatbots via gRPC."""
    connected_document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False
    )
    
    class Meta:
        model = Chatbot
        fields = [
            'name',
            'description',
            'instructions',
            'model_name',
            'temperature',
            'max_tokens',
            'is_active',
            'connected_document_ids',
        ]


class ChatbotExistsRequestSerializer(proto_serializers.ProtoSerializer):
    """Request serializer for checking chatbot existence."""
    chatbot_id = serializers.UUIDField()
    
    class Meta:
        fields = ['chatbot_id']


class ChatbotExistsResponseSerializer(proto_serializers.ProtoSerializer):
    """Response serializer for chatbot existence check."""
    exists = serializers.BooleanField()
    is_active = serializers.BooleanField(required=False)
    
    class Meta:
        fields = ['exists', 'is_active']


class ConnectDocumentRequestSerializer(proto_serializers.ProtoSerializer):
    """Request serializer for connecting documents to chatbot."""
    chatbot_id = serializers.UUIDField()
    document_ids = serializers.ListField(child=serializers.UUIDField())
    
    class Meta:
        fields = ['chatbot_id', 'document_ids']


class ConnectDocumentResponseSerializer(proto_serializers.ProtoSerializer):
    """Response serializer for document connection."""
    success = serializers.BooleanField()
    connected_count = serializers.IntegerField()
    message = serializers.CharField(required=False)
    
    class Meta:
        fields = ['success', 'connected_count', 'message']
