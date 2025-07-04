from .base import *

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]

# Optional: Dev-specific tools
INSTALLED_APPS += [
    # 'debug_toolbar',
]

# Optional: Debug toolbar middleware
# MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Logging for dev
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}
