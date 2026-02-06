"""
gRPC Service for Knowledge domain.

Provides gRPC endpoints for Document and Search operations.
This service will be the primary interface for the Knowledge microservice.
"""
import logging
from typing import List
from uuid import UUID

from django.conf import settings
from django_socio_grpc import generics, mixins
from django_socio_grpc.decorators import grpc_action

from apps.documents.models import Document, DocumentChunk

from common.grpc.serializers.knowledge import (
    DocumentProtoSerializer,
    DocumentCreateProtoSerializer,
    DocumentChunkProtoSerializer,
    SemanticSearchRequestSerializer,
    SemanticSearchResponseSerializer,
    TriggerProcessingRequestSerializer,
    TriggerProcessingResponseSerializer,
)

logger = logging.getLogger(__name__)


class DocumentGRPCService(
    mixins.AsyncListModelMixin,
    mixins.AsyncRetrieveModelMixin,
    mixins.AsyncCreateModelMixin,
    mixins.AsyncDestroyModelMixin,
    generics.GenericService,
):
    """
    gRPC Service for Document operations.
    
    Provides CRUD operations for documents and document-related queries.
    Used by Chat service for document retrieval.
    """
    queryset = Document.objects.all()
    serializer_class = DocumentProtoSerializer
    lookup_field = 'id'
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'Create':
            return DocumentCreateProtoSerializer
        return DocumentProtoSerializer
    
    @grpc_action(
        request=[{"name": "organization_id", "type": "string"}],
        response=DocumentProtoSerializer,
        response_stream=True,
    )
    async def ListByOrganization(self, request, context):
        """
        List all documents for an organization.
        
        Streams documents for efficient handling.
        """
        org_id = UUID(request.organization_id)
        async for doc in Document.objects.filter(organization_id=org_id).aiterator():
            serializer = DocumentProtoSerializer(doc)
            yield serializer.message
    
    @grpc_action(
        request=[
            {"name": "document_ids", "type": "repeated string"},
        ],
        response=DocumentProtoSerializer,
        response_stream=True,
    )
    async def ListByIds(self, request, context):
        """
        List documents by their IDs.
        
        Used by Chat service to retrieve connected documents.
        """
        doc_ids = [UUID(uid) for uid in request.document_ids]
        async for doc in Document.objects.filter(id__in=doc_ids).aiterator():
            serializer = DocumentProtoSerializer(doc)
            yield serializer.message
    
    @grpc_action(
        request=[{"name": "document_id", "type": "string"}],
        response=[{"name": "exists", "type": "bool"}, {"name": "status", "type": "string"}],
    )
    async def Exists(self, request, context):
        """
        Check if a document exists and return its status.
        
        Lightweight existence check for validation.
        """
        try:
            doc_id = UUID(request.document_id)
            doc = await Document.objects.filter(id=doc_id).afirst()
            
            if doc:
                return {
                    "exists": True,
                    "status": doc.status,
                }
            return {
                "exists": False,
                "status": "",
            }
        except ValueError:
            return {
                "exists": False,
                "status": "",
            }
    
    @grpc_action(
        request=TriggerProcessingRequestSerializer,
        response=TriggerProcessingResponseSerializer,
    )
    async def TriggerProcessing(self, request, context):
        """
        Trigger document processing (chunking, embedding).
        
        Enqueues a Celery task for document processing.
        """
        try:
            from apps.documents.tasks import process_document
            
            doc_id = UUID(str(request.document_id))
            doc = await Document.objects.filter(id=doc_id).afirst()
            
            if not doc:
                return {
                    "success": False,
                    "task_id": None,
                    "message": f"Document {request.document_id} not found",
                }
            
            # Check if already processing
            if doc.status == Document.Status.PROCESSING and not request.force_reprocess:
                return {
                    "success": False,
                    "task_id": None,
                    "message": "Document is already being processed",
                }
            
            # Update status to processing
            doc.status = Document.Status.PROCESSING
            await doc.asave()
            
            # Trigger Celery task
            task = process_document.delay(str(doc_id))
            
            return {
                "success": True,
                "task_id": task.id,
                "message": "Document processing started",
            }
        except Exception as e:
            logger.error(f"Error triggering document processing: {str(e)}")
            return {
                "success": False,
                "task_id": None,
                "message": str(e),
            }


class DocumentChunkGRPCService(
    mixins.AsyncListModelMixin,
    mixins.AsyncRetrieveModelMixin,
    generics.GenericService,
):
    """
    gRPC Service for DocumentChunk operations.
    
    Provides read access to document chunks.
    """
    queryset = DocumentChunk.objects.all()
    serializer_class = DocumentChunkProtoSerializer
    lookup_field = 'id'
    
    @grpc_action(
        request=[{"name": "document_id", "type": "string"}],
        response=DocumentChunkProtoSerializer,
        response_stream=True,
    )
    async def ListByDocument(self, request, context):
        """
        List all chunks for a document.
        
        Streams chunks in order by chunk_index.
        """
        doc_id = UUID(request.document_id)
        async for chunk in DocumentChunk.objects.filter(
            document_id=doc_id
        ).order_by('chunk_index').aiterator():
            serializer = DocumentChunkProtoSerializer(chunk)
            yield serializer.message


class SearchGRPCService(generics.GenericService):
    """
    gRPC Service for semantic search operations.
    
    Provides vector similarity search across documents.
    """
    
    @grpc_action(
        request=SemanticSearchRequestSerializer,
        response=SemanticSearchResponseSerializer,
    )
    async def SemanticSearch(self, request, context):
        """
        Perform semantic similarity search across documents.
        
        Uses pgvector for efficient vector similarity search.
        """
        try:
            from common.llm.embeddings import get_embedding
            from pgvector.django import CosineDistance
            
            # Generate embedding for query
            query_embedding = get_embedding(request.query)
            
            # Build base queryset
            queryset = DocumentChunk.objects.select_related('document')
            
            # Filter by organization
            org_id = UUID(str(request.organization_id))
            queryset = queryset.filter(document__organization_id=org_id)
            
            # Filter by specific documents if provided
            if request.document_ids:
                doc_ids = [UUID(str(uid)) for uid in request.document_ids]
                queryset = queryset.filter(document_id__in=doc_ids)
            
            # Perform vector similarity search
            queryset = queryset.annotate(
                distance=CosineDistance('embedding', query_embedding)
            ).filter(
                distance__lt=1 - request.similarity_threshold
            ).order_by('distance')[:request.top_k]
            
            # Build results
            results = []
            async for chunk in queryset.aiterator():
                similarity = 1 - chunk.distance  # Convert distance to similarity
                results.append({
                    "chunk_id": str(chunk.id),
                    "document_id": str(chunk.document_id),
                    "document_name": chunk.document.name,
                    "content": chunk.content,
                    "chunk_index": chunk.chunk_index,
                    "similarity_score": similarity,
                })
            
            return {
                "results": results,
                "total_count": len(results),
                "query": request.query,
            }
        except Exception as e:
            logger.error(f"Semantic search error: {str(e)}")
            return {
                "results": [],
                "total_count": 0,
                "query": request.query,
            }
