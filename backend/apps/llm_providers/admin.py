from django.contrib import admin
from .models import LLMProvider, LLMModel


@admin.register(LLMProvider)
class LLMProviderAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'display_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    fieldsets = (
        (None, {
            'fields': ('name', 'display_name', 'description', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_base_url',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(LLMModel)
class LLMModelAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'provider', 'name', 'is_active', 'is_default', 'created_at']
    list_filter = ['provider', 'is_active', 'is_default', 'supports_streaming', 'supports_function_calling']
    search_fields = ['name', 'display_name', 'provider__name', 'provider__display_name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'full_name']
    fieldsets = (
        (None, {
            'fields': ('provider', 'name', 'display_name', 'description', 'is_active', 'is_default')
        }),
        ('Model Specifications', {
            'fields': ('context_window', 'max_tokens', 'supports_streaming', 'supports_function_calling'),
            'classes': ('collapse',)
        }),
        ('Pricing', {
            'fields': ('cost_per_1k_input_tokens', 'cost_per_1k_output_tokens'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'full_name', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('provider')
