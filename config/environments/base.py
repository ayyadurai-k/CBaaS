import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "dev-secret-change")
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
    "corsheaders", # Added for CORS

    # Domain apps
    "apps.users",
    "apps.ops", # Added for health/readiness endpoints
    "apps.organizations",
    "apps.documents",
    "apps.chatbot",
    "apps.chatbot_provider",
    "apps.api_keys",
    "apps.chat",
    "apps.search",

    # Auth sub-apps
    "apps.auth.signup",
    "apps.auth.login",
    "apps.auth.logout",
    "apps.auth.reset",
]

AUTH_USER_MODEL = "users.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware", # Must be above CommonMiddleware
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.debug",
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

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

# Static/Media
STATIC_URL = "/static/"
DEFAULT_FILE_STORAGE = os.environ.get(
    "DEFAULT_FILE_STORAGE",
    "django.core.files.storage.FileSystemStorage",
)
MEDIA_ROOT = BASE_DIR / "media"
MEDIA_URL = "/media/"

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
}

# JWT
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
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

# Secrets-at-rest
ENCRYPTION_SECRET_KEY = os.environ.get("ENCRYPTION_SECRET_KEY", "")

# Email
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@example.com")

# ---- LLM / Chat ----
LLM_CHAT_TIMEOUT_S = int(os.environ.get("LLM_CHAT_TIMEOUT_S", 30))

# ---- RAG / retrieval ----
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "openai")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small")
# MUST match your embedding model; 1536 is correct for OpenAI text-embedding-3-small
EMBEDDING_DIM = int(os.environ.get("EMBEDDING_DIM", 1536))

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
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",") if os.environ.get("CORS_ALLOWED_ORIGINS") else []
CORS_ALLOW_HEADERS = list(set([
    "accept", "accept-encoding", "authorization", "content-type", "origin",
    "x-api-key", "idempotency-key",
]))
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS", "DELETE", "PUT", "PATCH"]
CORS_EXPOSE_HEADERS = ["Content-Type"]
CORS_ALLOW_CREDENTIALS = False
