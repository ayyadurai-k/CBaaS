"""
Proto Serializers for Knowledge Service domain.

These serializers handle Document and Search related gRPC communication.
"""
from django_socio_grpc import proto_serializers
from rest_framework import serializers

from apps.documents.models import Document, DocumentChunk


class DocumentProtoSerializer(proto_serializers.ModelProtoSerializer):
    """
    Proto serializer for Document model.
    
    Exposes document metadata for cross-service communication.
    """
    chunk_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id',
            'organization_id',
            'name',
            'file_type',
            'size_bytes',
            'upload_date',
            'status',
            'url',
            'chunk_count',
        ]
        read_only_fields = ['id', 'upload_date', 'chunk_count']
    
    def get_chunk_count(self, obj) -> int:
        """Return the number of chunks for this document."""
        return obj.chunks.count() if hasattr(obj, 'chunks') else 0


class DocumentCreateProtoSerializer(proto_serializers.ModelProtoSerializer):
    """Proto serializer for creating documents via gRPC."""
    organization_id = serializers.UUIDField()
    
    class Meta:
        model = Document
        fields = [
            'name',
            'file_type',
            'size_bytes',
            'organization_id',
            'url',
        ]


class DocumentChunkProtoSerializer(proto_serializers.ModelProtoSerializer):
    """
    Proto serializer for DocumentChunk model.
    
    Note: Embedding field is excluded as it's too large for gRPC.
    Use semantic search endpoint instead.
    """
    document_id = serializers.UUIDField(source='document.id', read_only=True)
    document_name = serializers.CharField(source='document.name', read_only=True)
    
    class Meta:
        model = DocumentChunk
        fields = [
            'id',
            'document_id',
            'document_name',
            'chunk_index',
            'content',
        ]
        read_only_fields = ['id', 'document_id', 'document_name']


class SemanticSearchRequestSerializer(proto_serializers.ProtoSerializer):
    """Request serializer for semantic search."""
    query = serializers.CharField()
    organization_id = serializers.UUIDField()
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        help_text="Optional: Filter to specific documents"
    )
    top_k = serializers.IntegerField(default=10, min_value=1, max_value=100)
    similarity_threshold = serializers.FloatField(default=0.7, min_value=0.0, max_value=1.0)
    
    class Meta:
        fields = ['query', 'organization_id', 'document_ids', 'top_k', 'similarity_threshold']


class SearchResultSerializer(proto_serializers.ProtoSerializer):
    """Single search result item."""
    chunk_id = serializers.UUIDField()
    document_id = serializers.UUIDField()
    document_name = serializers.CharField()
    content = serializers.CharField()
    chunk_index = serializers.IntegerField()
    similarity_score = serializers.FloatField()
    
    class Meta:
        fields = ['chunk_id', 'document_id', 'document_name', 'content', 'chunk_index', 'similarity_score']


class SemanticSearchResponseSerializer(proto_serializers.ProtoSerializer):
    """Response serializer for semantic search."""
    results = SearchResultSerializer(many=True)
    total_count = serializers.IntegerField()
    query = serializers.CharField()
    
    class Meta:
        fields = ['results', 'total_count', 'query']


class TriggerProcessingRequestSerializer(proto_serializers.ProtoSerializer):
    """Request serializer for triggering document processing."""
    document_id = serializers.UUIDField()
    force_reprocess = serializers.BooleanField(default=False)
    
    class Meta:
        fields = ['document_id', 'force_reprocess']


class TriggerProcessingResponseSerializer(proto_serializers.ProtoSerializer):
    """Response serializer for document processing trigger."""
    success = serializers.BooleanField()
    task_id = serializers.CharField(required=False)
    message = serializers.CharField(required=False)
    
    class Meta:
        fields = ['success', 'task_id', 'message']
