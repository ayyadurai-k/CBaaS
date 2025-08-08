from rest_framework.views import APIView
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from apps.chatbot.models import Chatbot
from .models import ChatbotProvider
from apps.chatbot_provider.serializers import (
    ProviderSerializer,
    ProviderUpsertSerializer,
)
from rest_framework import status
from drf_spectacular.utils import extend_schema


class TestKeyView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def post(self, request):
        bot = Chatbot.objects.filter(organization=request.user.organization).first()
        if not bot:
            return Response({"detail": "Chatbot not configured"}, status=400)
        s = ProviderSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        # (Optional) ping provider here
        return Response({"ok": True})


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

        # Optional: live ping here if you want to validate the key/model.

        return Response(
            {
                "id": str(provider.id),
                "provider": provider.provider,
                "model_name": provider.model_name,
                "created_at": provider.created_at,
                "updated_at": provider.updated_at,
            },
            status=status.HTTP_200_OK,
        )
