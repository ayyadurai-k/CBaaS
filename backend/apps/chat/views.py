from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from apps.chat.serializers import ChatRequestSerializer, ChatResponseSerializer
from apps.chat.services import chat_completion, chat_stream
from apps.chatbot.models import Chatbot
from common.security.throttles import ChatRateThrottle, APIKeyRateThrottle
from common.security.api_key_permissions import ChatAPIKeyPermission
from common.utils.idempotency import (
    reserve_idempotency_key,
    save_idempotent_result,
    get_idempotent_result,
)
from common.utils.sse import sse_event
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from django.db.models import F


@extend_schema(
    request=ChatRequestSerializer,
    responses={200: ChatResponseSerializer},
    parameters=[
        OpenApiParameter(
            name='X-API-Key',
            type=str,
            location=OpenApiParameter.HEADER,
            description='API Key for authentication (alternative to JWT)',
            required=False
        ),
        OpenApiParameter(
            name='Idempotency-Key',
            type=str,
            location=OpenApiParameter.HEADER,
            description='Unique key to prevent duplicate requests',
            required=True
        ),
    ],
    examples=[
        OpenApiExample(
            "Chat request",
            value={
                "messages": [{"role": "user", "content": "What is our refund policy?"}],
                "max_tokens": 512,
                "temperature": 0.2,
                "top_k": 6,
            },
        )
    ],
    description="""
    Synchronous chat completion with org-scoped retrieval (RAG).
    
    **Authentication:**
    - JWT Token (Authorization: Bearer <token>) OR
    - API Key (X-API-Key: <key>)
    
    **API Key Requirements:**
    - Scope: FULL_ACCESS required (read-only and upload-only keys are rejected)
    - Status: ACTIVE (revoked or expired keys are rejected)
    - Quota: Must have remaining quota
    - IP: Must be from allowed IP (if IP whitelist is configured)
    - Rate Limit: Subject to per-key rate limits
    
    **Idempotency:**
    - Requires Idempotency-Key header to prevent duplicate processing
    - Same key within TTL window returns cached response
    
    **Rate Limits:**
    - Per-API-key: Custom limit or default 60/min
    - Per-user (JWT): 1000/hour
    - Scoped (chat): Configurable in settings
    """,
    tags=["Chat"]
)
class ChatCompletionsView(APIView):
    """
    POST /api/chat/completions
    
    Secure chat endpoint with comprehensive API key protection:
    - Scope validation (full-access only)
    - Quota enforcement
    - Rate limiting (per-key)
    - IP whitelisting
    - Usage tracking
    - Idempotency
    """

    permission_classes = [IsAuthenticated, ChatAPIKeyPermission]
    throttle_classes = [ChatRateThrottle, APIKeyRateThrottle]

    def post(self, request):
        # org resolution
        org = getattr(request, "organization", None) or getattr(
            request.user, "organization", None
        )
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
        
        # Get chatbot's connected documents for filtering
        try:
            chatbot = Chatbot.objects.get(organization=org)
            document_ids = list(chatbot.documents_connected.values_list('id', flat=True))
            
            # Enforce: Must have connected documents
            if not document_ids:
                return Response(
                    {"detail": "No documents connected to chatbot. Please connect at least one document."},
                    status=400
                )
            
            # Ensure we only search in connected documents
            payload = s.validated_data.copy()
            if 'filters' not in payload:
                payload['filters'] = {}
            payload['filters']['document_ids'] = document_ids
            
        except Chatbot.DoesNotExist:
            return Response(
                {"detail": "Chatbot not configured. Please configure your chatbot first."},
                status=400
            )
        
        try:
            result = chat_completion(org=org, payload=payload)
            out = ChatResponseSerializer(result).data
            
            # Track token usage for API key billing/analytics
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            
            # Increment API key usage (atomic)
            api_key = getattr(request, "auth_api_key", None)
            if api_key:
                # Usage count incremented by middleware
                # Here we just attach tokens for logging middleware
                request.tokens_used = tokens_used
            
            save_idempotent_result(idem_key, out)
            
            # Attach usage metrics to response for middleware logging
            response = Response(out)
            response.tokens_used = tokens_used
            response.documents_searched = payload.get('top_k', 6)
            
            return response
            
        except Exception as e:
            return Response({"detail": str(e)}, status=500)


@extend_schema(
    request=ChatRequestSerializer,
    parameters=[
        OpenApiParameter(
            name='X-API-Key',
            type=str,
            location=OpenApiParameter.HEADER,
            description='API Key for authentication',
            required=False
        ),
    ],
    responses={
        200: OpenApiResponse(description="SSE stream (text/event-stream) of deltas")
    },
    description="""
    Streaming chat completion via Server-Sent Events (SSE).
    
    **Authentication:** Same as /completions endpoint
    
    **Stream Events:**
    - message_start: Initial message metadata
    - citation: Document chunk reference
    - delta: Incremental text chunk
    - message_end: Final message with usage stats
    - error: Error information
    
    **API Key Scope:** FULL_ACCESS required
    """,
    tags=["Chat"]
)
class ChatStreamView(APIView):
    """
    POST /api/chat/stream  (SSE)
    
    Streaming version of chat with same security as completions endpoint.
    """

    permission_classes = [IsAuthenticated, ChatAPIKeyPermission]
    throttle_classes = [ChatRateThrottle, APIKeyRateThrottle]

    def post(self, request):
        org = getattr(request, "organization", None) or getattr(
            request.user, "organization", None
        )
        if not org:
            return Response({"detail": "No organization context"}, status=403)

        s = ChatRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        
        # Get chatbot's connected documents for filtering
        try:
            chatbot = Chatbot.objects.get(organization=org)
            document_ids = list(chatbot.documents_connected.values_list('id', flat=True))
            
            # Enforce: Must have connected documents
            if not document_ids:
                return Response(
                    {"detail": "No documents connected to chatbot. Please connect at least one document."},
                    status=400
                )
            
            # Ensure we only search in connected documents
            payload = s.validated_data.copy()
            if 'filters' not in payload:
                payload['filters'] = {}
            payload['filters']['document_ids'] = document_ids
            
        except Chatbot.DoesNotExist:
            return Response(
                {"detail": "Chatbot not configured. Please configure your chatbot first."},
                status=400
            )

        def gen():
            try:
                for event, data in chat_stream(org=org, payload=payload):
                    yield sse_event(data, event=event)
            except Exception as e:
                yield sse_event({"detail": str(e)}, event="error")
            yield "data: [DONE]\n\n"

        resp = StreamingHttpResponse(gen(), content_type="text/event-stream")
        resp["Cache-Control"] = "no-cache"
        resp["X-Accel-Buffering"] = "no"
        return resp
