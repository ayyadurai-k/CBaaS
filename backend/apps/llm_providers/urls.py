from django.urls import path
from . import views

urlpatterns = [
    # Full provider data with models
    path('providers/', views.LLMProviderListView.as_view(), name='llm-providers'),
    
    # Simple provider list (for dropdowns)
    path('providers/simple/', views.LLMProviderSimpleListView.as_view(), name='llm-providers-simple'),
    
    # Models for a specific provider
    path('providers/<str:provider_name>/models/', views.LLMModelsByProviderView.as_view(), name='llm-provider-models'),
    
    # Frontend-compatible config (matches old hardcoded structure)
    path('providers/config/', views.provider_models_config, name='llm-providers-config'),
    
    # Model details
    path('providers/<str:provider_name>/models/<str:model_name>/', views.provider_model_details, name='llm-model-details'),
    
    # Cache management
    path('providers/cache/clear/', views.clear_provider_cache, name='clear-provider-cache'),
]