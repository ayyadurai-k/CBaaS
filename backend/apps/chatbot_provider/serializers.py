from rest_framework import serializers
from .models import ChatbotProvider

class TestKeySerializer(serializers.Serializer):
    """Serializer for testing LLM provider API keys."""
    api_key = serializers.CharField(max_length=255, required=True)
    
    provider = serializers.ChoiceField(
        choices=[
            ("openai", "OpenAI"),
            ("gemini", "Gemini"),
            ("deepseek", "DeepSeek"),
        ],
        required=True
    )
    model_name = serializers.CharField(max_length=50, required=True)

class ProviderSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True)
    class Meta:
        model = ChatbotProvider
        fields = ["id","provider","model_name","api_key","created_at","updated_at"]
        read_only_fields = ["id","created_at","updated_at"]

class ProviderUpsertSerializer(serializers.ModelSerializer):
    api_key = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = ChatbotProvider
        fields = ["provider", "model_name", "api_key"]

    def create(self, validated_data):
        raise NotImplementedError("Use view's upsert logic")

    def update(self, instance, validated_data):
        instance.provider = validated_data.get("provider", instance.provider)
        instance.model_name = validated_data.get("model_name", instance.model_name)
        if "api_key" in validated_data:
            instance.api_key = validated_data["api_key"]  # property setter encrypts
        instance.save()
        return instance