from .base import *  # noqa

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------
# 🔧 Debug and Security
# ---------------------------------------------------------------------
DEBUG = False  # Disable in production

# Use wildcard since ALB restricts access anyway
ALLOWED_HOSTS = ["*"]

# ---------------------------------------------------------------------
# ⚙️ Static / Media Configuration
# ---------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = "/app/staticfiles"
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/app/media"

# ---------------------------------------------------------------------
# 🗄️ Database Configuration
# ---------------------------------------------------------------------
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    db_info = urlparse(DATABASE_URL)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_info.path[1:],
            "USER": db_info.username,
            "PASSWORD": db_info.password,
            "HOST": db_info.hostname,
            "PORT": db_info.port or 5432,
            "CONN_MAX_AGE": 600,
            "OPTIONS": {"sslmode": "require"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "cbaasdb"),
            "USER": os.environ.get("DB_USER", "postgres"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }

# ---------------------------------------------------------------------
# 🔒 Security Settings
# ---------------------------------------------------------------------
# AWS ALB forwards X-Forwarded-Proto
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Enforce HTTPS cookies
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True

# Force HTTPS for the site
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_REFERRER_POLICY = "strict-origin"

# ---------------------------------------------------------------------
# 🌍 CORS / CSRF Configuration
# ---------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "https://chatweave.space",  # frontend
    "https://cbaas.chatweave.space",  # frontend
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "authorization",
    "content-type",
    "accept",
    "origin",
    "x-api-key",
    "idempotency-key",
]
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
CORS_EXPOSE_HEADERS = ["Content-Type", "Authorization"]

# CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    "https://chatweave.space",
    "https://cbaas.chatweave.space",
    "https://api.chatweave.space",
]

# ---------------------------------------------------------------------
# 📦 ECS / Deployment Behavior
# ---------------------------------------------------------------------
FORCE_SERVE_STATIC = True  # Safe behind ALB
USE_X_FORWARDED_HOST = True

# ---------------------------------------------------------------------
# 🧠 Logging Configuration
# ---------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard"},
        "file": {
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "logs", "django.log"),
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {"handlers": ["console", "file"], "level": "INFO"},
        "django.request": {"handlers": ["file"], "level": "ERROR", "propagate": False},
        "apps": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False},
    },
}

# ---------------------------------------------------------------------
# ✅ Operational Defaults
# ---------------------------------------------------------------------
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
USE_TZ = True

# Keep static serve for ECS (no CDN needed inside ALB)
FORCE_SERVE_STATIC = True
