from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status
from django.conf import settings
from django.utils.timezone import now
from django.http import StreamingHttpResponse
from apps.chat.serializers import ChatRequestSerializer, ChatResponseSerializer
from apps.chat.services import chat_completion, chat_strea
from common.security.throttles import ChatRateThrottle # Import ChatRateThrottle
from common.utils.idempotency import reserve_idempotency_key, save_idempotent_result, get_idempotent_result
from common.utils.sse import sse_event
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse

@extend_schema(
    request=ChatRequestSerializer,
    responses={200: ChatResponseSerializer},
    examples=[
        OpenApiExample(
            "Chat request",
            value={
              "messages":[{"role":"user","content":"What is our refund policy?"}],
              "max_tokens":512,"temperature":0.2,"top_k":6
            },
        )
    ],
    description="Synchronous chat completion with org-scoped retrieval (RAG). "
                "Requires Authorization (JWT) or X-API-Key and Idempotency-Key header.",
)
class ChatCompletionsView(APIView):
    """
    POST /api/chat/completions
    Auth: JWT (dashboard) or X-API-Key (integrations)
    Requires Idempotency-Key header (returns 400 if missing).
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatRateThrottle] # Apply throttle

    def post(self, request):
        # org resolution
        org = getattr(request, "organization", None) or getattr(request.user, "organization", None)
        if not org:
            return Response({"detail": "No organization context"}, status=403)

        # idempotency
        idem_key = request.headers.get("Idempotency-Key")
        if not idem_key:
            return Response({"detail": "Idempotency-Key header required"}, status=400)
        prev = get_idempotent_result(idem_key)
        if prev is not None:
            return Response(prev, status=200)

        ok = reserve_idempotency_key(idem_key)
        if not ok:
            # Another request is/was processing this key; ask client to retry backoff
            return Response({"detail": "Duplicate request in progress"}, status=409)

        s = ChatRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            result = chat_completion(org=org, payload=s.validated_data)
            out = ChatResponseSerializer(result).data
            # usage++
            api_key = getattr(request, "auth_api_key", None)
            if api_key:
                type(api_key).objects.filter(pk=api_key.pk).update(usage_count=F("usage_count") + 1)
            save_idempotent_result(idem_key, out)
            return Response(out)
        except Exception as e:
            return Response({"detail": str(e)}, status=500)

@extend_schema(
    request=ChatRequestSerializer,
    responses={200: OpenApiResponse(description="SSE stream (text/event-stream) of deltas")},
    description="Streaming chat completion via SSE. Emits events: message_start, citation, delta, message_end, error.",
)
class ChatStreamView(APIView):
    """
    POST /api/chat/stream  (SSE)
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ChatRateThrottle] # Apply throttle

    def post(self, request):
        org = getattr(request, "organization", None) or getattr(request.user, "organization", None)
        if not org:
            return Response({"detail": "No organization context"}, status=403)

        s = ChatRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        def gen():
            try:
                for event, data in chat_stream(org=org, payload=s.validated_data):
                    yield sse_event(data, event=event)
            except Exception as e:
                yield sse_event({"detail": str(e)}, event="error")
            yield "data: [DONE]\n\n"

        resp = StreamingHttpResponse(gen(), content_type="text/event-stream")
        resp["Cache-Control"] = "no-cache"
        resp["X-Accel-Buffering"] = "no"
        return resp
