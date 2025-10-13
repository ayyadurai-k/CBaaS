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
from drf_spectacular.utils import extend_schema


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
        # Get the organization's chatbot
        org = request.user.organization
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
        
        message = request.data.get('message', '')
        history = request.data.get('history', [])
        
        if not message.strip():
            return Response(
                {"error": "Message cannot be empty"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # TODO: Implement RAG logic here using the connected documents
            # For now, returning a mock response
            response_text = "Based on our company handbook, employees are entitled to 15 days of paid vacation per year. You can request time off through our HR portal or by contacting your manager directly."
            sources = list(chatbot.documents_connected.values_list('name', flat=True))
            
            return Response({
                "reply": response_text,
                "sources": sources
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to generate response: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
