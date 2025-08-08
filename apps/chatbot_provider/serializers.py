from rest_framework import serializers
from .models import ChatbotProvider

class ProviderSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True)
    class Meta:
        model = ChatbotProvider
        fields = ["id","provider","model_name","api_key","created_at","updated_at"]
        read_only_fields = ["id","created_at","updated_at"]
