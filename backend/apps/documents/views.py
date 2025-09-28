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
        
        # Determine MIME type
        mime_type, encoding = mimetypes.guess_type(document.name)
        if not mime_type:
            mime_type = self._get_mime_type_by_extension(document.file_type)
        
        # Generate safe filename
        safe_filename = self._get_safe_filename(document)
        
        # Log download event
        logger.info(
            f"Document download: {document.id} by user {request.user.id} "
            f"from org {request.user.organization.id}"
        )
        
        # Handle range requests for large files (partial content)
        range_header = request.META.get('HTTP_RANGE')
        if range_header and file_size > 1024 * 1024:  # 1MB threshold
            return self._handle_range_request(document, file_path, range_header, mime_type, safe_filename)
        
        # Stream the file
        def file_iterator(file_path, chunk_size=8192):
            with default_storage.open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        
        response = StreamingHttpResponse(
            file_iterator(file_path),
            content_type=mime_type
        )
        
        # Set download headers
        response['Content-Length'] = str(file_size)
        response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        
        return response
    
    def _get_file_path(self, document: Document) -> str | None:
        """Extract file path from document URL."""
        url = document.url
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        
        if url.startswith(media_url):
            # Remove media URL prefix to get relative path
            return url[len(media_url):].lstrip('/')
        
        # For absolute URLs, try to extract the path
        if url.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            if parsed.path.startswith(media_url):
                return parsed.path[len(media_url):].lstrip('/')
        
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
    
    def _get_safe_filename(self, document: Document) -> str:
        """Generate a safe filename for download."""
        name = document.name
        
        # Add extension if not present
        if not name.lower().endswith(f'.{document.file_type.lower()}'):
            name = f"{name}.{document.file_type.lower()}"
        
        # Quote special characters for HTTP header
        return quote(name.encode('utf-8'))
    
    def _handle_range_request(self, document, file_path, range_header, mime_type, safe_filename):
        """Handle HTTP range requests for partial content (resumable downloads)."""
        try:
            file_size = default_storage.size(file_path)
            
            # Parse range header (e.g., "bytes=0-1023")
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            
            # Validate range
            if start >= file_size or end >= file_size or start > end:
                response = HttpResponse(status=416)  # Range Not Satisfiable
                response['Content-Range'] = f'bytes */{file_size}'
                return response
            
            # Stream partial content
            def range_file_iterator(file_path, start, end, chunk_size=8192):
                with default_storage.open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = end - start + 1
                    while remaining > 0:
                        chunk_size = min(chunk_size, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            response = StreamingHttpResponse(
                range_file_iterator(file_path, start, end),
                status=206,  # Partial Content
                content_type=mime_type
            )
            
            response['Content-Range'] = f'bytes {start}-{end}/{file_size}'
            response['Content-Length'] = str(end - start + 1)
            response['Content-Disposition'] = f'attachment; filename="{safe_filename}"'
            response['Accept-Ranges'] = 'bytes'
            
            return response
            
        except (ValueError, IndexError):
            # Invalid range header, fall back to full download
            return self._serve_file(document, None)
