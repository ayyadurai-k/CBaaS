from .base import *  # noqa

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Debug and security
DEBUG = False
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',') if os.environ.get('ALLOWED_HOSTS') else []

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

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cbaasdb'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
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

# Add ALB DNS to ALLOWED_HOSTS if not already present
if 'cbaas-alb-1444354359.ap-south-1.elb.amazonaws.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('cbaas-alb-1444354359.ap-south-1.elb.amazonaws.com')

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

# Add localhost and internal IPs to ALLOWED_HOSTS
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '172.31.0.0/16',
    '10.0.0.0/8',
    'cbaas-alb-1444354359.ap-south-1.elb.amazonaws.com'
]