from rest_framework import serializers
from .models import APIKey


class APIKeySerializer(serializers.ModelSerializer):
    plaintext = serializers.CharField(read_only=True)

    class Meta:
        model = APIKey
        fields = [
            "id",
            "name",
            "status",
            "usage_count",
            "quota",
            "scope",
            "created_at",
            "plaintext",
        ]
        read_only_fields = ["id", "status", "usage_count", "created_at", "plaintext"]


class APIKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    quota = serializers.IntegerField(required=False, min_value=1)
    scope = serializers.ChoiceField(
        choices=APIKey.Scope.choices, default=APIKey.Scope.FULL
    )

    def create(self, validated):
        org = self.context["request"].user.organization
        key = APIKey(
            organization=org,
            name=validated["name"],
            quota=validated.get("quota"),
            scope=validated["scope"],
        )
        raw = APIKey.generate_plaintext()
        key.key = raw
        key.save()
        key.plaintext = raw
        return key
