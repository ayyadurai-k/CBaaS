import uuid
from django.db import models

class Chatbot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    tone = models.CharField(max_length=20, choices=[("Friendly","Friendly"),("Technical","Technical"),("Formal","Formal")], default="Technical")
    system_instructions = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)