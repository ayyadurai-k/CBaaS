"""
Centralized logging configuration for CBaaS backend.
Provides structured JSON logging with different handlers for various log types.
"""
import os
import sys
from pathlib import Path


def get_logging_config():
    """
    Get comprehensive logging configuration.
    
    Features:
    - Structured JSON logging
    - Separate log files for different log types
    - Console logging for development
    - Proper log rotation
    - Security-focused sanitization
    - Performance monitoring
    """
    
    # Base directory for logs
    log_dir = Path(os.environ.get('LOG_DIR', 'logs'))
    log_dir.mkdir(exist_ok=True)
    
    # Log levels
    log_level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    django_log_level = os.environ.get('DJANGO_LOG_LEVEL', 'WARNING').upper()
    
    # Whether we're in development
    is_development = os.environ.get('DJANGO_ENV', 'dev').lower() == 'dev'
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                'class': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d %(funcName)s %(request_id)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '{asctime} {levelname:8s} {name:20s} {request_id} [{pathname}:{lineno}] {message}',
                'style': '{',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '{levelname:8s} {name:20s} {message}',
                'style': '{',
            },
            'console_dev': {
                'format': '\033[36m{asctime}\033[0m |\033[35m{levelname:8s}\033[0m| \033[32m{name:20s}\033[0m | {message}',
                'style': '{',
                'datefmt': '%H:%M:%S'
            }
        },
        'filters': {
            'require_debug_false': {
                '()': 'django.utils.log.RequireDebugFalse',
            },
            'require_debug_true': {
                '()': 'django.utils.log.RequireDebugTrue',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'stream': sys.stdout,
                'formatter': 'console_dev' if is_development else 'simple',
            },
            'file_general': {
                'level': log_level,
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'cbaas.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'formatter': 'json',
                'encoding': 'utf-8',
            },
            'file_requests': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'requests.log',
                'maxBytes': 100 * 1024 * 1024,  # 100MB
                'backupCount': 20,
                'formatter': 'json',
                'encoding': 'utf-8',
            },
            'file_errors': {
                'level': 'ERROR',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'errors.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 15,
                'formatter': 'json',
                'encoding': 'utf-8',
            },
            'file_security': {
                'level': 'WARNING',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'security.log',
                'maxBytes': 20 * 1024 * 1024,  # 20MB
                'backupCount': 30,
                'formatter': 'json',
                'encoding': 'utf-8',
            },
            'file_performance': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'performance.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'formatter': 'json',
                'encoding': 'utf-8',
            },
            'file_celery': {
                'level': 'INFO',
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': log_dir / 'celery.log',
                'maxBytes': 50 * 1024 * 1024,  # 50MB
                'backupCount': 10,
                'formatter': 'json',
                'encoding': 'utf-8',
            }
        },
        'root': {
            'level': log_level,
            'handlers': ['console', 'file_general'] if is_development else ['file_general'],
        },
        'loggers': {
            # Main application loggers
            'cbaas': {
                'level': log_level,
                'handlers': ['console', 'file_general'] if is_development else ['file_general'],
                'propagate': False,
            },
            'cbaas.requests': {
                'level': 'INFO',
                'handlers': ['file_requests'],
                'propagate': False,
            },
            'cbaas.errors': {
                'level': 'ERROR',
                'handlers': ['console', 'file_errors'] if is_development else ['file_errors'],
                'propagate': False,
            },
            'cbaas.security': {
                'level': 'WARNING',
                'handlers': ['console', 'file_security'] if is_development else ['file_security'],
                'propagate': False,
            },
            'cbaas.performance': {
                'level': 'INFO',
                'handlers': ['file_performance'],
                'propagate': False,
            },
            
            # Django framework loggers
            'django': {
                'level': django_log_level,
                'handlers': ['console'] if is_development else ['file_general'],
                'propagate': False,
            },
            'django.request': {
                'level': 'ERROR',
                'handlers': ['console', 'file_errors'] if is_development else ['file_errors'],
                'propagate': False,
            },
            'django.security': {
                'level': 'WARNING',
                'handlers': ['console', 'file_security'] if is_development else ['file_security'],
                'propagate': False,
            },
            'django.db.backends': {
                'level': 'WARNING',
                'handlers': ['console'] if is_development and log_level == 'DEBUG' else ['file_general'],
                'propagate': False,
            },
            
            # Third-party loggers
            'celery': {
                'level': 'INFO',
                'handlers': ['console', 'file_celery'] if is_development else ['file_celery'],
                'propagate': False,
            },
            'celery.task': {
                'level': 'INFO',
                'handlers': ['file_celery'],
                'propagate': False,
            },
            'urllib3': {
                'level': 'WARNING',
                'handlers': ['file_general'],
                'propagate': False,
            },
            'requests': {
                'level': 'WARNING',
                'handlers': ['file_general'],
                'propagate': False,
            },
            
            # Application-specific loggers
            'apps.chat': {
                'level': log_level,
                'handlers': ['console', 'file_general'] if is_development else ['file_general'],
                'propagate': False,
            },
            'apps.documents': {
                'level': log_level,
                'handlers': ['console', 'file_general'] if is_development else ['file_general'],
                'propagate': False,
            },
            'apps.api_keys': {
                'level': log_level,
                'handlers': ['console', 'file_security'] if is_development else ['file_security'],
                'propagate': False,
            },
            'apps.auth': {
                'level': log_level,
                'handlers': ['console', 'file_security'] if is_development else ['file_security'],
                'propagate': False,
            },
        }
    }
    
    # Add email handler for critical errors in production
    if not is_development and os.environ.get('ADMIN_EMAIL'):
        config['handlers']['mail_admins'] = {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
            'formatter': 'detailed',
        }
        
        # Add email handler to critical loggers
        config['loggers']['cbaas.errors']['handlers'].append('mail_admins')
        config['loggers']['django.request']['handlers'].append('mail_admins')
        config['loggers']['django.security']['handlers'].append('mail_admins')
    
    return config


# Application-specific logging utilities
class CBaaSLogger:
    """
    Centralized logger for CBaaS with structured logging methods.
    """
    
    def __init__(self, name: str):
        self.logger = __import__('logging').getLogger(f'cbaas.{name}')
        self.request_logger = __import__('logging').getLogger('cbaas.requests')
        self.error_logger = __import__('logging').getLogger('cbaas.errors')
        self.security_logger = __import__('logging').getLogger('cbaas.security')
        self.performance_logger = __import__('logging').getLogger('cbaas.performance')
    
    def log_request(self, request_id: str, method: str, path: str, **kwargs):
        """Log HTTP request with structured data."""
        self.request_logger.info(
            f"{method} {path}",
            extra={
                'request_id': request_id,
                'event_type': 'http_request',
                **kwargs
            }
        )
    
    def log_response(self, request_id: str, method: str, path: str, status_code: int, 
                    duration_ms: float, **kwargs):
        """Log HTTP response with structured data."""
        level = self._get_log_level_for_status(status_code)
        self.request_logger.log(
            level,
            f"{method} {path} - {status_code} ({duration_ms}ms)",
            extra={
                'request_id': request_id,
                'event_type': 'http_response',
                'status_code': status_code,
                'duration_ms': duration_ms,
                **kwargs
            }
        )
    
    def log_error(self, message: str, request_id: str = None, **kwargs):
        """Log application error with context."""
        self.error_logger.error(
            message,
            extra={
                'request_id': request_id,
                'event_type': 'application_error',
                **kwargs
            }
        )
    
    def log_security_event(self, event_type: str, message: str, request_id: str = None, **kwargs):
        """Log security-related events."""
        self.security_logger.warning(
            message,
            extra={
                'request_id': request_id,
                'event_type': event_type,
                **kwargs
            }
        )
    
    def log_performance(self, operation: str, duration_ms: float, request_id: str = None, **kwargs):
        """Log performance metrics."""
        self.performance_logger.info(
            f"{operation} completed in {duration_ms}ms",
            extra={
                'request_id': request_id,
                'event_type': 'performance_metric',
                'operation': operation,
                'duration_ms': duration_ms,
                **kwargs
            }
        )
    
    def _get_log_level_for_status(self, status_code: int) -> int:
        """Get appropriate log level for HTTP status code."""
        import logging
        if 200 <= status_code < 300:
            return logging.INFO
        elif 300 <= status_code < 400:
            return logging.INFO
        elif 400 <= status_code < 500:
            return logging.WARNING
        else:
            return logging.ERROR


# Convenience function to get a logger
def get_logger(name: str) -> CBaaSLogger:
    """Get a CBaaS logger instance."""
    return CBaaSLogger(name)
