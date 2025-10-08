# Static Files Configuration - Clean Implementation

## Overview
Simple, environment-based static file serving:
- **Local/Dev**: Standard Django filesystem storage
- **Production**: AWS S3 with separate static/media directories

## Changes Made

### 1. Backend Configuration Files

#### `backend/config/environments/base.py`
- Added `STATIC_ROOT = BASE_DIR / "staticfiles"` for local development
- Added `"storages"` to `INSTALLED_APPS`
- Clean configuration for local development

#### `backend/config/environments/prod.py`
- Configured AWS S3 settings (bucket, region, credentials)
- Set custom storage backends for static and media files
- URLs point directly to S3

#### `backend/config/urls.py`
- Removed custom static file serving logic
- Uses standard Django `static()` helper (only in DEBUG mode)
- Clean, no monkey patching

#### `backend/common/storage_backends.py` (NEW)
- `StaticStorage`: For collectstatic files (public-read, overwrite enabled)
- `MediaStorage`: For user uploads (private, unique filenames)

### 2. How It Works

#### Development (DEBUG=True)
```python
# base.py / dev.py
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# urls.py serves these via Django's development server
```

#### Production (DEBUG=False)
```python
# prod.py
AWS_STORAGE_BUCKET_NAME = "your-bucket-name"
STATICFILES_STORAGE = "common.storage_backends.StaticStorage"
DEFAULT_FILE_STORAGE = "common.storage_backends.MediaStorage"
STATIC_URL = "https://your-bucket.s3.amazonaws.com/static/"
MEDIA_URL = "https://your-bucket.s3.amazonaws.com/media/"

# No URL patterns needed - S3 serves directly
```

### 3. Required Environment Variables (Production)

Add to your ECS task definition or `.env.prod`:
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=ap-south-1
```

### 4. Deployment Steps

1. **Create S3 Bucket**:
   - Name: `cbaas-static-files` (or your choice)
   - Region: `ap-south-1`
   - Block public access: OFF for static files, ON for media
   - CORS configuration (if frontend hosted separately)

2. **Set Bucket Policy** (for static files):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::cbaas-static-files/static/*"
    }
  ]
}
```

3. **Create IAM User** with policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cbaas-static-files",
        "arn:aws:s3:::cbaas-static-files/*"
      ]
    }
  ]
}
```

4. **Update ECS Task Definition**:
   - Add environment variables for AWS credentials
   - `collectstatic` runs during Docker build (already configured in Dockerfile.backend)

5. **First Deploy**:
```bash
# Locally or in CI/CD
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput

# Or let the Dockerfile handle it during build
```

## Benefits

✅ **Clean separation**: Dev uses local files, prod uses S3  
✅ **No hacks**: Standard Django patterns, no custom URL serving  
✅ **Secure**: Media files can be private, static files cached  
✅ **Scalable**: S3 handles all file serving, no Django overhead  
✅ **Simple**: Environment variables control everything  

## Testing

### Local Development
```bash
# Start containers
docker compose -f docker-compose.dev.yml up -d

# Collect static files
docker compose -f docker-compose.dev.yml exec web python manage.py collectstatic --noinput

# Check if files are served
curl http://localhost:8000/static/admin/css/base.css
```

### Production (S3)
```bash
# Set environment variables
export AWS_STORAGE_BUCKET_NAME=your-bucket
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret
export DJANGO_ENV=prod

# Collect to S3 (happens during Docker build)
python manage.py collectstatic --noinput

# Verify
curl https://your-bucket.s3.amazonaws.com/static/admin/css/base.css
```

## No More Monkey Business! 🚫🐒

Previous implementation had custom `re_path` patterns bypassing Django's DEBUG check.  
New implementation: **Standard Django + django-storages**. That's it.
