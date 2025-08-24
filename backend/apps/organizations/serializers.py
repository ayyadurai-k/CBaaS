from rest_framework import serializers
from .models import Organization

class UpdateOrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["name", "logo_url"]
