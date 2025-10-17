"""
Logging middleware for tracking all incoming and outgoing HTTP requests.
Logs requests/responses with timing, IP address, user info, and payload details.
"""
import json
import logging
import time
import uuid
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

from common.utils.logging_utils import get_client_ip, sanitize_headers, mask_sensitive_data


logger = logging.getLogger("cbaas.requests")


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all HTTP requests and responses with comprehensive details.
    
    Features:
    - Unique request ID for tracing
    - Request/response timing
    - User authentication info
    - IP address and user agent
    - Request/response headers and body (sanitized)
    - Error tracking and status codes
    - Performance metrics
    """
    
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.get_response = get_response
        
        # Configurable options
        self.log_request_body = getattr(settings, 'LOG_REQUEST_BODY', True)
        self.log_response_body = getattr(settings, 'LOG_RESPONSE_BODY', True)
        self.max_body_length = getattr(settings, 'LOG_MAX_BODY_LENGTH', 10000)
        self.excluded_paths = getattr(settings, 'LOG_EXCLUDED_PATHS', [
            '/health/',
            '/readiness/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ])
        self.excluded_content_types = getattr(settings, 'LOG_EXCLUDED_CONTENT_TYPES', [
            'image/',
            'video/',
            'audio/',
            'application/octet-stream',
        ])

    def process_request(self, request: HttpRequest) -> None:
        """Process incoming request and start logging."""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return
            
        # Generate unique request ID
        request.request_id = str(uuid.uuid4())
        request.start_time = time.time()
        
        # Extract request information
        request_data = self._extract_request_data(request)
        
        # Log incoming request
        logger.info(
            "Incoming Request",
            extra={
                "event_type": "request_started",
                "request_id": request.request_id,
                "method": request.method,
                "path": request.path,
                "query_string": request.GET.dict(),
                "user_id": getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                "user_email": getattr(request.user, 'email', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
                "ip_address": get_client_ip(request),
                "user_agent": request.META.get('HTTP_USER_AGENT', ''),
                "content_type": request.content_type,
                "content_length": request.META.get('CONTENT_LENGTH', 0),
                "headers": sanitize_headers(dict(request.headers)),
                "body": request_data.get('body') if self.log_request_body else None,
                "organization_id": getattr(request.user, 'organization_id', None) if hasattr(request, 'user') and hasattr(request.user, 'organization_id') else None,
            }
        )

    def process_response(self, request: HttpRequest, response: HttpResponse) -> HttpResponse:
        """Process outgoing response and complete logging."""
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.excluded_paths):
            return response
            
        # Skip if request doesn't have our tracking info
        if not hasattr(request, 'request_id'):
            return response
            
        # Calculate request duration
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        # Extract response information
        response_data = self._extract_response_data(response)
        
        # Determine log level based on status code
        log_level = self._get_log_level_for_status(response.status_code)
        
        # Log outgoing response
        logger.log(
            log_level,
            "Outgoing Response",
            extra={
                "event_type": "request_completed",
                "request_id": request.request_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "response_size": len(response.content) if hasattr(response, 'content') else 0,
                "content_type": response.get('Content-Type', ''),
                "headers": sanitize_headers(dict(response.items())),
                "body": response_data.get('body') if self.log_response_body else None,
                "user_id": getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else None,
                "ip_address": get_client_ip(request),
            }
        )
        
        return response

    def process_exception(self, request: HttpRequest, exception: Exception) -> None:
        """Process exceptions and log error details."""
        if not hasattr(request, 'request_id'):
            return
            
        duration = time.time() - getattr(request, 'start_time', time.time())
        
        logger.error(
            "Request Exception",
            extra={
                "event_type": "request_failed",
                "request_id": request.request_id,
                "method": request.method,
                "path": request.path,
                "duration_ms": round(duration * 1000, 2),
                "exception_type": type(exception).__name__,
                "exception_message": str(exception),
                "user_id": getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user and hasattr(request.user, 'is_authenticated') and request.user.is_authenticated else None,
                "ip_address": get_client_ip(request),
            },
            exc_info=True
        )

    def _extract_request_data(self, request: HttpRequest) -> Dict[str, Any]:
        """Extract and sanitize request data."""
        data = {}
        
        if self.log_request_body and request.content_type:
            # Skip binary content types
            if any(ct in request.content_type for ct in self.excluded_content_types):
                data['body'] = f"<Binary content: {request.content_type}>"
            else:
                try:
                    body = request.body.decode('utf-8')
                    if len(body) > self.max_body_length:
                        body = body[:self.max_body_length] + "...[truncated]"
                    
                    # Try to parse as JSON for better formatting
                    if 'application/json' in request.content_type:
                        try:
                            parsed_body = json.loads(body)
                            data['body'] = mask_sensitive_data(parsed_body)
                        except json.JSONDecodeError:
                            data['body'] = body
                    else:
                        data['body'] = mask_sensitive_data(body)
                except (UnicodeDecodeError, AttributeError):
                    data['body'] = "<Binary or undecodable content>"
        
        return data

    def _extract_response_data(self, response: HttpResponse) -> Dict[str, Any]:
        """Extract and sanitize response data."""
        data = {}
        
        if self.log_response_body:
            content_type = response.get('Content-Type', '')
            
            # Skip binary content types
            if any(ct in content_type for ct in self.excluded_content_types):
                data['body'] = f"<Binary content: {content_type}>"
            else:
                try:
                    if hasattr(response, 'content'):
                        content = response.content.decode('utf-8')
                        if len(content) > self.max_body_length:
                            content = content[:self.max_body_length] + "...[truncated]"
                        
                        # Try to parse as JSON for better formatting
                        if 'application/json' in content_type:
                            try:
                                parsed_content = json.loads(content)
                                data['body'] = mask_sensitive_data(parsed_content)
                            except json.JSONDecodeError:
                                data['body'] = content
                        else:
                            data['body'] = content
                except (UnicodeDecodeError, AttributeError):
                    data['body'] = "<Binary or undecodable content>"
        
        return data

    def _get_log_level_for_status(self, status_code: int) -> int:
        """Determine appropriate log level based on HTTP status code."""
        if 200 <= status_code < 300:
            return logging.INFO
        elif 300 <= status_code < 400:
            return logging.INFO
        elif 400 <= status_code < 500:
            return logging.WARNING
        else:
            return logging.ERROR
