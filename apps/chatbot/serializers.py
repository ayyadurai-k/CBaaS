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
