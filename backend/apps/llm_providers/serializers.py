from rest_framework import serializers
from .models import LLMProvider, LLMModel


class LLMModelSerializer(serializers.ModelSerializer):
    """Serializer for LLM models"""
    
    class Meta:
        model = LLMModel
        fields = [
            'id', 'name', 'display_name', 'description',
            'context_window', 'max_tokens', 'supports_streaming',
            'supports_function_calling', 'cost_per_1k_input_tokens',
            'cost_per_1k_output_tokens', 'is_default', 'full_name'
        ]
        read_only_fields = ['id', 'full_name']


class LLMProviderSerializer(serializers.ModelSerializer):
    """Serializer for LLM providers with nested models"""
    models = LLMModelSerializer(many=True, read_only=True)
    active_models = serializers.SerializerMethodField()
    
    class Meta:
        model = LLMProvider
        fields = [
            'id', 'name', 'display_name', 'description', 
            'api_base_url', 'models', 'active_models'
        ]
        read_only_fields = ['id']
    
    def get_active_models(self, obj):
        """Return only active models for the provider"""
        active_models = obj.models.filter(is_active=True)
        return LLMModelSerializer(active_models, many=True).data


class LLMProviderSimpleSerializer(serializers.ModelSerializer):
    """Simple serializer for LLM providers without nested models"""
    
    class Meta:
        model = LLMProvider
        fields = ['id', 'name', 'display_name', 'description']
        read_only_fields = ['id']