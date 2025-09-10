from rest_framework.views import APIView
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from apps.chatbot.models import Chatbot
from apps.chatbot_provider.models import ChatbotProvider
from apps.chatbot_provider.serializers import (
    ProviderSerializer,
    ProviderUpsertSerializer,
    TestKeySerializer,
)
from apps.chatbot_provider.services import ProviderTestService
from rest_framework import status
from drf_spectacular.utils import extend_schema


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
class TestKeyView(APIView):
    """
    POST /api/chatbot/test-key
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


@extend_schema(
    request=ProviderUpsertSerializer,
    responses={200: ProviderUpsertSerializer},
    description="Create or update the LLM provider for the current organization's chatbot. Key is encrypted at rest.",
)
class ChatbotProviderUpsertView(APIView):
    """
    PUT /api/chatbot/provider
    Body: { "provider": "openai|gemini|deepseek", "model_name": "<model>", "api_key": "<secret>" }
    Creates or updates the provider for the org's single chatbot.
    """

    permission_classes = [IsOwnerOrAdmin]

    def put(self, request):
        org = request.user.organization
        bot, _ = Chatbot.objects.get_or_create(
            organization=org,
            defaults={
                "name": f"{org.name} Chatbot",
                "tone": "Technical",
                "system_instructions": "",
            },
        )
        provider = ChatbotProvider.objects.filter(chatbot=bot).first()
        serializer = ProviderUpsertSerializer(instance=provider, data=request.data)
        serializer.is_valid(raise_exception=True)

        if provider is None:
            provider = ChatbotProvider(
                chatbot=bot,
                provider=serializer.validated_data["provider"],
                model_name=serializer.validated_data["model_name"],
            )
            provider.api_key = serializer.validated_data["api_key"]  # encrypted setter
            provider.save()
        else:
            serializer.update(provider, serializer.validated_data)

        # Optional: Test the provider configuration
        test_success, test_message, test_details = ProviderTestService.test_provider(
            provider=provider.provider,
            model_name=provider.model_name,
            api_key=provider.api_key  # This uses the decrypted property
        )

        return Response(
            {
                "id": str(provider.id),
                "provider": provider.provider,
                "model_name": provider.model_name,
                "created_at": provider.created_at,
                "updated_at": provider.updated_at,
                "test_result": {
                    "success": test_success,
                    "message": test_message,
                    "details": test_details
                }
            },
            status=status.HTTP_200_OK,
        )
