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


class APIKeyUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating existing API keys.
    
    Security principles:
    - Never allow key regeneration (use separate endpoint)
    - Scope can only be downgraded (FULL → READ_ONLY → UPLOAD_ONLY)
    - Expiration can't be set to past dates
    - IP whitelist must be valid IPv4/IPv6
    """
    
    class Meta:
        model = APIKey
        fields = [
            'name',
            'scope', 
            'allowed_ips',
            'rate_limit_per_minute',
            'expires_at',
            'quota',
            'metadata'
        ]
    
    def validate_name(self, value):
        """Ensure unique name (excluding current instance)"""
        instance = self.instance
        org = self.context["request"].user.organization
        if APIKey.objects.exclude(id=instance.id).filter(
            organization=org, name=value
        ).exists():
            raise serializers.ValidationError(
                "An API key with this name already exists."
            )
        return value
    
    def validate_scope(self, value):
        """
        Only allow scope DOWNGRADE for security.
        
        Rationale: Upgrading permissions without re-authentication 
        could be exploited if key is compromised.
        """
        instance = self.instance
        current_scope = instance.scope
        
        # Define scope hierarchy (higher = more permissions)
        scope_hierarchy = {
            APIKey.Scope.READ_ONLY: 1,
            APIKey.Scope.UPLOAD_ONLY: 2,
            APIKey.Scope.FULL: 3
        }
        
        current_level = scope_hierarchy.get(current_scope, 0)
        new_level = scope_hierarchy.get(value, 0)
        
        if new_level > current_level:
            raise serializers.ValidationError(
                f"Cannot upgrade scope from '{current_scope}' to '{value}'. "
                f"Generate a new API key with higher permissions instead."
            )
        
        return value
    
    def validate_expires_at(self, value):
        """Prevent setting expiration to past date"""
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                "Expiration date must be in the future."
            )
        return value
    
    def validate_allowed_ips(self, value):
        """Validate IP address format"""
        if not value:
            return []  # Empty list = allow all IPs
        
        import ipaddress
        validated_ips = []
        for ip in value:
            ip_str = ip.strip()
            if not ip_str:
                continue
                
            try:
                # Validate IP address or CIDR notation
                ipaddress.ip_network(ip_str, strict=False)
                validated_ips.append(ip_str)
            except ValueError:
                raise serializers.ValidationError(
                    f"Invalid IP address or CIDR: '{ip_str}'. "
                    f"Use format like '192.168.1.1' or '10.0.0.0/24'"
                )
        
        return validated_ips
    
    def validate_rate_limit_per_minute(self, value):
        """Ensure rate limit is reasonable"""
        if value is not None and value < 1:
            raise serializers.ValidationError(
                "Rate limit must be at least 1 request per minute."
            )
        return value
    
    def validate_quota(self, value):
        """Prevent setting quota below current usage"""
        instance = self.instance
        if value is not None and value < instance.usage_count:
            raise serializers.ValidationError(
                f"Quota ({value}) cannot be less than current usage ({instance.usage_count})."
            )
        return value
