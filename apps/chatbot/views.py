from rest_framework.views import APIView
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from .models import Chatbot
from apps.chatbot.serializers import ChatbotSerializer, ChatbotUpdateSerializer


class ChatbotView(APIView):
    permission_classes = [IsOwnerOrAdmin]

    def get_object(self, request):
        org = request.user.organization
        bot, _ = Chatbot.objects.get_or_create(
            organization=org,
            defaults={
                "name": f"{org.name} Chatbot",
                "tone": "Technical",
                "system_instructions": "",
            },
        )
        return bot

    def get(self, request):
        return Response(ChatbotSerializer(self.get_object(request)).data)

    def put(self, request):
        bot = self.get_object(request)
        serializer = ChatbotUpdateSerializer(bot, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ChatbotSerializer(bot).data)
