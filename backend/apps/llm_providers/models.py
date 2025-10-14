import uuid
from django.db import models
from django.core.exceptions import ValidationError


class LLMProvider(models.Model):
    """
    Model to store LLM provider configurations (OpenAI, Gemini, DeepSeek, etc.)
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=50, 
        unique=True,
        help_text="Internal provider name (e.g., 'openai', 'gemini', 'deepseek')"
    )
    display_name = models.CharField(
        max_length=100,
        help_text="Human-readable provider name (e.g., 'OpenAI', 'Google Gemini')"
    )
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this provider is available for selection"
    )
    api_base_url = models.URLField(blank=True, null=True, help_text="Base URL for the provider's API")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'llm_providers'
        verbose_name = 'LLM Provider'
        verbose_name_plural = 'LLM Providers'
        ordering = ['display_name']

    def __str__(self):
        return f"{self.display_name} ({self.name})"

    def clean(self):
        """Validate the model before saving"""
        # Ensure name is lowercase and alphanumeric with underscores
        if self.name:
            if not self.name.replace('_', '').isalnum() or not self.name.islower():
                raise ValidationError(
                    "Provider name must be lowercase alphanumeric with underscores only"
                )

    def get_active_models(self):
        """Get all active models for this provider"""
        return self.models.filter(is_active=True)


class LLMModel(models.Model):
    """
    Model to store available models for each LLM provider
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider = models.ForeignKey(
        LLMProvider, 
        on_delete=models.CASCADE, 
        related_name='models'
    )
    name = models.CharField(
        max_length=100,
        help_text="Internal model name (e.g., 'gpt-4', 'gemini-pro')"
    )
    display_name = models.CharField(
        max_length=150,
        help_text="Human-readable model name (e.g., 'GPT-4', 'Gemini Pro')"
    )
    description = models.TextField(blank=True, null=True)
    context_window = models.IntegerField(
        blank=True, 
        null=True,
        help_text="Maximum context window size in tokens"
    )
    max_tokens = models.IntegerField(
        blank=True,
        null=True, 
        help_text="Maximum output tokens"
    )
    supports_streaming = models.BooleanField(default=True)
    supports_function_calling = models.BooleanField(default=False)
    cost_per_1k_input_tokens = models.DecimalField(
        max_digits=12, 
        decimal_places=8, 
        blank=True, 
        null=True,
        help_text="Cost per 1000 input tokens in USD"
    )
    cost_per_1k_output_tokens = models.DecimalField(
        max_digits=12, 
        decimal_places=8, 
        blank=True, 
        null=True,
        help_text="Cost per 1000 output tokens in USD"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this model is available for selection"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this is the default model for the provider"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'llm_models'
        verbose_name = 'LLM Model'
        verbose_name_plural = 'LLM Models'
        unique_together = ['provider', 'name']
        ordering = ['provider__display_name', 'display_name']

    def __str__(self):
        return f"{self.provider.display_name} - {self.display_name}"

    def clean(self):
        """Validate the model before saving"""
        # Ensure only one default model per provider
        if self.is_default:
            existing_default = LLMModel.objects.filter(
                provider=self.provider,
                is_default=True
            ).exclude(pk=self.pk)
            
            if existing_default.exists():
                raise ValidationError(
                    f"Provider {self.provider.display_name} already has a default model"
                )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def full_name(self):
        """Returns provider_name/model_name format"""
        return f"{self.provider.name}/{self.name}"
