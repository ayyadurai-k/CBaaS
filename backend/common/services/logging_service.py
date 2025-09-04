"""
Centralized logging service for CBaaS applications.
Provides high-level logging methods for common scenarios.
"""
import logging
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union

from django.conf import settings
from django.http import HttpRequest

from common.utils.logging_config import get_logger


class LoggingService:
    """
    Centralized logging service with structured logging capabilities.
    """
    
    def __init__(self):
        self.logger = get_logger('service')
        
    def log_api_request(self, request: HttpRequest, view_name: str = None, **kwargs):
        """Log an API request with structured data."""
        request_id = getattr(request, 'request_id', 'unknown')
        
        self.logger.log_request(
            request_id=request_id,
            method=request.method,
            path=request.path,
            view_name=view_name,
            user_id=getattr(request.user, 'id', None) if hasattr(request, 'user') and request.user.is_authenticated else None,
            organization_id=getattr(request.user, 'organization_id', None) if hasattr(request, 'user') and hasattr(request.user, 'organization_id') else None,
            **kwargs
        )
    
    def log_api_response(self, request: HttpRequest, response, duration_ms: float, **kwargs):
        """Log an API response with structured data."""
        request_id = getattr(request, 'request_id', 'unknown')
        status_code = getattr(response, 'status_code', 0)
        
        self.logger.log_response(
            request_id=request_id,
            method=request.method,
            path=request.path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def log_business_event(self, event_type: str, message: str, request_id: str = None, **context):
        """Log business logic events."""
        self.logger.logger.info(
            message,
            extra={
                'event_type': f'business.{event_type}',
                'request_id': request_id,
                **context
            }
        )
    
    def log_security_event(self, event_type: str, message: str, request: HttpRequest = None, 
                          severity: str = 'warning', **context):
        """Log security-related events."""
        request_id = getattr(request, 'request_id', None) if request else None
        ip_address = self._get_client_ip(request) if request else None
        user_id = getattr(request.user, 'id', None) if request and hasattr(request, 'user') and request.user.is_authenticated else None
        
        self.logger.log_security_event(
            event_type=f'security.{event_type}',
            message=message,
            request_id=request_id,
            severity=severity,
            ip_address=ip_address,
            user_id=user_id,
            **context
        )
    
    def log_data_access(self, operation: str, table: str, record_id: str = None, 
                       request: HttpRequest = None, **context):
        """Log data access operations."""
        request_id = getattr(request, 'request_id', None) if request else None
        user_id = getattr(request.user, 'id', None) if request and hasattr(request, 'user') and request.user.is_authenticated else None
        
        self.logger.logger.info(
            f"Data {operation}: {table}" + (f" (ID: {record_id})" if record_id else ""),
            extra={
                'event_type': f'data.{operation}',
                'request_id': request_id,
                'user_id': user_id,
                'table': table,
                'record_id': record_id,
                **context
            }
        )
    
    def log_external_api_call(self, service: str, method: str, url: str, status_code: int, 
                             duration_ms: float, request_id: str = None, **context):
        """Log external API calls."""
        level = logging.INFO if 200 <= status_code < 400 else logging.WARNING
        
        self.logger.logger.log(
            level,
            f"External API {method} {service}: {status_code} ({duration_ms}ms)",
            extra={
                'event_type': 'external_api_call',
                'request_id': request_id,
                'service': service,
                'method': method,
                'url': url,
                'status_code': status_code,
                'duration_ms': duration_ms,
                **context
            }
        )
    
    def log_celery_task(self, task_name: str, task_id: str, status: str, 
                       duration_ms: float = None, **context):
        """Log Celery task execution."""
        message = f"Celery task {task_name} [{task_id}]: {status}"
        if duration_ms:
            message += f" ({duration_ms}ms)"
            
        level = logging.INFO if status in ['started', 'completed'] else logging.ERROR
        
        self.logger.logger.log(
            level,
            message,
            extra={
                'event_type': 'celery_task',
                'task_name': task_name,
                'task_id': task_id,
                'status': status,
                'duration_ms': duration_ms,
                **context
            }
        )
    
    def log_error(self, error: Exception, message: str = None, request: HttpRequest = None, **context):
        """Log application errors with full context."""
        request_id = getattr(request, 'request_id', None) if request else None
        user_id = getattr(request.user, 'id', None) if request and hasattr(request, 'user') and request.user.is_authenticated else None
        
        error_message = message or f"{type(error).__name__}: {str(error)}"
        
        self.logger.log_error(
            message=error_message,
            request_id=request_id,
            user_id=user_id,
            error_type=type(error).__name__,
            error_message=str(error),
            **context
        )
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request."""
        from common.utils.logging_utils import get_client_ip
        return get_client_ip(request)


# Global logging service instance
logging_service = LoggingService()


# Decorators for automatic logging
def log_api_call(view_name: str = None, log_request_body: bool = None, log_response_body: bool = None):
    """
    Decorator to automatically log API calls.
    
    Args:
        view_name: Name of the view/endpoint
        log_request_body: Whether to log request body (overrides global setting)
        log_response_body: Whether to log response body (overrides global setting)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            start_time = time.time()
            
            # Determine actual view name
            actual_view_name = view_name or func.__name__
            
            # Log request
            request_context = {}
            if log_request_body or (log_request_body is None and settings.LOG_REQUEST_BODY):
                # Add request body if configured
                pass  # Body logging is handled by middleware
                
            logging_service.log_api_request(
                request=request,
                view_name=actual_view_name,
                **request_context
            )
            
            try:
                # Execute the view
                response = func(request, *args, **kwargs)
                
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log response
                response_context = {}
                if log_response_body or (log_response_body is None and settings.LOG_RESPONSE_BODY):
                    # Add response body if configured
                    pass  # Body logging is handled by middleware
                
                logging_service.log_api_response(
                    request=request,
                    response=response,
                    duration_ms=duration_ms,
                    view_name=actual_view_name,
                    **response_context
                )
                
                return response
                
            except Exception as e:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000
                
                # Log error
                logging_service.log_error(
                    error=e,
                    message=f"Error in {actual_view_name}",
                    request=request,
                    view_name=actual_view_name,
                    duration_ms=duration_ms
                )
                
                # Re-raise the exception
                raise
                
        return wrapper
    return decorator


def log_performance(operation_name: str = None):
    """
    Decorator to log performance metrics for functions.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            actual_operation_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logging_service.logger.log_performance(
                    operation=actual_operation_name,
                    duration_ms=duration_ms,
                    status='success'
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logging_service.logger.log_performance(
                    operation=actual_operation_name,
                    duration_ms=duration_ms,
                    status='error',
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                
                raise
                
        return wrapper
    return decorator


def log_data_operation(operation: str, table: str = None):
    """
    Decorator to log data access operations.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Try to extract request from args if available
            request = None
            for arg in args:
                if hasattr(arg, 'META') and hasattr(arg, 'method'):
                    request = arg
                    break
            
            actual_table = table or func.__name__
            
            try:
                result = func(*args, **kwargs)
                
                # Try to extract record ID from result
                record_id = None
                if hasattr(result, 'id'):
                    record_id = str(result.id)
                elif hasattr(result, 'pk'):
                    record_id = str(result.pk)
                
                logging_service.log_data_access(
                    operation=operation,
                    table=actual_table,
                    record_id=record_id,
                    request=request,
                    status='success'
                )
                
                return result
                
            except Exception as e:
                logging_service.log_data_access(
                    operation=operation,
                    table=actual_table,
                    request=request,
                    status='error',
                    error_type=type(e).__name__,
                    error_message=str(e)
                )
                
                raise
                
        return wrapper
    return decorator
