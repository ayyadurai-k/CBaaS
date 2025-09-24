"""
Centralized logging configuration for CBaaS backend.
Provides structured JSON logging with different handlers for various log types.
"""
import os
import sys
from pathlib import Path
import logging


def get_logging_config():
    # Log directory
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)

    cbaas_log = str(log_dir / "cbaas.log")
    requests_log = str(log_dir / "requests.log")
    errors_log = str(log_dir / "errors.log")
    security_log = str(log_dir / "security.log")
    performance_log = str(log_dir / "performance.log")

    is_dev = os.environ.get("DJANGO_ENV", "dev").lower() == "dev"

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "console": {
                "format": "{asctime} | {levelname:8s} | {name:20s} | {message}",
                "style": "{",
                "datefmt": "%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "level": "DEBUG" if is_dev else "INFO",
                "formatter": "console",
            },
            "file_general": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": cbaas_log,
                "maxBytes": 50 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf-8",
                "level": "INFO",
            },
            "file_requests": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": requests_log,
                "maxBytes": 50 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf-8",
                "level": "INFO",
            },
            "file_errors": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": errors_log,
                "maxBytes": 20 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf-8",
                "level": "ERROR",
            },
            "file_security": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": security_log,
                "maxBytes": 20 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf-8",
                "level": "WARNING",
            },
            "file_performance": {
                "class": "logging.handlers.RotatingFileHandler",
                "filename": performance_log,
                "maxBytes": 20 * 1024 * 1024,
                "backupCount": 5,
                "formatter": "json",
                "encoding": "utf-8",
                "level": "INFO",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["console", "file_general"],
        },
        "loggers": {
            # ✅ Our app logs
            "cbaas": {"level": "DEBUG", "handlers": ["console", "file_general"], "propagate": False},
            "cbaas.requests": {"level": "INFO", "handlers": ["file_requests"], "propagate": False},
            "cbaas.errors": {"level": "ERROR", "handlers": ["file_errors"], "propagate": False},
            "cbaas.security": {"level": "WARNING", "handlers": ["file_security"], "propagate": False},
            "cbaas.performance": {"level": "INFO", "handlers": ["file_performance"], "propagate": False},
            "apps": {"level": "DEBUG", "handlers": ["console", "file_general"], "propagate": False},

            # ✅ Important Django signals (only WARNING+)
            "django": {"level": "WARNING", "handlers": ["file_errors"], "propagate": False},
            "django.request": {"level": "ERROR", "handlers": ["file_errors"], "propagate": False},
            "django.security": {"level": "ERROR", "handlers": ["file_security"], "propagate": False},

            # 🚫 Suppress noise
            "django.utils.autoreload": {"level": "ERROR", "handlers": [], "propagate": False},
            "django.db.backends": {"level": "ERROR", "handlers": [], "propagate": False},
            "urllib3": {"level": "ERROR", "handlers": [], "propagate": False},
            "requests": {"level": "ERROR", "handlers": [], "propagate": False},
        },
    }

    return config


# Application-specific logging utilities
class CBaaSLogger:
    """Centralized logger for CBaaS with structured logging methods."""

    def __init__(self, name: str):
        self.logger = logging.getLogger(f'cbaas.{name}')
        self.request_logger = logging.getLogger('cbaas.requests')
        self.error_logger = logging.getLogger('cbaas.errors')
        self.security_logger = logging.getLogger('cbaas.security')
        self.performance_logger = logging.getLogger('cbaas.performance')

    def log_request(self, request_id: str, method: str, path: str, **kwargs):
        """Log HTTP request with structured data."""
        self.request_logger.info(
            f"{method} {path}",
            extra={'request_id': request_id, 'event_type': 'http_request', **kwargs}
        )

    def log_response(self, request_id: str, method: str, path: str,
                     status_code: int, duration_ms: float, **kwargs):
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
            extra={'request_id': request_id, 'event_type': 'application_error', **kwargs}
        )

    def log_security_event(self, event_type: str, message: str,
                           request_id: str = None, **kwargs):
        """Log security-related events."""
        self.security_logger.warning(
            message,
            extra={'request_id': request_id, 'event_type': event_type, **kwargs}
        )

    def log_performance(self, operation: str, duration_ms: float,
                        request_id: str = None, **kwargs):
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
        if 200 <= status_code < 300:
            return logging.INFO
        elif 300 <= status_code < 400:
            return logging.INFO
        elif 400 <= status_code < 500:
            return logging.WARNING
        return logging.ERROR


def get_logger(name: str) -> CBaaSLogger:
    """Get a CBaaS logger instance."""
    return CBaaSLogger(name)
