from .base import *  # noqa

import os
from pathlib import Path
import json
import boto3
from botocore.exceptions import ClientError

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# =============================================================================
# Security Settings
# =============================================================================
DEBUG = False

# Get secret from AWS Secrets Manager or environment
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    try:
        secrets_client = boto3.client('secretsmanager', region_name=os.environ.get('AWS_REGION', 'ap-south-1'))
        secret_name = os.environ.get('SECRET_NAME', 'cbaas/prod/django-secret')
        response = secrets_client.get_secret_value(SecretId=secret_name)
        SECRET_KEY = response['SecretString']
    except (ClientError, KeyError):
        raise ValueError("SECRET_KEY not found in environment or Secrets Manager")

# Update with your actual domains
ALLOWED_HOSTS = [
    os.environ.get('BACKEND_DOMAIN', ''),
    os.environ.get('ALB_DNS', ''),
    '.elb.amazonaws.com',  # Allow ECS health checks
    'localhost',
]
ALLOWED_HOSTS = [h for h in ALLOWED_HOSTS if h]  # Remove empty strings

# HTTPS/SSL
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = False  # ALB handles SSL termination
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# =============================================================================
# CORS Settings
# =============================================================================
CORS_ALLOWED_ORIGINS = [
    f"https://{os.environ.get('FRONTEND_DOMAIN', 'app.example.com')}",
    f"https://{os.environ.get('CLOUDFRONT_DOMAIN', '')}",
]
CORS_ALLOWED_ORIGINS = [origin for origin in CORS_ALLOWED_ORIGINS if origin != 'https://']

CORS_ALLOW_CREDENTIALS = True

# =============================================================================
# Database Configuration
# =============================================================================
# Get database credentials from environment (injected from Secrets Manager)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cbaas_db'),
        'USER': os.environ.get('DB_USER', 'cbaas_admin'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000',  # 30 seconds
        },
    }
}

# =============================================================================
# Redis/Celery Configuration
# =============================================================================
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

# Use rediss:// for TLS
REDIS_URL = f"rediss://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0?ssl_cert_reqs=required"

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        },
        'KEY_PREFIX': 'cbaas',
    }
}

# Celery Configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# =============================================================================
# AWS S3 Storage Configuration
# =============================================================================
AWS_STORAGE_BUCKET_NAME_STATIC = os.environ.get('AWS_STORAGE_BUCKET_NAME_STATIC', 'cbaas-django-static-prod')
AWS_STORAGE_BUCKET_NAME_MEDIA = os.environ.get('AWS_STORAGE_BUCKET_NAME_MEDIA', 'cbaas-django-media-prod')
AWS_S3_REGION_NAME = os.environ.get('AWS_REGION', 'ap-south-1')

# Use IAM role for authentication (ECS task role)
AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None  # Use bucket ACLs
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400',
}

# Static files
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
AWS_LOCATION = 'static'
STATIC_URL = f'https://{AWS_STORAGE_BUCKET_NAME_STATIC}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/{AWS_LOCATION}/'

# Media files
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_STORAGE_BUCKET_NAME_MEDIA}.s3.{AWS_S3_REGION_NAME}.amazonaws.com/'

# Local fallback (for collectstatic during build)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# =============================================================================
# Logging Configuration
# =============================================================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s',
        },
        'verbose': {
            'format': '[%(levelname)s] %(asctime)s %(name)s: %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# =============================================================================
# Email Configuration (AWS SES)
# =============================================================================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = f'email-smtp.{AWS_S3_REGION_NAME}.amazonaws.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
# EMAIL_HOST_USER and EMAIL_HOST_PASSWORD should be in Secrets Manager
EMAIL_HOST_USER = os.environ.get('SES_SMTP_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('SES_SMTP_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')

# =============================================================================
# Performance & Security
# =============================================================================
# Connection pooling
CONN_MAX_AGE = 600

# Trusted origins for CSRF
CSRF_TRUSTED_ORIGINS = [
    f"https://{os.environ.get('BACKEND_DOMAIN', '')}",
    f"https://{os.environ.get('FRONTEND_DOMAIN', '')}",
]
CSRF_TRUSTED_ORIGINS = [origin for origin in CSRF_TRUSTED_ORIGINS if origin != 'https://']

# Admin URL (change this in production for security)
ADMIN_URL = os.environ.get('ADMIN_URL', 'admin/')
