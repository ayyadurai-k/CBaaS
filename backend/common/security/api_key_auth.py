from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from apps.api_keys.models import APIKey


class APIKeyAuthentication(BaseAuthentication):
    keyword = "X-API-Key"

    def authenticate(self, request):
        key = request.headers.get(self.keyword)
        if not key:
            return None
        try:
            api_key = APIKey.objects.select_related("organization").get_plaintext(key)
        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed("Invalid API key")
        if api_key.status != APIKey.Status.ACTIVE:
            raise exceptions.AuthenticationFailed("API key revoked")
        if api_key.quota is not None and api_key.usage_count >= api_key.quota:
            raise exceptions.AuthenticationFailed("API key quota exceeded")
        request.organization = api_key.organization
        request.auth_api_key = api_key
        return (None, None)
