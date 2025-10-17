import logging
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from apps.api_keys.models import APIKey

logger = logging.getLogger(__name__)


class APIKeyAuthentication(BaseAuthentication):
    """
    API Key authentication using X-API-Key header.
    
    Provides comprehensive security checks:
    - Constant-time key lookup via HMAC
    - Status validation (active/revoked/expired)
    - Quota enforcement
    - IP whitelisting support
    - Detailed audit logging
    
    Sets request.organization and request.auth_api_key for downstream use.
    """
    keyword = "X-API-Key"

    def authenticate(self, request):
        """
        Authenticate the request using API key.
        
        Returns:
            None if no API key provided (allows JWT fallback)
            (None, None) if authentication succeeds
            
        Raises:
            AuthenticationFailed with detailed error message
        """
        key = request.headers.get(self.keyword)
        if not key:
            return None  # No API key provided, allow other auth methods
        
        # Get client IP address
        ip_address = self._get_client_ip(request)
        
        # Attempt to find and validate the key
        try:
            api_key = APIKey.get_by_plaintext(key)
        except APIKey.DoesNotExist:
            logger.warning(
                f"Invalid API key attempt from IP {ip_address}",
                extra={
                    'ip_address': ip_address,
                    'path': request.path,
                    'method': request.method
                }
            )
            raise exceptions.AuthenticationFailed("Invalid API key")
        
        # Comprehensive validation using model method
        is_valid, error_message = api_key.can_be_used()
        if not is_valid:
            logger.warning(
                f"API key validation failed: {error_message}",
                extra={
                    'api_key_id': str(api_key.id),
                    'api_key_name': api_key.name,
                    'organization': api_key.organization.name,
                    'ip_address': ip_address,
                    'error': error_message
                }
            )
            raise exceptions.AuthenticationFailed(error_message)
        
        # IP whitelisting check
        if not api_key.is_ip_allowed(ip_address):
            logger.warning(
                f"API key used from unauthorized IP: {ip_address}",
                extra={
                    'api_key_id': str(api_key.id),
                    'api_key_name': api_key.name,
                    'organization': api_key.organization.name,
                    'ip_address': ip_address,
                    'allowed_ips': api_key.allowed_ips
                }
            )
            raise exceptions.AuthenticationFailed(
                f"API key not authorized from IP address {ip_address}"
            )
        
        # Set organization and API key on request for downstream use
        request.organization = api_key.organization
        request.auth_api_key = api_key
        request.client_ip = ip_address
        
        logger.info(
            f"API key authentication successful",
            extra={
                'api_key_id': str(api_key.id),
                'api_key_name': api_key.name,
                'organization': api_key.organization.name,
                'scope': api_key.scope,
                'ip_address': ip_address
            }
        )
        
        # Return None for user since API keys are not user-based
        # DRF will use request.organization for authorization
        return (None, None)

    def _get_client_ip(self, request) -> str:
        """
        Extract client IP address from request.
        Handles X-Forwarded-For header for proxied requests.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Take the first IP in the chain (client IP)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '')
        return ip

    def authenticate_header(self, request):
        """
        Return a string to use as the value of the WWW-Authenticate
        header in a 401 Unauthenticated response.
        """
        return self.keyword

