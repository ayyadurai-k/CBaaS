"""
Knowledge Service Interface

This interface abstracts access to Document and Search functionality.
In Phase 1 (Modular Monolith), it uses Django ORM directly.
In Phase 2+, it will make HTTP calls to the Knowledge Service.
"""
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocumentData:
    """Document data returned by the Knowledge Service."""
    id: str
    organization_id: str
    name: str
    file_type: str
    size_bytes: int
    status: str
    url: str
    upload_date: str


@dataclass
class SearchResult:
    """Search result from semantic search."""
    document_id: str
    document_name: str
    chunk_content: str
    chunk_index: int
    similarity_score: float


class KnowledgeServiceInterface(ABC):
    """Abstract interface for Knowledge Service operations."""
    
    @abstractmethod
    def get_document(self, document_id: str) -> Optional[DocumentData]:
        """Fetch a document by ID."""
        pass
    
    @abstractmethod
    def get_documents_by_organization(self, organization_id: str) -> list[DocumentData]:
        """Fetch all documents for an organization."""
        pass
    
    @abstractmethod
    def get_documents_by_chatbot(self, chatbot_id: str) -> list[DocumentData]:
        """Fetch all documents connected to a chatbot."""
        pass
    
    @abstractmethod
    def semantic_search(
        self, 
        query: str, 
        organization_id: str,
        document_ids: Optional[list[str]] = None,
        top_k: int = 5
    ) -> list[SearchResult]:
        """Perform semantic search across documents."""
        pass
    
    @abstractmethod
    def trigger_document_processing(self, document_id: str) -> bool:
        """Trigger async processing of a document."""
        pass


class LocalKnowledgeService(KnowledgeServiceInterface):
    """
    Local implementation using Django ORM.
    Used in Phase 1 (Modular Monolith).
    """
    
    def get_document(self, document_id: str) -> Optional[DocumentData]:
        """Fetch a document by ID using Django ORM."""
        from apps.documents.models import Document
        
        try:
            doc = Document.objects.get(id=document_id)
            return DocumentData(
                id=str(doc.id),
                organization_id=str(doc.organization_id),
                name=doc.name,
                file_type=doc.file_type,
                size_bytes=doc.size_bytes,
                status=doc.status,
                url=doc.url,
                upload_date=doc.upload_date.isoformat(),
            )
        except Document.DoesNotExist:
            logger.warning(f"Document not found: {document_id}")
            return None
    
    def get_documents_by_organization(self, organization_id: str) -> list[DocumentData]:
        """Fetch all documents for an organization."""
        from apps.documents.models import Document
        
        docs = Document.objects.filter(organization_id=organization_id)
        return [
            DocumentData(
                id=str(doc.id),
                organization_id=str(doc.organization_id),
                name=doc.name,
                file_type=doc.file_type,
                size_bytes=doc.size_bytes,
                status=doc.status,
                url=doc.url,
                upload_date=doc.upload_date.isoformat(),
            )
            for doc in docs
        ]
    
    def get_documents_by_chatbot(self, chatbot_id: str) -> list[DocumentData]:
        """Fetch all documents connected to a chatbot."""
        from apps.chatbot.models import Chatbot
        
        try:
            chatbot = Chatbot.objects.prefetch_related('documents_connected').get(id=chatbot_id)
            return [
                DocumentData(
                    id=str(doc.id),
                    organization_id=str(doc.organization_id),
                    name=doc.name,
                    file_type=doc.file_type,
                    size_bytes=doc.size_bytes,
                    status=doc.status,
                    url=doc.url,
                    upload_date=doc.upload_date.isoformat(),
                )
                for doc in chatbot.documents_connected.all()
            ]
        except Chatbot.DoesNotExist:
            logger.warning(f"Chatbot not found: {chatbot_id}")
            return []
    
    def semantic_search(
        self, 
        query: str, 
        organization_id: str,
        document_ids: Optional[list[str]] = None,
        top_k: int = 5
    ) -> list[SearchResult]:
        """Perform semantic search across documents."""
        from apps.documents.models import DocumentChunk
        from common.llm.embeddings import get_embedding
        from pgvector.django import CosineDistance
        
        # Generate embedding for query
        query_embedding = get_embedding(query)
        
        # Build queryset
        queryset = DocumentChunk.objects.select_related('document').filter(
            document__organization_id=organization_id,
            document__status='ready',
        )
        
        if document_ids:
            queryset = queryset.filter(document_id__in=document_ids)
        
        # Perform vector similarity search
        results = queryset.annotate(
            distance=CosineDistance('embedding', query_embedding)
        ).order_by('distance')[:top_k]
        
        return [
            SearchResult(
                document_id=str(chunk.document_id),
                document_name=chunk.document.name,
                chunk_content=chunk.content,
                chunk_index=chunk.chunk_index,
                similarity_score=1 - chunk.distance,  # Convert distance to similarity
            )
            for chunk in results
        ]
    
    def trigger_document_processing(self, document_id: str) -> bool:
        """Trigger async processing of a document using Celery."""
        from apps.documents.tasks import process_document
        
        try:
            process_document.delay(str(document_id))
            logger.info(f"Triggered processing for document: {document_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to trigger processing for document {document_id}: {e}")
            return False


# Singleton instance
_knowledge_service: Optional[KnowledgeServiceInterface] = None


def get_knowledge_service() -> KnowledgeServiceInterface:
    """Get the Knowledge Service instance."""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = LocalKnowledgeService()
    return _knowledge_service


def set_knowledge_service(service: KnowledgeServiceInterface) -> None:
    """Set a custom Knowledge Service instance (for testing or Phase 2)."""
    global _knowledge_service
    _knowledge_service = service
