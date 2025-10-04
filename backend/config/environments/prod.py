from .base import *  # noqa

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Static files configuration for production
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

# Ensure static files are served correctly
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# Media files configuration
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

DEBUG = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Add static file serving in production (for ALB)
FORCE_SERVE_STATIC = True