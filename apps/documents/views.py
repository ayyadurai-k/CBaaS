from rest_framework import generics, permissions
from common.security.permissions import ReadOnlyOrOwnerAdmin
from .models import Document
from apps.documents.serializers import DocumentSerializer, DocumentUploadSerializer

class DocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    search_fields = ["name", "file_type", "status"]
    ordering_fields = ["upload_date", "name", "size_bytes"]
    def get_queryset(self):
        return Document.objects.all()
    def get_serializer_class(self):
        return DocumentUploadSerializer if self.request.method == "POST" else DocumentSerializer

class DocumentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [ReadOnlyOrOwnerAdmin]
    serializer_class = DocumentSerializer
    def get_queryset(self):
        return Document.objects.all()
