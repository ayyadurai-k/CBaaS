from .base import *  # noqa

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Static files configuration for production
STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"

# Use default Django static file storage
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = "/app/media"

# Security settings
DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Force Django to serve static files in production (for containers without nginx)
SERVE_STATIC_FILES = True
FORCE_SERVE_STATIC = True

# Add localhost and internal IPs to ALLOWED_HOSTS
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '172.31.0.0/16',
    '10.0.0.0/8',
    'cbaas-alb-1444354359.ap-south-1.elb.amazonaws.com'
]