from django.contrib import admin
from apps.documents.models import Document, DocumentChunk


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['name', 'organization', 'file_type', 'status', 'size_bytes', 'upload_date']
    list_filter = ['status', 'file_type', 'organization', 'upload_date']
    search_fields = ['name', 'organization__name']
    readonly_fields = ['id', 'upload_date', 'url']
    ordering = ['-upload_date']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'organization')
        }),
        ('File Details', {
            'fields': ('file_type', 'size_bytes', 'url', 'upload_date')
        }),
        ('Processing', {
            'fields': ('status',)
        }),
    )


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['id', 'document', 'chunk_index', 'content_preview', 'has_embedding']
    list_filter = ['document__organization', 'document__status']
    search_fields = ['document__name', 'content']
    readonly_fields = ['id', 'embedding_display']
    ordering = ['document', 'chunk_index']
    
    def content_preview(self, obj):
        return obj.content[:100] + "..." if len(obj.content) > 100 else obj.content
    content_preview.short_description = 'Content Preview'
    
    def has_embedding(self, obj):
        return obj.embedding is not None and len(obj.embedding) > 0
    has_embedding.boolean = True
    has_embedding.short_description = 'Has Embedding'
    
    def embedding_display(self, obj):
        if obj.embedding is not None:
            return f"Vector ({len(obj.embedding)} dimensions): [{obj.embedding[:3].tolist()}...]"
        return "No embedding"
    embedding_display.short_description = 'Embedding Vector'
    
    fieldsets = (
        ('Chunk Information', {
            'fields': ('id', 'document', 'chunk_index')
        }),
        ('Content', {
            'fields': ('content',)
        }),
        ('Vector Data', {
            'fields': ('embedding_display',),
            'classes': ('collapse',)
        }),
    )
