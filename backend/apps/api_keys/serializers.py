from rest_framework import serializers
from django.utils import timezone
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
            "updated_at",
            "last_used_at",
            "expires_at",
            "allowed_ips",
            "rate_limit_per_minute",
            "metadata",
            "revoked_reason",
            "plaintext",
        ]
        read_only_fields = [
            "id", 
            "status", 
            "usage_count", 
            "created_at", 
            "updated_at",
            "last_used_at",
            "plaintext"
        ]


class APIKeyCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    quota = serializers.IntegerField(required=False, min_value=1)
    scope = serializers.ChoiceField(
        choices=APIKey.Scope.choices, default=APIKey.Scope.FULL
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)
    allowed_ips = serializers.ListField(
        child=serializers.CharField(), 
        required=False, 
        allow_empty=True
    )
    rate_limit_per_minute = serializers.IntegerField(
        required=False, 
        min_value=1, 
        allow_null=True
    )
    metadata = serializers.JSONField(required=False)

    def validate_name(self, value):
        org = self.context["request"].user.organization
        if APIKey.objects.filter(organization=org, name=value).exists():
            raise serializers.ValidationError("API key with this name already exists.")
        return value
    
    def validate_expires_at(self, value):
        """Ensure expiration date is in the future"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Expiration date must be in the future")
        return value
    
    def validate_allowed_ips(self, value):
        """Basic IP address validation"""
        import ipaddress
        for ip in value:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise serializers.ValidationError(f"Invalid IP address: {ip}")
        return value

    def create(self, validated):
        org = self.context["request"].user.organization
        key = APIKey(
            organization=org,
            name=validated["name"],
            quota=validated.get("quota"),
            scope=validated["scope"],
            expires_at=validated.get("expires_at"),
            allowed_ips=validated.get("allowed_ips", []),
            rate_limit_per_minute=validated.get("rate_limit_per_minute"),
            metadata=validated.get("metadata", {}),
        )
        raw = APIKey.generate_plaintext()
        key.key = raw
        key.save()
        key._plaintext = raw
        return key
