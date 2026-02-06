"""
Proto Serializers for Identity Service domain.

These serializers are used by Django Socio gRPC to automatically
generate .proto files and handle serialization/deserialization
for gRPC communication.
"""
from django_socio_grpc import proto_serializers
from rest_framework import serializers

from apps.users.models import User
from apps.organizations.models import Organization


class UserProtoSerializer(proto_serializers.ModelProtoSerializer):
    """
    Proto serializer for User model.
    
    Exposes user data for gRPC communication while protecting
    sensitive fields like password.
    """
    organization_id = serializers.UUIDField(source='organization.id', read_only=True, allow_null=True)
    organization_name = serializers.CharField(source='organization.name', read_only=True, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            'id',
            'email', 
            'name',
            'role',
            'is_active',
            'organization_id',
            'organization_name',
        ]
        read_only_fields = ['id', 'organization_id', 'organization_name']


class UserCreateProtoSerializer(proto_serializers.ModelProtoSerializer):
    """Proto serializer for creating users via gRPC."""
    organization_id = serializers.UUIDField(required=False, allow_null=True)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'name', 'password', 'role', 'organization_id']
        
    def create(self, validated_data):
        organization_id = validated_data.pop('organization_id', None)
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            password=password,
            **validated_data
        )
        
        if organization_id:
            user.organization_id = organization_id
            user.save()
            
        return user


class OrganizationProtoSerializer(proto_serializers.ModelProtoSerializer):
    """
    Proto serializer for Organization model.
    
    Used for cross-service organization data retrieval and validation.
    """
    member_count = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = Organization
        fields = [
            'id',
            'name',
            'slug',
            'created_at',
            'updated_at',
            'member_count',
        ]
        read_only_fields = ['id', 'slug', 'created_at', 'updated_at', 'member_count']
    
    def get_member_count(self, obj) -> int:
        """Return the number of members in the organization."""
        return User.objects.filter(organization=obj).count()


class OrganizationCreateProtoSerializer(proto_serializers.ModelProtoSerializer):
    """Proto serializer for creating organizations via gRPC."""
    
    class Meta:
        model = Organization
        fields = ['name']


class ValidateAPIKeyRequestSerializer(proto_serializers.ProtoSerializer):
    """Request serializer for API key validation."""
    api_key = serializers.CharField()
    
    class Meta:
        fields = ['api_key']


class ValidateAPIKeyResponseSerializer(proto_serializers.ProtoSerializer):
    """Response serializer for API key validation."""
    is_valid = serializers.BooleanField()
    organization_id = serializers.CharField(allow_null=True)
    permissions = serializers.ListField(child=serializers.CharField(), required=False)
    error_message = serializers.CharField(allow_null=True, required=False)
    
    class Meta:
        fields = ['is_valid', 'organization_id', 'permissions', 'error_message']
