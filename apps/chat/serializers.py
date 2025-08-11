from rest_framework import serializers
from django.conf import settings

MAX_MESSAGES = 40
MAX_MESSAGE_CHARS = 8000
MAX_TOTAL_CHARS = 20000

class MessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["system", "user", "assistant"])
    content = serializers.CharField() # Max length enforced in validate

class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    messages = MessageSerializer(many=True)
    max_tokens = serializers.IntegerField(required=False, min_value=16, max_value=4096, default=512)
    temperature = serializers.FloatField(required=False, min_value=0.0, max_value=2.0, default=0.2)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20, default=6)
    filters = serializers.DictField(required=False)
    metadata = serializers.DictField(required=False)

    def validate(self, data):
        messages = data.get("messages", [])
        if len(messages) > MAX_MESSAGES:
            raise serializers.ValidationError(f"Too many messages. Max is {MAX_MESSAGES}.")

        total_chars = 0
        for message in messages:
            content_len = len(message.get("content", ""))
            if content_len > MAX_MESSAGE_CHARS:
                raise serializers.ValidationError(f"Message content too long. Max is {MAX_MESSAGE_CHARS} characters per message.")
            total_chars += content_len
        
        if total_chars > MAX_TOTAL_CHARS:
            raise serializers.ValidationError(f"Total message content too long. Max is {MAX_TOTAL_CHARS} characters.")

        top_k = data.get("top_k")
        if top_k is not None and top_k > settings.TOP_K:
            raise serializers.ValidationError(f"top_k exceeds maximum allowed. Max is {settings.TOP_K}.")

        return data

class ChatResponseCitationSerializer(serializers.Serializer):
    doc_id = serializers.CharField()
    chunk_index = serializers.IntegerField()
    score = serializers.FloatField()

class ChatResponseSerializer(serializers.Serializer):
    id = serializers.CharField()
    session_id = serializers.CharField(allow_null=True)
    model = serializers.CharField()
    created = serializers.DateTimeField()
    answer = serializers.CharField()
    citations = ChatResponseCitationSerializer(many=True)
    usage = serializers.DictField()
    latency_ms = serializers.IntegerField(min_value=0)
