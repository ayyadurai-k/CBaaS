from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from apps.search.serializers import SearchRequestSerializer, SearchResponseSerializer
from common.llm.embeddings import get_embedding
from apps.documents.models import DocumentChunk
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse



@extend_schema(request=SearchRequestSerializer, responses={200: SearchResponseSerializer})
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
        api_key = getattr(request, "auth_api_key", None)
        if api_key:
            type(api_key).objects.filter(pk=api_key.pk).update(usage_count=F("usage_count") + 1)
        return Response({"results": rows})
