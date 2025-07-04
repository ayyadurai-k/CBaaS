from .base import *

DEBUG = True # Often True for staging, but can be False

ALLOWED_HOSTS = ['your-staging-domain.com', 'www.your-staging-domain.com']

# Staging database settings (example for PostgreSQL)
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': 'staging_db',
#         'USER': 'staging_user',
#         'PASSWORD': 'staging_password',
#         'HOST': 'localhost',
#         'PORT': '',
#     }
# }

# Static files (CSS, JavaScript, Images)
# Example for local static files or a staging-specific CDN
# STATIC_ROOT = BASE_DIR / 'staticfiles_staging'
# STATIC_URL = '/static/'

# Security settings (can be less strict than production, but still good practice)
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True