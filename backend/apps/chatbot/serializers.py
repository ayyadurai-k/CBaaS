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
    # Use JSONField for document IDs instead of M2M
    connected_document_ids = serializers.ListField(
        child=serializers.UUIDField(), read_only=True
    )
    # Convenience field to show organization info (fetched via service)
    organization_name = serializers.SerializerMethodField()

    class Meta:
        model = Chatbot
        fields = [
            "id",
            "organization_id",
            "organization_name",
            "name",
            "tone",
            "system_instructions",
            "llm_provider",
            "llm_model",
            "llm_api_key",
            "llm_system_prompt",
            "llm_is_active",
            "connected_document_ids",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization_id", "created_at", "updated_at"]

    def get_organization_name(self, obj):
        """Fetch organization name via Identity Service."""
        org = obj.get_organization()
        return org.name if org else None


class ChatbotUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating chatbot configuration."""

    llm_api_key = serializers.CharField(
        write_only=True, required=False, allow_blank=True
    )
    connected_document_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False
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
            "connected_document_ids",
        ]
        extra_kwargs = {
            'name': {'required': False},
            'tone': {'required': False},
            'system_instructions': {'required': False, 'allow_blank': True},
            'llm_provider': {'required': False},
            'llm_model': {'required': False},
            'llm_system_prompt': {'required': False, 'allow_blank': True},
            'llm_is_active': {'required': False},
        }

    def update(self, instance, validated_data):
        """Handle document ID list update."""
        document_ids = validated_data.pop('connected_document_ids', None)
        if document_ids is not None:
            # Store as list of UUID strings
            instance.connected_document_ids = [str(doc_id) for doc_id in document_ids]
        return super().update(instance, validated_data)

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
    llm_api_key_preview = serializers.SerializerMethodField()
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
            "llm_api_key_preview",
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
            "llm_api_key_preview",
            "documents_connected_ids",
            "documents_available",
        ]

    def get_documents_connected_ids(self, obj):
        """Return list of connected document IDs."""
        return list(obj.documents_connected.values_list("id", flat=True))

    def get_llm_api_key_preview(self, obj):
        """Return masked preview of API key (last 4 characters) for security."""
        if not obj.llm_api_key_encrypted:
            return None
        
        try:
            # Decrypt to get actual key
            decrypted_key = obj.llm_api_key
            if not decrypted_key or len(decrypted_key) < 4:
                return "••••"
            
            # Return masked preview with last 4 chars
            last_four = decrypted_key[-4:]
            return f"••••••••{last_four}"
        except Exception:
            # If decryption fails, just show dots
            return "••••••••"

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
