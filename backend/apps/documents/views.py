import os
import mimetypes
import logging
from urllib.parse import quote
from django.http import HttpResponse, StreamingHttpResponse, Http404
from django.core.files.storage import default_storage
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.documents.models import Document
from common.security.permissions import ReadOnlyOrOwnerAdmin
from common.security.throttles import DocumentsRateThrottle
from apps.documents.serializers import DocumentSerializer, DocumentUploadSerializer
from apps.documents.tasks import process_document

logger = logging.getLogger(__name__)


class DocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DocumentsRateThrottle]  # Apply throttle
    search_fields = ["name", "file_type", "status"]
    ordering_fields = ["upload_date", "name", "size_bytes"]

    def get_queryset(self):
        # Filter documents by user's organization
        return Document.objects.filter(organization=self.request.user.organization)

    def get_serializer_class(self):
        return (
            DocumentUploadSerializer
            if self.request.method == "POST"
            else DocumentSerializer
        )


class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOrOwnerAdmin]
    serializer_class = DocumentSerializer

    def get_queryset(self):
        # Filter documents by user's organization
        return Document.objects.filter(organization=self.request.user.organization)


class DocumentReprocessView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DocumentsRateThrottle]  # Apply throttle

    def post(self, request, pk):
        try:
            doc = Document.objects.get(id=pk, organization=request.user.organization)
        except Document.DoesNotExist:
            return Response(
                {"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND
            )

        doc.status = Document.Status.PROCESSING
        doc.save(update_fields=["status"])
        process_document.delay(str(doc.id))
        return Response(status=status.HTTP_202_ACCEPTED)


class DocumentDownloadView(APIView):
    """Download a document file with proper security and performance."""
    
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DocumentsRateThrottle]
    
    def get(self, request, pk):
        try:
            # Verify document exists and user has access
            document = Document.objects.get(
                id=pk, 
                organization=request.user.organization
            )
        except Document.DoesNotExist:
            raise Http404("Document not found")
        
        # Check if document is ready
        if document.status != Document.Status.READY:
            return Response(
                {
                    "detail": "Document is not ready for download",
                    "status": document.status
                },
                status=status.HTTP_409_CONFLICT
            )
        
        try:
            return self._serve_file(document, request)
        except Exception as e:
            logger.error(f"Failed to download document {document.id}: {e}")
            return Response(
                {"detail": "File download failed"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _serve_file(self, document: Document, request):
        """Serve the file with appropriate headers and streaming."""
        
        # Try to get file path from URL
        file_path = self._get_file_path(document)
        
        if not file_path or not default_storage.exists(file_path):
            logger.warning(f"File not found in storage: {file_path}")
            # File not found in storage, return the URL for external download
            return Response(
                {
                    "download_url": document.url,
                    "message": "File is stored externally, use the provided URL"
                },
                status=status.HTTP_200_OK
            )
        
        # Get file info
        file_size = default_storage.size(file_path)
        logger.info(f"Serving file: {file_path}, size: {file_size} bytes")
        
        # Determine MIME type
        mime_type = self._get_mime_type_by_extension(document.file_type)
        logger.debug(f"MIME type: {mime_type}")
        
        # Generate safe filename (without encoding issues)
        safe_filename = document.name
        if not safe_filename.lower().endswith(f'.{document.file_type.lower()}'):
            safe_filename = f"{safe_filename}.{document.file_type.lower()}"
        
        # Log download event
        logger.info(
            f"Document download: {document.id} ({safe_filename}) by user {request.user.id} "
            f"from org {request.user.organization.id}"
        )
        
        # Simple file streaming without range requests (which can cause corruption)
        try:
            with default_storage.open(file_path, 'rb') as file_handle:
                response = HttpResponse(
                    file_handle.read(),
                    content_type=mime_type
                )
                
                # Set download headers
                response['Content-Length'] = str(file_size)
                response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
                response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                
                # Security headers
                response['X-Content-Type-Options'] = 'nosniff'
                response['X-Frame-Options'] = 'DENY'
                
                logger.debug(f"File served successfully: {safe_filename}")
                return response
                
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return Response(
                {"detail": "Error reading file"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_file_path(self, document: Document) -> str | None:
        """Extract file path from document URL."""
        from urllib.parse import unquote
        
        url = document.url
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        
        logger.debug(f"Extracting file path from URL: {url}")
        
        if url.startswith(media_url):
            # Remove media URL prefix to get relative path and URL decode
            path = url[len(media_url):].lstrip('/')
            decoded_path = unquote(path)
            logger.debug(f"Local file path: {path} -> decoded: {decoded_path}")
            return decoded_path
        
        # For absolute URLs, try to extract the path
        if url.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.path.startswith(media_url):
                path = parsed.path[len(media_url):].lstrip('/')
                decoded_path = unquote(path)
                logger.debug(f"HTTP file path: {path} -> decoded: {decoded_path}")
                return decoded_path
        
        logger.warning(f"Could not extract file path from URL: {url}")
        return None
    
    def _get_mime_type_by_extension(self, file_type: str) -> str:
        """Get MIME type based on file extension."""
        mime_types = {
            'pdf': 'application/pdf',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',
            'md': 'text/markdown',
            'csv': 'text/csv',
        }
        return mime_types.get(file_type.lower(), 'application/octet-stream')
    

