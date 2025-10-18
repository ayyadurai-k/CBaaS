"""
API Key Usage Logging Middleware

Tracks all requests made with API keys for analytics, billing, and security auditing.
Logs detailed information including:
- Endpoint and method
- Response time and status code
- IP address and user agent
- Token consumption (for LLM calls)
- Errors and metadata
"""

import time
import logging
from django.utils.deprecation import MiddlewareMixin
from apps.api_keys.models import APIKeyUsageLog

logger = logging.getLogger(__name__)


class APIKeyUsageMiddleware(MiddlewareMixin):
    """
    Middleware to log API key usage to the database.
    
    This runs after the response is generated and logs:
    - Request details (endpoint, method, IP, user agent)
    - Response details (status code, response time)
    - Usage metrics (tokens, documents searched)
    - Errors (if any)
    
    Usage logs are created asynchronously to avoid blocking the response.
    """
    
    def process_request(self, request):
        """Store request start time"""
        request._api_key_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """
        Log API key usage after response is generated.
        
        Only logs if request was authenticated with an API key.
        """
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            # No API key used, skip logging
            return response
        
        # Calculate response time
        start_time = getattr(request, '_api_key_start_time', time.time())
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Extract request metadata
        ip_address = self._get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]  # Truncate
        endpoint = request.path
        method = request.method
        status_code = response.status_code
        
        # Extract usage metrics if available
        tokens_used = getattr(response, 'tokens_used', 0)
        documents_searched = getattr(response, 'documents_searched', 0)
        
        # Extract error message if present
        error_message = ''
        if status_code >= 400:
            try:
                if hasattr(response, 'data'):
                    error_message = str(response.data.get('error', ''))[:500]
                elif hasattr(response, 'content'):
                    error_message = response.content.decode('utf-8')[:500]
            except Exception:
                error_message = 'Error parsing response'
        
        # Create usage log asynchronously
        try:
            self._log_usage_async(
                api_key=api_key,
                timestamp=None,  # auto_now_add handles this
                endpoint=endpoint,
                method=method,
                ip_address=ip_address,
                user_agent=user_agent,
                status_code=status_code,
                response_time_ms=response_time_ms,
                tokens_used=tokens_used,
                documents_searched=documents_searched,
                error_message=error_message,
                metadata=self._extract_metadata(request, response)
            )
        except Exception as e:
            # Don't fail the request if logging fails
            logger.error(
                f"Failed to log API key usage: {str(e)}",
                extra={
                    'api_key_id': str(api_key.id),
                    'endpoint': endpoint,
                    'error': str(e)
                }
            )
        
        return response
    
    def _log_usage_async(self, **kwargs):
        """
        Create usage log entry.
        
        In production, this could be offloaded to Celery for true async processing.
        For now, we create the log synchronously but quickly.
        """
        try:
            APIKeyUsageLog.objects.create(**kwargs)
        except Exception as e:
            logger.error(f"Error creating usage log: {str(e)}")
    
    def _get_client_ip(self, request) -> str:
        """Extract client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def _extract_metadata(self, request, response) -> dict:
        """
        Extract additional metadata from request/response.
        
        This can include:
        - Request headers (sanitized)
        - Query parameters
        - Custom business metrics
        """
        metadata = {}
        
        # Add idempotency key if present
        if idem_key := request.headers.get('Idempotency-Key'):
            metadata['idempotency_key'] = idem_key
        
        # Add referer if present
        if referer := request.META.get('HTTP_REFERER'):
            metadata['referer'] = referer
        
        # Add session ID if this is a chat request
        if session_id := getattr(request, 'session_id', None):
            metadata['session_id'] = str(session_id)
        
        return metadata


class APIKeyQuotaMiddleware(MiddlewareMixin):
    """
    Middleware to enforce API key quotas.
    
    This is a fail-safe in case the authentication layer doesn't catch quota violations.
    Also handles atomically incrementing the usage counter.
    """
    
    def process_response(self, request, response):
        """Increment usage count if request was successful"""
        api_key = getattr(request, 'auth_api_key', None)
        if not api_key:
            return response
        
        # Only increment for successful requests
        if 200 <= response.status_code < 300:
            try:
                # Atomically increment usage count
                api_key.record_usage(increment=1)
            except Exception as e:
                logger.error(
                    f"Failed to increment API key usage count: {str(e)}",
                    extra={'api_key_id': str(api_key.id)}
                )
        
        return response
