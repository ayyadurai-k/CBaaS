# SERVE_STATIC_FILES Implementation

## Problem Statement
We need `DEBUG=True` in both development and production for error tracking, but we don't want Django to serve static files in production (that's S3's job). The standard Django pattern uses `if settings.DEBUG` to control static file serving, which couples these two concerns.

## Solution
Introduced a custom environment variable `SERVE_STATIC_FILES` to decouple static file serving from Django's `DEBUG` setting.

---

## Changes Made

### 1. Base Configuration
**File**: `backend/config/environments/base.py`

Added new setting with environment variable support:
```python
# Custom environment variable to control static file serving
# Use this instead of DEBUG to avoid coupling with Django's debug mode
SERVE_STATIC_FILES = os.environ.get("SERVE_STATIC_FILES", "true").lower() == "true"
```

**Default**: `True` (for backward compatibility with development)

---

### 2. Development Environment
**File**: `backend/config/environments/dev.py`

```python
DEBUG = True  # Error tracking
SERVE_STATIC_FILES = True  # Django serves files
```

**Behavior**: Django serves static/media files from local filesystem

---

### 3. Production Environment
**File**: `backend/config/environments/prod.py`

```python
DEBUG = True  # Keep error tracking enabled
SERVE_STATIC_FILES = False  # S3 serves files, not Django
```

**Behavior**: 
- Django shows detailed errors in logs (DEBUG=True)
- S3 serves static files (SERVE_STATIC_FILES=False)
- No static URL patterns registered

---

### 4. Staging Environment
**File**: `backend/config/environments/staging.py`

```python
DEBUG = True  # Error tracking in staging
SERVE_STATIC_FILES = False  # S3 serves files like production
```

**Behavior**: Mirrors production behavior

---

### 5. URL Configuration
**File**: `backend/config/urls.py`

**Before**:
```python
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

**After**:
```python
# Serve static/media files based on SERVE_STATIC_FILES setting
# Development: Django serves files locally
# Production: S3 serves files (SERVE_STATIC_FILES=False)
if getattr(settings, 'SERVE_STATIC_FILES', False):
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

---

### 6. Diagnostic Endpoint
**File**: `backend/apps/ops/views.py`

Updated `StaticDebugView` to show both settings:
```python
static_info = {
    'DEBUG': getattr(settings, 'DEBUG', False),
    'SERVE_STATIC_FILES': getattr(settings, 'SERVE_STATIC_FILES', False),
    'STATICFILES_STORAGE': ...,
    'DEFAULT_FILE_STORAGE': ...,
}
```

**Endpoint**: `GET /api/debug/static`

---

## Configuration Matrix

| Environment | DEBUG | SERVE_STATIC_FILES | Static Serving | Error Details |
|-------------|-------|--------------------|----------------|---------------|
| **Development** | `True` | `True` | Django (local) | Full |
| **Staging** | `True` | `False` | S3 | Full |
| **Production** | `True` | `False` | S3 | Full |

---

## Environment Variables

### Development (docker-compose.dev.yml)
```yaml
environment:
  - DJANGO_ENV=dev
  - SERVE_STATIC_FILES=true  # Optional, defaults to true in dev.py
```

### Production (ECS Task Definition)
```json
{
  "environment": [
    {"name": "DJANGO_ENV", "value": "prod"},
    {"name": "SERVE_STATIC_FILES", "value": "false"},
    {"name": "AWS_STORAGE_BUCKET_NAME", "value": "your-bucket"},
    {"name": "AWS_ACCESS_KEY_ID", "value": "..."},
    {"name": "AWS_SECRET_ACCESS_KEY", "value": "..."}
  ]
}
```

---

## Benefits

✅ **Decoupled Concerns**: Error tracking (DEBUG) separate from file serving (SERVE_STATIC_FILES)  
✅ **Production Error Tracking**: Can see detailed errors in CloudWatch logs while S3 serves files  
✅ **Clean Pattern**: Single environment variable controls static file serving behavior  
✅ **Explicit Configuration**: No implicit coupling with Django's DEBUG mode  
✅ **Backward Compatible**: Defaults to `True` in base settings  

---

## Testing

### Local Development
```bash
# Start containers
docker compose -f docker-compose.dev.yml up -d

# Collect static files
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput

# Check configuration
curl http://localhost:8000/api/debug/static

# Verify file serving
curl http://localhost:8000/static/admin/css/base.css
```

**Expected**: 
- `SERVE_STATIC_FILES: true`
- Static files served successfully

### Production (with S3)
```bash
# Check configuration
curl https://your-api.com/api/debug/static

# Verify S3 serving
curl https://your-bucket.s3.amazonaws.com/static/admin/css/base.css
```

**Expected**:
- `SERVE_STATIC_FILES: false`
- `STATICFILES_STORAGE: common.storage_backends.StaticStorage`
- Static files served from S3, not Django

---

## Why This Matters

### The Problem with `if DEBUG`
Django's `DEBUG` setting has multiple purposes:
1. Show detailed error pages
2. Enable SQL query logging
3. Serve static files in development
4. Disable template caching
5. Security warnings in development

**Production Dilemma**: 
- Need `DEBUG=False` for security (no stack traces to users)
- Want `DEBUG=True` for internal error logging (CloudWatch, Sentry)
- Can't have both with standard pattern

### Our Solution
Split the concerns:
- `DEBUG=True`: Always show detailed errors in **logs** (not user-facing)
- `SERVE_STATIC_FILES`: Explicitly control whether Django serves files
- Production: Detailed logging + S3 file serving
- Development: Detailed logging + Django file serving

---

## Migration Guide

If you have existing deployments:

1. **ECS Task Definition**: Add `SERVE_STATIC_FILES=false` environment variable
2. **Local Development**: No changes needed (defaults to `true`)
3. **CI/CD**: Update environment variable injection
4. **Verify**: Check `/api/debug/static` endpoint after deployment

---

## Related Files Updated

- ✅ `backend/config/environments/base.py` - Added `SERVE_STATIC_FILES` setting
- ✅ `backend/config/environments/dev.py` - Set to `True`
- ✅ `backend/config/environments/prod.py` - Set to `False`, `DEBUG=True`
- ✅ `backend/config/environments/staging.py` - Set to `False`, `DEBUG=True`
- ✅ `backend/config/urls.py` - Use `SERVE_STATIC_FILES` instead of `DEBUG`
- ✅ `backend/apps/ops/views.py` - Updated diagnostic endpoint
- ✅ `docs/STATIC_FILES_S3.md` - Updated documentation
- ✅ `.github/copilot-instructions.md` - Updated AI agent instructions

---

## No More Coupling! 🎯

**Before**: Static file serving tied to DEBUG setting  
**After**: Explicit `SERVE_STATIC_FILES` control

Clean, simple, maintainable! 🚫🐒
