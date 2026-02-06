import os
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / ".env.dev")

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "pHGgxiiy2Pc,=XL[#.U#vjq=eq7y7<3Y!9zU'U+U$V0I"
)
DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "pgvector",
    "corsheaders",  # Added for CORS
    "storages",  # AWS S3 storage backend
    "django_socio_grpc",  # gRPC framework for microservices
    # Domain apps
    "apps.users",
    "apps.ops",  # Added for health/readiness endpoints
    "apps.organizations",
    "apps.documents",
    "apps.chatbot",
    "apps.llm_providers",  # LLM provider management
    "apps.api_keys",
    "apps.chat",
    "apps.search",
    # Auth sub-apps
    "apps.auth.signup",
    "apps.auth.login",
    "apps.auth.logout",
    "apps.auth.reset",
    "apps.auth.status",

]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Must be above CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "common.middleware.logging_middleware.RequestLoggingMiddleware",  # Add request logging
    "common.middleware.api_key_usage_middleware.APIKeyUsageMiddleware",  # Track API key usage
    "common.middleware.api_key_usage_middleware.APIKeyQuotaMiddleware",  # Enforce API key quotas
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "cbaas"),
        "USER": os.environ.get("POSTGRES_USER", "postgres"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "password"),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
    }
}

# Static/Media (Development defaults)
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Custom environment variable to control static file serving
# Use this instead of DEBUG to avoid coupling with Django's debug mode
SERVE_STATIC_FILES = os.environ.get("SERVE_STATIC_FILES", "true").lower() == "true"

# DRF
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "common.security.api_key_auth.APIKeyAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "common.core.filters.OrganizationFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "common.core.pagination.DefaultPagination",
    "PAGE_SIZE": 25,
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "user": "1000/hour",
        "anon": "50/hour",
        "login": "10/minute",
        "password_reset": "5/minute",
        "chat": os.environ.get("RATE_CHAT", "60/min"),
        "search": os.environ.get("RATE_SEARCH", "120/min"),
        "documents": os.environ.get("RATE_DOCS", "10/min"),
    },
    # Global exception handler - catches ALL exceptions and returns consistent JSON
    "EXCEPTION_HANDLER": "common.exceptions.handlers.custom_exception_handler",
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "SIGNING_KEY": os.environ.get("JWT_SIGNING_KEY", SECRET_KEY),
    "ALGORITHM": "HS256",
}

# OpenAPI
SPECTACULAR_SETTINGS = {"TITLE": "Org Chatbot API", "VERSION": "0.1.0"}

# Celery / Redis
CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.environ.get("CELERY_RESULT_BACKEND", "redis://redis:6379/0")

# Celery Configuration
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = os.environ.get("TIME_ZONE", "UTC")
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_RETRY = True

# Secrets-at-rest
ENCRYPTION_SECRET_KEY = os.environ.get("ENCRYPTION_SECRET_KEY", "")

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("SMTP_USER")
EMAIL_HOST_PASSWORD = os.getenv("SMTP_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ---- LLM / Chat ---- 
LLM_CHAT_TIMEOUT_S = int(os.environ.get("LLM_CHAT_TIMEOUT_S", 30))

# ---- RAG / retrieval ----
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "gemini")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-004")
# MUST match your embedding model; 768 is correct for Gemini text-embedding-004
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", 768))

TOP_K = int(os.environ.get("TOP_K", 6))
MAX_CONTEXT_CHARS = int(os.environ.get("MAX_CONTEXT_CHARS", 12000))

# ---- chunking ----
CHUNK_SIZE_CHARS = int(os.environ.get("CHUNK_SIZE_CHARS", 1500))
CHUNK_OVERLAP_CHARS = int(os.environ.get("CHUNK_OVERLAP_CHARS", 200))

# ---- Idempotency / SSE ----
IDEMPOTENCY_REDIS_URL = os.environ.get("IDEMPOTENCY_REDIS_URL", CELERY_BROKER_URL)
IDEMPOTENCY_TTL_S = int(os.environ.get("IDEMPOTENCY_TTL_S", 3600))

# Timezone (explicit; Django defaults to UTC with USE_TZ=True)
TIME_ZONE = os.environ.get("TIME_ZONE", "UTC")
USE_TZ = True

API_KEY_HMAC_SECRET = os.environ.get("API_KEY_HMAC_SECRET", ENCRYPTION_SECRET_KEY)

# Document extraction caps
MAX_UPLOAD_MB = int(os.environ.get("MAX_UPLOAD_MB", 25))
MAX_PDF_PAGES = int(os.environ.get("MAX_PDF_PAGES", 500))

# CORS settings
CORS_ALLOWED_ORIGINS = (
    os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:8080").split(",")
    if os.environ.get("CORS_ALLOWED_ORIGINS")
    else ["http://localhost:8080"]
)
CORS_ALLOW_HEADERS = list(
    set(
        [
            "accept",
            "accept-encoding",
            "authorization",
            "content-type",
            "origin",
            "x-api-key",
            "idempotency-key",
        ]
    )
)
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS", "DELETE", "PUT", "PATCH"]
CORS_EXPOSE_HEADERS = ["Content-Type"]
CORS_ALLOW_CREDENTIALS = True

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8080")


# ---- Logging Configuration ----
# from common.utils.logging_config import get_logging_config
# LOGGING = get_logging_config()

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,  # don't override Django's default loggers
    "formatters": {
        "standard": {
            "format": "[{asctime}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {  # capture 5xx errors
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
        "apps": {  # replace with your app name
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Logging settings for request/response middleware
LOG_REQUEST_BODY = os.environ.get("LOG_REQUEST_BODY", "true").lower() == "true"
LOG_RESPONSE_BODY = os.environ.get("LOG_RESPONSE_BODY", "true").lower() == "true"
LOG_MAX_BODY_LENGTH = int(os.environ.get("LOG_MAX_BODY_LENGTH", "10000"))
LOG_EXCLUDED_PATHS = [
    "/health/",
    "/readiness/", 
    "/static/",
    "/media/",
    "/favicon.ico",
    "/admin/jsi18n/",
]
LOG_EXCLUDED_CONTENT_TYPES = [
    "image/",
    "video/",
    "audio/",
    "application/octet-stream",
    "application/pdf",
]

# ---- gRPC Framework Configuration ----
# Django Socio gRPC settings for microservices communication
GRPC_FRAMEWORK = {
    # Root handlers hook - registers all gRPC services
    "ROOT_HANDLERS_HOOK": "config.grpc_handlers.grpc_handlers",
    # gRPC server port (default: 50051)
    "GRPC_CHANNEL_PORT": int(os.environ.get("GRPC_PORT", 50051)),
    # Enable async gRPC for better performance
    "GRPC_ASYNC": True,
    # Root folder for generated proto files
    "ROOT_GRPC_FOLDER": "grpc_generated",
    # Authentication classes for gRPC requests
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "common.grpc.authentication.JWTGRPCAuthentication",
    ],
    # Filter backends for gRPC services
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    # Pagination class for list operations
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    # gRPC middleware for request processing
    "GRPC_MIDDLEWARE": [
        "django_socio_grpc.middlewares.log_requests_middleware",
        "django_socio_grpc.middlewares.close_old_connections_middleware",
    ],
    # Log OK responses (useful for debugging)
    "LOG_OK_RESPONSE": DEBUG,
    # Separate read/write models for serializers
    "SEPARATE_READ_WRITE_MODEL": True,
    # Enable health check endpoint
    "ENABLE_HEALTH_CHECK": True,
}
