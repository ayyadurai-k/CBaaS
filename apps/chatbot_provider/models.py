import uuid
from django.db import models
from common.security.encryption import Encryptor

class ChatbotProvider(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chatbot = models.ForeignKey('chatbot.Chatbot', on_delete=models.CASCADE)
    provider = models.CharField(max_length=20, choices=[("openai","openai"),("gemini","gemini"),("deepseek","deepseek")])
    model_name = models.CharField(max_length=50)
    api_key_encrypted = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    @property
    def api_key(self) -> str:
        return Encryptor.decrypt(self.api_key_encrypted)
    @api_key.setter
    def api_key(self, value: str):
        self.api_key_encrypted = Encryptor.encrypt(value)