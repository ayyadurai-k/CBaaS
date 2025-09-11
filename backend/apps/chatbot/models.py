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
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
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
    llm_api_key_encrypted = models.CharField(max_length=255, null=True, blank=True)
    llm_system_prompt = models.TextField(blank=True, default="")
    llm_is_active = models.BooleanField(default=True, db_index=True)
    
    # Document connections
    documents_connected = models.ManyToManyField(
        'documents.Document',
        blank=True,
        related_name='connected_chatbots',
        help_text="Documents that this chatbot can access for RAG"
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

    def __str__(self) -> str:
        return f"{self.name} ({self.organization.name})"

    class Meta:
        unique_together = [('organization',)]  # One chatbot per organization
        indexes = [
            models.Index(fields=['organization', 'created_at']),
        ]