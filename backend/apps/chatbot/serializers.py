from rest_framework import serializers
from .models import Chatbot


class TestKeySerializer(serializers.Serializer):
    """Serializer for testing LLM provider API keys."""

    api_key = serializers.CharField(max_length=255, required=True)
    provider = serializers.ChoiceField(choices=Chatbot.PROVIDER_CHOICES, required=True)
    model_name = serializers.CharField(max_length=50, required=True)


class ChatbotSerializer(serializers.ModelSerializer):
    """Complete chatbot serializer with all configuration fields."""

    llm_api_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    documents_connected = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = Chatbot
        fields = [
            "id",
            "name",
            "tone",
            "system_instructions",
            "llm_provider",
            "llm_model",
            "llm_api_key",
            "llm_system_prompt",
            "llm_is_active",
            "documents_connected",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For write operations, we'll handle documents_connected in the view


class ChatbotUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating chatbot configuration."""

    llm_api_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    documents_connected = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )

    class Meta:
        model = Chatbot
        fields = [
            "name",
            "tone",
            "system_instructions",
            "llm_provider",
            "llm_model",
            "llm_api_key",
            "llm_system_prompt",
            "llm_is_active",
            "documents_connected",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Documents will be handled in the update method

    def update(self, instance, validated_data):
        # Handle API key encryption
        if "llm_api_key" in validated_data:
            api_key = validated_data.pop("llm_api_key")
            if api_key:
                instance.llm_api_key = (
                    api_key  # Uses the property setter for encryption
                )
            elif api_key == "":  # Explicitly clear the key
                instance.llm_api_key_encrypted = None

        # Handle documents_connected (Many-to-Many)
        if "documents_connected" in validated_data:
            document_ids = validated_data.pop("documents_connected")
            from apps.documents.models import Document

            documents = Document.objects.filter(
                id__in=document_ids, organization=instance.organization
            )
            instance.documents_connected.set(documents)

        # Update other fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class ChatbotConfigSerializer(serializers.ModelSerializer):
    """Serializer for frontend chatbot configuration page."""

    llm_api_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    documents_connected_ids = serializers.SerializerMethodField()
    documents_available = serializers.SerializerMethodField()

    class Meta:
        model = Chatbot
        fields = [
            "id",
            "name",
            "tone",
            "system_instructions",
            "llm_provider",
            "llm_model",
            "llm_api_key",
            "llm_system_prompt",
            "llm_is_active",
            "documents_connected_ids",
            "documents_available",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
            "documents_connected_ids",
            "documents_available",
        ]

    def get_documents_connected_ids(self, obj):
        """Return list of connected document IDs."""
        return list(obj.documents_connected.values_list("id", flat=True))

    def get_documents_available(self, obj):
        """Return all available documents for this organization."""
        from apps.documents.models import Document

        docs = Document.objects.filter(organization=obj.organization)
        return [
            {
                "id": str(doc.id),
                "name": doc.name,
                "connected": obj.documents_connected.filter(id=doc.id).exists(),
            }
            for doc in docs
        ]
