from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from common.llm.embeddings import get_embedding
from apps.documents.models import DocumentChunk

class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=4000)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=50, default=8)
    filters = serializers.DictField(required=False)

class SearchView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        org = getattr(request, "organization", None) or getattr(request.user, "organization", None)
        if not org:
            return Response({"detail": "No organization context"}, status=403)
        s = SearchRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        qvec = get_embedding(s.validated_data["query"])
        qs = (DocumentChunk.objects
              .filter(document__organization_id=org.id)
              .extra(select={"score": "1 - (embedding <=> %s)"}, select_params=[qvec])
              .order_by("-score"))
        filters = s.validated_data.get("filters") or {}
        if ids := filters.get("document_ids"):
            qs = qs.filter(document_id__in=ids)
        if fts := filters.get("file_types"):
            qs = qs.filter(document__file_type__in=fts)
        rows = list(qs.values("document_id", "chunk_index", "content", "score")[: s.validated_data["top_k"]])
        return Response({"results": rows})
