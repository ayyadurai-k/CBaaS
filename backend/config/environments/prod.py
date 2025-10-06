from .base import *  # noqa

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Debug and security - TEMPORARILY ENABLED FOR DEBUGGING
DEBUG = True  # TODO: Set to False after debugging

# ALLOWED_HOSTS configuration for ECS deployment
# Use wildcard since we're behind ALB (external access controlled by ALB security groups)
ALLOWED_HOSTS = ['*']  # Allow all hosts - safe behind ALB

# Static files configuration for ECS deployment
STATIC_URL = '/static/'
STATIC_ROOT = '/app/staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Force static file serving in production (safe behind ALB)
# This is required for ECS deployment where Django serves static files directly
FORCE_SERVE_STATIC = True

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = '/app/media'

# Database configuration from DATABASE_URL (Secrets Manager)
# DATABASE_URL format: postgresql://user:password@host:port/dbname
# Parse manually without external dependencies
DATABASE_URL = os.environ.get('DATABASE_URL', '')
if DATABASE_URL:
    from urllib.parse import urlparse
    db_info = urlparse(DATABASE_URL)
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': db_info.path[1:],  # Remove leading slash from /cbaasdb
            'USER': db_info.username,
            'PASSWORD': db_info.password,
            'HOST': db_info.hostname,
            'PORT': db_info.port or 5432,
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'sslmode': 'require',  # RDS requires SSL connection
            }
        }
    }
else:
    # Fallback for local development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'cbaasdb'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'localhost'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    }

# Security settings
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# CSRF settings - Set to False for HTTP-only ALB (until SSL is configured)
CSRF_COOKIE_SECURE = False  # Set to True when using HTTPS
SESSION_COOKIE_SECURE = False  # Set to True when using HTTPS

# CSRF trusted origins for ALB
CSRF_TRUSTED_ORIGINS = [
    'http://cbaas-alb-1444354359.ap-south-1.elb.amazonaws.com',
]

# Enable static file serving logging for debugging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.contrib.staticfiles': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
FORCE_SERVE_STATIC = True