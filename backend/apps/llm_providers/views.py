from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from .models import LLMProvider, LLMModel
from .serializers import (
    LLMProviderSerializer, 
    LLMProviderSimpleSerializer,
    LLMModelSerializer
)


class LLMProviderListView(generics.ListAPIView):
    """
    List all active LLM providers with their models
    """
    serializer_class = LLMProviderSerializer
    permission_classes = [AllowAny]  # Public endpoint
    
    def get_queryset(self):
        return LLMProvider.objects.filter(is_active=True).prefetch_related('models')
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class LLMProviderSimpleListView(generics.ListAPIView):
    """
    List all active LLM providers without nested models (for dropdowns)
    """
    serializer_class = LLMProviderSimpleSerializer
    permission_classes = [AllowAny]  # Public endpoint
    
    def get_queryset(self):
        return LLMProvider.objects.filter(is_active=True)
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


class LLMModelsByProviderView(generics.ListAPIView):
    """
    List all active models for a specific provider
    """
    serializer_class = LLMModelSerializer
    permission_classes = [AllowAny]  # Public endpoint
    
    def get_queryset(self):
        provider_name = self.kwargs.get('provider_name')
        return LLMModel.objects.filter(
            provider__name=provider_name,
            provider__is_active=True,
            is_active=True
        ).select_related('provider')
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)


@api_view(['GET'])
@permission_classes([AllowAny])  # Public endpoint
def provider_models_config(request):
    """
    Return provider and model configuration in the format expected by frontend
    This mimics the old hardcoded llmProviders object structure for easier migration
    """
    cache_key = 'llm_providers_config'
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return Response(cached_data)
    
    providers = LLMProvider.objects.filter(is_active=True).prefetch_related('models')
    
    config = {}
    for provider in providers:
        active_models = provider.models.filter(is_active=True)
        config[provider.name] = {
            'name': provider.display_name,
            'models': [model.name for model in active_models],
            'description': provider.description,
            'api_base_url': provider.api_base_url,
        }
    
    # Cache for 15 minutes
    cache.set(cache_key, config, 60 * 15)
    
    return Response(config)


@api_view(['GET'])
@permission_classes([AllowAny])  # Public endpoint
def provider_model_details(request, provider_name, model_name):
    """
    Get detailed information about a specific model
    """
    try:
        model = LLMModel.objects.select_related('provider').get(
            provider__name=provider_name,
            name=model_name,
            provider__is_active=True,
            is_active=True
        )
        serializer = LLMModelSerializer(model)
        return Response(serializer.data)
    except LLMModel.DoesNotExist:
        return Response(
            {'error': f'Model {model_name} not found for provider {provider_name}'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
def clear_provider_cache(request):
    """
    Clear LLM provider cache (admin only)
    """
    cache.delete('llm_providers_config')
    cache.delete_many([
        'views.decorators.cache.cache_page.*.apps.llm_providers.views.LLMProviderListView.*',
        'views.decorators.cache.cache_page.*.apps.llm_providers.views.LLMProviderSimpleListView.*',
    ])
    return Response({'message': 'Provider cache cleared successfully'})
