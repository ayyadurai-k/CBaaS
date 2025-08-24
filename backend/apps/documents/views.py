from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from apps.documents.models import Document
from common.security.permissions import ReadOnlyOrOwnerAdmin
from common.security.throttles import DocumentsRateThrottle
from apps.documents.serializers import DocumentSerializer, DocumentUploadSerializer
from apps.documents.tasks import process_document

class DocumentListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DocumentsRateThrottle] # Apply throttle
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

class DocumentReprocessView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [DocumentsRateThrottle] # Apply throttle

    def post(self, request, pk):
        try:
            doc = Document.objects.get(id=pk, organization=request.user.organization)
        except Document.DoesNotExist:
            return Response({"detail": "Document not found."}, status=status.HTTP_404_NOT_FOUND)

        doc.status = Document.Status.PROCESSING
        doc.save(update_fields=["status"])
        process_document.delay(str(doc.id))
        return Response(status=status.HTTP_202_ACCEPTED)
