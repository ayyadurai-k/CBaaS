from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from apps.api_keys.models import APIKey, APIKeyUsageLog


@admin.register(APIKey)
class APIKeyAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'organization', 'scope', 'status_badge', 
        'usage_info', 'last_used_at', 'created_at'
    ]
    list_filter = ['status', 'scope', 'created_at', 'organization']
    search_fields = ['name', 'organization__name', 'key_hmac']
    readonly_fields = [
        'id', 'key_encrypted', 'key_hmac', 
        'created_at', 'updated_at', 'last_used_at', 'usage_count'
    ]
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'organization', 'name', 'scope')
        }),
        ('Security', {
            'fields': ('key_encrypted', 'key_hmac', 'allowed_ips', 'rate_limit_per_minute')
        }),
        ('Status & Quota', {
            'fields': ('status', 'revoked_reason', 'usage_count', 'quota', 'expires_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_used_at')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'active': 'green',
            'revoked': 'red',
            'expired': 'orange'
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def usage_info(self, obj):
        if obj.quota:
            percentage = (obj.usage_count / obj.quota) * 100
            color = 'red' if percentage >= 90 else 'orange' if percentage >= 70 else 'green'
            return format_html(
                '<span style="color: {};">{} / {} ({:.1f}%)</span>',
                color, obj.usage_count, obj.quota, percentage
            )
        return f"{obj.usage_count} (unlimited)"
    usage_info.short_description = 'Usage / Quota'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('organization')


@admin.register(APIKeyUsageLog)
class APIKeyUsageLogAdmin(admin.ModelAdmin):
    list_display = [
        'timestamp', 'api_key', 'method', 'endpoint', 
        'status_code', 'response_time_ms', 'tokens_used', 'ip_address'
    ]
    list_filter = ['method', 'status_code', 'timestamp', 'api_key__organization']
    search_fields = ['api_key__name', 'endpoint', 'ip_address']
    readonly_fields = [
        'id', 'api_key', 'timestamp', 'endpoint', 'method', 
        'ip_address', 'user_agent', 'status_code', 'response_time_ms',
        'tokens_used', 'documents_searched', 'error_message', 'metadata'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        # Usage logs are created automatically, not manually
        return False
    
    def has_change_permission(self, request, obj=None):
        # Usage logs should not be edited
        return False
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('api_key__organization')

