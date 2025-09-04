"""
Logging utilities for sanitizing and extracting request/response data.
"""
import re
from typing import Any, Dict, List, Union


def get_client_ip(request) -> str:
    """
    Extract the real client IP address from request headers.
    Handles common proxy headers and load balancers.
    """
    # Check for forwarded headers (common in load balancers)
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        ip = x_forwarded_for.split(',')[0].strip()
        if ip:
            return ip
    
    # Check other common headers
    headers_to_check = [
        'HTTP_X_REAL_IP',
        'HTTP_X_CLIENT_IP',
        'HTTP_CF_CONNECTING_IP',  # Cloudflare
        'HTTP_TRUE_CLIENT_IP',    # Akamai
        'HTTP_X_CLUSTER_CLIENT_IP',
    ]
    
    for header in headers_to_check:
        ip = request.META.get(header)
        if ip:
            return ip.strip()
    
    # Fallback to REMOTE_ADDR
    return request.META.get('REMOTE_ADDR', 'unknown')


def sanitize_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """
    Sanitize HTTP headers by masking sensitive information.
    """
    sensitive_headers = {
        'authorization',
        'x-api-key',
        'cookie',
        'set-cookie',
        'x-csrf-token',
        'x-csrftoken',
    }
    
    sanitized = {}
    for key, value in headers.items():
        key_lower = key.lower()
        if key_lower in sensitive_headers:
            if value:
                # Show first and last few characters for debugging
                if len(value) > 8:
                    sanitized[key] = f"{value[:4]}***{value[-4:]}"
                else:
                    sanitized[key] = "***"
            else:
                sanitized[key] = value
        else:
            sanitized[key] = value
    
    return sanitized


def mask_sensitive_data(data: Union[str, Dict, List]) -> Union[str, Dict, List]:
    """
    Recursively mask sensitive data in strings, dictionaries, and lists.
    """
    if isinstance(data, dict):
        return {key: mask_sensitive_data(value) if not _is_sensitive_key(key) 
                else _mask_value(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]
    elif isinstance(data, str):
        return _mask_sensitive_patterns(data)
    else:
        return data


def _is_sensitive_key(key: str) -> bool:
    """
    Check if a dictionary key contains sensitive information.
    """
    sensitive_keys = {
        'password',
        'passwd',
        'pwd',
        'secret',
        'token',
        'key',
        'api_key',
        'apikey',
        'auth',
        'authorization',
        'credit_card',
        'creditcard',
        'card_number',
        'cardnumber',
        'ssn',
        'social_security',
        'cvv',
        'cvc',
        'pin',
        'private',
        'confidential',
    }
    
    key_lower = key.lower()
    return any(sensitive in key_lower for sensitive in sensitive_keys)


def _mask_value(value: Any) -> str:
    """
    Mask a sensitive value while preserving some information for debugging.
    """
    if value is None:
        return None
    
    value_str = str(value)
    if len(value_str) <= 4:
        return "***"
    elif len(value_str) <= 8:
        return f"{value_str[:1]}***{value_str[-1:]}"
    else:
        return f"{value_str[:2]}***{value_str[-2:]}"


def _mask_sensitive_patterns(text: str) -> str:
    """
    Mask sensitive patterns in text using regex.
    """
    # Email addresses
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                  lambda m: f"{m.group(0)[:3]}***@{m.group(0).split('@')[1]}", text)
    
    # Credit card numbers (basic pattern)
    text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', 
                  '****-****-****-****', text)
    
    # Phone numbers
    text = re.sub(r'\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b', 
                  '***-***-****', text)
    
    # SSN pattern
    text = re.sub(r'\b\d{3}[\s-]?\d{2}[\s-]?\d{4}\b', 
                  '***-**-****', text)
    
    return text


# Structured logging formatters
class StructuredLogFormatter:
    """
    Formatter for structured logging with consistent field naming.
    """
    
    @staticmethod
    def format_request_log(request_id: str, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """Format a request log entry."""
        log_entry = {
            'timestamp': kwargs.get('timestamp'),
            'event_type': 'http_request',
            'request_id': request_id,
            'method': method,
            'path': path,
            'level': kwargs.get('level', 'INFO'),
        }
        
        # Add optional fields
        optional_fields = [
            'user_id', 'user_email', 'organization_id', 'ip_address', 
            'user_agent', 'query_params', 'headers', 'body', 'content_type'
        ]
        
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                log_entry[field] = kwargs[field]
        
        return log_entry
    
    @staticmethod
    def format_response_log(request_id: str, method: str, path: str, status_code: int, 
                          duration_ms: float, **kwargs) -> Dict[str, Any]:
        """Format a response log entry."""
        log_entry = {
            'timestamp': kwargs.get('timestamp'),
            'event_type': 'http_response', 
            'request_id': request_id,
            'method': method,
            'path': path,
            'status_code': status_code,
            'duration_ms': duration_ms,
            'level': kwargs.get('level', 'INFO'),
        }
        
        # Add optional fields
        optional_fields = [
            'user_id', 'ip_address', 'response_size', 'headers', 'body', 'content_type'
        ]
        
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                log_entry[field] = kwargs[field]
                
        return log_entry
    
    @staticmethod
    def format_error_log(request_id: str, method: str, path: str, error: Exception, 
                        duration_ms: float, **kwargs) -> Dict[str, Any]:
        """Format an error log entry."""
        log_entry = {
            'timestamp': kwargs.get('timestamp'),
            'event_type': 'http_error',
            'request_id': request_id,
            'method': method,
            'path': path,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'duration_ms': duration_ms,
            'level': 'ERROR',
        }
        
        # Add optional fields
        optional_fields = ['user_id', 'ip_address', 'stack_trace']
        
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                log_entry[field] = kwargs[field]
                
        return log_entry
