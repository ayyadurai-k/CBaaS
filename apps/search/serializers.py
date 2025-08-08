from rest_framework import serializers

class SearchRequestSerializer(serializers.Serializer):
    query = serializers.CharField(max_length=4000)
    top_k = serializers.IntegerField(required=False, min_value=1, max_value=50, default=8)
    filters = serializers.DictField(required=False)

class SearchResultSerializer(serializers.Serializer):
    document_id = serializers.CharField()
    chunk_index = serializers.IntegerField()
    content = serializers.CharField()
    score = serializers.FloatField()

class SearchResponseSerializer(serializers.Serializer):
    results = SearchResultSerializer(many=True)
