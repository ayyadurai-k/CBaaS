import uuid
from django.db import models
from common.security.encryption import Encryptor


class Chatbot(models.Model):
    TONE_CHOICES = [
        ("friendly", "Friendly"),
        ("technical", "Technical"),
        ("formal", "Formal"),
        ("professional", "Professional"),
    ]
    
    PROVIDER_CHOICES = [
        ("openai", "OpenAI"),
        ("gemini", "Gemini"),
        ("deepseek", "DeepSeek"),
    ]

    # Basic chatbot configuration
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Cross-service reference (Phase 1: soft reference to Identity Service)
    # In Phase 2+, this will be validated via Identity Service API
    organization_id = models.UUIDField(
        db_index=True,
        help_text="Reference to Organization in Identity Service"
    )
    
    name = models.CharField(max_length=100)
    tone = models.CharField(max_length=20, choices=TONE_CHOICES, default="technical")
    system_instructions = models.TextField()
    
    # LLM Provider configuration (merged from chatbot_provider)
    llm_provider = models.CharField(
        max_length=20, 
        choices=PROVIDER_CHOICES, 
        null=True, 
        blank=True
    )
    llm_model = models.CharField(max_length=50, null=True, blank=True)
    llm_api_key_encrypted = models.CharField(max_length=512, null=True, blank=True)
    llm_system_prompt = models.TextField(blank=True, default="")
    llm_is_active = models.BooleanField(default=True, db_index=True)
    
    # Cross-service document references
    # Stores list of document UUIDs from Knowledge Service
    # In Phase 2+, document existence is validated via Knowledge Service API
    connected_document_ids = models.JSONField(
        default=list,
        blank=True,
        help_text="List of Document UUIDs from Knowledge Service"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def llm_api_key(self) -> str:
        """Decrypt and return the LLM API key."""
        if not self.llm_api_key_encrypted:
            return ""
        return Encryptor.decrypt(self.llm_api_key_encrypted)

    @llm_api_key.setter
    def llm_api_key(self, value: str):
        """Encrypt and store the LLM API key."""
        if value:
            self.llm_api_key_encrypted = Encryptor.encrypt(value)
        else:
            self.llm_api_key_encrypted = None
    
    # Helper methods for cross-service data access
    def get_organization(self):
        """Fetch organization data via Identity Service."""
        from common.services import get_identity_service
        return get_identity_service().get_organization(str(self.organization_id))
    
    def get_connected_documents(self):
        """Fetch connected documents via Knowledge Service."""
        from common.services import get_knowledge_service
        knowledge_service = get_knowledge_service()
        return [
            knowledge_service.get_document(doc_id) 
            for doc_id in self.connected_document_ids
        ]

    def __str__(self) -> str:
        org = self.get_organization()
        org_name = org.name if org else "Unknown"
        return f"{self.name} ({org_name})"

    class Meta:
        indexes = [
            models.Index(fields=['organization_id', 'created_at']),
        ]