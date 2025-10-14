from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from common.security.permissions import IsOwnerOrAdmin
from apps.chatbot.models import Chatbot
from apps.chatbot.serializers import (
    ChatbotUpdateSerializer, 
    ChatbotConfigSerializer,
    TestKeySerializer
)
from apps.chatbot.services import ProviderTestService
from apps.chat.services import chat_completion
from drf_spectacular.utils import extend_schema
import logging

logger = logging.getLogger(__name__)


class ChatbotView(APIView):
    """
    Main chatbot configuration view.
    GET: Get current chatbot configuration
    PUT: Update chatbot configuration (including LLM provider and documents)
    """
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self, request):
        org = request.user.organization
        bot, _ = Chatbot.objects.get_or_create(
            organization=org,
            defaults={
                "name": f"{org.name} Chatbot",
                "tone": "technical",
                "system_instructions": "",
            },
        )
        return bot

    @extend_schema(
        responses={200: ChatbotConfigSerializer},
        description="Get the chatbot configuration including connected documents"
    )
    def get(self, request):
        chatbot = self.get_object(request)
        serializer = ChatbotConfigSerializer(chatbot, context={'request': request})
        return Response(serializer.data)

    @extend_schema(
        request=ChatbotUpdateSerializer,
        responses={200: ChatbotConfigSerializer},
        description="Update chatbot configuration including LLM provider and connected documents"
    )
    def put(self, request):
        chatbot = self.get_object(request)
        serializer = ChatbotUpdateSerializer(
            chatbot, 
            data=request.data, 
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Return updated configuration
        response_serializer = ChatbotConfigSerializer(chatbot, context={'request': request})
        return Response(response_serializer.data)


@extend_schema(
    request=TestKeySerializer,
    responses={
        200: {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "details": {"type": "object"}
            }
        },
        400: {
            "type": "object", 
            "properties": {
                "success": {"type": "boolean"},
                "message": {"type": "string"},
                "details": {"type": "object"}
            }
        }
    },
    description="Test LLM provider API key and model functionality by making a real API call.",
)
class TestApiKeyView(APIView):
    """
    POST /api/chatbot/test-api-key
    Body: { "provider": "openai|gemini|deepseek", "model_name": "<model>", "api_key": "<secret>" }
    Tests the provided API key by making a real call to the LLM provider.
    """
    permission_classes = [IsOwnerOrAdmin]

    def post(self, request):
        # Validate input data
        serializer = TestKeySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract validated data
        provider = serializer.validated_data["provider"]
        model_name = serializer.validated_data["model_name"]
        api_key = serializer.validated_data["api_key"]
        
        # Test the provider
        success, message, details = ProviderTestService.test_provider(
            provider=provider,
            model_name=model_name,
            api_key=api_key
        )
        
        # Return appropriate response
        status_code = status.HTTP_200_OK if success else status.HTTP_400_BAD_REQUEST
        
        return Response(
            {
                "success": success,
                "message": message,
                "details": details
            },
            status=status_code
        )


class ChatbotMessageView(APIView):
    """
    POST /api/chatbot/message
    Send a message to the chatbot and get a response using RAG with connected documents.
    """
    permission_classes = [IsOwnerOrAdmin]

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "message": {"type": "string"},
                "history": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {"type": "string", "enum": ["user", "bot"]},
                            "content": {"type": "string"},
                            "timestamp": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["message"]
        },
        responses={
            200: {
                "type": "object",
                "properties": {
                    "reply": {"type": "string"},
                    "sources": {"type": "array", "items": {"type": "string"}}
                }
            }
        },
        description="Send a message to the chatbot and get a response using RAG"
    )
    def post(self, request):
        # Get the organization
        org = request.user.organization
        
        # Validate input
        message = request.data.get('message', '')
        history = request.data.get('history', [])
        
        if not message.strip():
            return Response(
                {"error": "Message cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Check if chatbot exists and is configured
            try:
                chatbot = Chatbot.objects.get(organization=org)
            except Chatbot.DoesNotExist:
                return Response(
                    {"error": "Chatbot not configured for this organization"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if LLM is configured
            if not chatbot.llm_provider or not chatbot.llm_api_key:
                return Response(
                    {"error": "LLM provider not configured"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert history to message format expected by chat_completion
            messages = []
            if history:
                for msg in history:
                    role = "user" if msg.get("type") == "user" else "assistant"
                    messages.append({
                        "role": role,
                        "content": msg.get("content", "")
                    })
            
            # Add current message
            messages.append({
                "role": "user",
                "content": message
            })
            
            # Get connected document IDs for filtering
            document_ids = list(chatbot.documents_connected.values_list('id', flat=True))
            
            # If no documents connected, don't allow RAG (require at least one document)
            if not document_ids:
                return Response(
                    {"error": "No documents connected. Please connect at least one document to use the chatbot."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Build payload for RAG (always with document filter)
            payload = {
                "messages": messages,
                "max_tokens": 512,
                "temperature": 0.2,
                "top_k": 6,
                "filters": {
                    "document_ids": document_ids
                }
            }
            
            # Call RAG completion
            result = chat_completion(org=org, payload=payload)
            
            # Extract sources from citations
            sources = []
            seen_docs = set()
            for citation in result.get("citations", []):
                doc_id = citation.get("document_id")
                if doc_id and doc_id not in seen_docs:
                    seen_docs.add(doc_id)
                    # Get document name
                    doc_name = chatbot.documents_connected.filter(id=doc_id).values_list('name', flat=True).first()
                    if doc_name:
                        sources.append(doc_name)
            
            return Response({
                "reply": result.get("answer", ""),
                "sources": sources,
                "usage": result.get("usage", {}),
                "latency_ms": result.get("latency_ms", 0)
            })
            
        except RuntimeError as e:
            logger.error(f"RAG error: {str(e)}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to generate response: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Failed to generate response: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
