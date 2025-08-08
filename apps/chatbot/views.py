from rest_framework.views import APIView
from rest_framework.response import Response
from common.security.permissions import IsOwnerOrAdmin
from rest_framework import serializers
from .models import Chatbot

class ChatbotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chatbot
        fields = ["id","name","tone","system_instructions","created_at","updated_at"]

class ChatbotUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chatbot
        fields = ["name","tone","system_instructions"]

class ChatbotView(APIView):
    permission_classes = [IsOwnerOrAdmin]
    def get_object(self, request):
        org = request.user.organization
        bot, _ = Chatbot.objects.get_or_create(organization=org, defaults={
            "name": f"{org.name} Chatbot", "tone": "Technical", "system_instructions": ""
        })
        return bot
    def get(self, request):
        return Response(ChatbotSerializer(self.get_object(request)).data)
    def put(self, request):
        bot = self.get_object(request)
        s = ChatbotUpdateSerializer(bot, data=request.data, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(ChatbotSerializer(bot).data)