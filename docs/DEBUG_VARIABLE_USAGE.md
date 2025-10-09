# DEBUG Variable Usage Analysis

## Overview
The `DEBUG` setting in Django controls development vs production behavior. Here's every place where it's used in the CBaaS codebase.

---

## 1. Configuration Files (Setting DEBUG value)

### ✅ `backend/config/environments/base.py` (Line 14)
```python
DEBUG = False
```
**Why**: Default to `False` for security. Individual environment files override this.

### ✅ `backend/config/environments/dev.py` (Line 2)
```python
DEBUG = True
```
**Why**: Enable debug mode for local development - shows detailed error pages, allows Django to serve static files, and provides verbose logging.

### ✅ `backend/config/environments/staging.py` (Line 2)
```python
DEBUG = False
```
**Why**: Staging should mimic production behavior - hide error details, don't serve static files via Django.

### ✅ `backend/config/environments/prod.py` (Line 12)
```python
DEBUG = False  # Disable in production
```
**Why**: Production must never expose debug information - security risk. Hides stack traces, SQL queries, and internal paths.

---

## 2. URL Configuration (Using DEBUG conditionally)

### ✅ `backend/config/urls.py` (Line 39)
```python
# Serve static/media files in development only
# Production uses AWS S3 (configured in prod.py)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
**Why**: 
- **Development (DEBUG=True)**: Django serves static/media files directly (convenient for local dev)
- **Production (DEBUG=False)**: No static URL patterns added because AWS S3 serves files directly
- **Critical**: This is the standard Django pattern - don't serve files through Django in production

---

## 3. Debugging/Diagnostics Endpoints

### ✅ `backend/apps/ops/views.py` (Line 38)
```python
class StaticDebugView(APIView):
    def get(self, request):
        static_info = {
            'STATIC_URL': getattr(settings, 'STATIC_URL', 'Not set'),
            'STATIC_ROOT': getattr(settings, 'STATIC_ROOT', 'Not set'),
            'DEBUG': getattr(settings, 'DEBUG', False),  # ← Reading DEBUG value
            'FORCE_SERVE_STATIC': getattr(settings, 'FORCE_SERVE_STATIC', False),
            'STATICFILES_STORAGE': getattr(settings, 'STATICFILES_STORAGE', 'Not set'),
        }
```
**Why**: Diagnostic endpoint to check static file configuration. Returns the current DEBUG status so you can verify environment settings.

**Endpoint**: `GET /api/debug/static`

---

## 4. Template Context Processor (Django Built-in)

### ✅ `backend/config/environments/base.py` (Line 74)
```python
TEMPLATES = [
    {
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",  # ← Uses DEBUG
                ...
            ]
        },
    }
]
```
**Why**: Django's built-in context processor. When `DEBUG=True`, adds debug info to template context. Required for Django admin's debug toolbar and error pages.

---

## Summary Table

| Location | Usage Type | DEBUG Value | Purpose |
|----------|-----------|-------------|---------|
| `config/environments/base.py` | **Set** | `False` | Default fallback |
| `config/environments/dev.py` | **Set** | `True` | Enable dev features |
| `config/environments/staging.py` | **Set** | `False` | Production-like behavior |
| `config/environments/prod.py` | **Set** | `False` | Production security |
| `config/urls.py` | **Read** | Conditional | Serve static files only in dev |
| `apps/ops/views.py` | **Read** | Display | Diagnostic endpoint |
| Template context processor | **Read** | Django internal | Admin/error pages |

---

## Key Implications

### When DEBUG = True (Development)
✅ Detailed error pages with stack traces  
✅ Django serves static/media files via development server  
✅ SQL queries logged to console  
✅ Template errors show detailed context  
✅ ALLOWED_HOSTS not strictly enforced  
⚠️ **Never use in production** - exposes sensitive information

### When DEBUG = False (Production/Staging)
✅ Generic error pages (no internal details)  
✅ Static files served by external service (S3, CDN, nginx)  
✅ ALLOWED_HOSTS strictly enforced  
✅ No SQL query logging  
✅ Better performance (no debug overhead)  
✅ Secure - hides application internals

---

## Environment Variables Control

The `DEBUG` value is set based on `DJANGO_ENV`:

```python
# config/settings.py loads the right environment:
DJANGO_ENV = os.environ.get("DJANGO_ENV", "dev")

if DJANGO_ENV == "dev":
    from .environments.dev import *  # DEBUG = True
elif DJANGO_ENV == "prod":
    from .environments.prod import *  # DEBUG = False
elif DJANGO_ENV == "staging":
    from .environments.staging import *  # DEBUG = False
```

**Container/Deployment**:
```bash
# Development
docker-compose.dev.yml: DJANGO_ENV=dev

# Production
ECS Task Definition: DJANGO_ENV=prod
```

---

## Related Settings Affected by DEBUG

While not directly using `DEBUG`, these settings behave differently based on environment:

- **STATICFILES_STORAGE**: Development uses default, Production uses S3
- **DEFAULT_FILE_STORAGE**: Development uses filesystem, Production uses S3
- **LOGGING**: More verbose in development
- **CORS_ALLOWED_ORIGINS**: Stricter in production
- **SECURE_SSL_REDIRECT**: Enabled only in production

---

## Recommendations

✅ **Keep it simple**: Only use `DEBUG` for its intended purpose (Django internal behavior)  
✅ **Don't abuse**: Don't use `if DEBUG` for custom business logic  
✅ **Environment-based**: Use `DJANGO_ENV` to load different settings files instead  
✅ **Security**: Always ensure `DEBUG=False` in production deployments  
✅ **Monitoring**: Check `/api/debug/static` endpoint to verify DEBUG status after deployment  

---

## No Monkeys Here! 🚫🐒

The only places we check `DEBUG`:
1. Setting its value in environment configs
2. Conditionally serving static files in `urls.py` (standard Django pattern)
3. Reading it in diagnostic endpoint

**That's it. Clean and simple.**
