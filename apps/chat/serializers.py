from rest_framework import serializers

class MessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=["system", "user", "assistant"])
    content = serializers.CharField(max_length=10000)

class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    messages = MessageSerializer(many=True)
    max_tokens = serializers.IntegerField(required=False, min_value=16, max_value=4096, default=512)
    temperature = serializers.FloatField(required=False, min_value=0.0, max_value=2.0, default=0.2)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=20, default=6)
    filters = serializers.DictField(required=False)
    metadata = serializers.DictField(required=False)

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
