# AWS Secrets Manager Setup for CBaaS Backend

## Overview
This guide shows how to add the required S3 storage credentials to AWS Secrets Manager for the ECS task definition.

---

## Current Secrets Structure

The task definition references secrets from:
```
arn:aws:secretsmanager:ap-south-1:577897067437:secret:cbaas/backend/env
```

This is a **single secret** with **multiple key-value pairs** (JSON format).

---

## Required Secret Keys

### Existing Keys (already configured)
- ✅ `DJANGO_SECRET_KEY`
- ✅ `DEBUG`
- ✅ `ALLOWED_HOSTS`
- ✅ `DATABASE_URL`
- ✅ `CORS_ALLOWED_ORIGINS`
- ✅ `CORS_ALLOW_CREDENTIALS`

### New Keys (to add for S3 storage)
- 🆕 `AWS_ACCESS_KEY_ID` - IAM user access key for S3
- 🆕 `AWS_SECRET_ACCESS_KEY` - IAM user secret key for S3
- 🆕 `AWS_STORAGE_BUCKET_NAME` - S3 bucket name for static/media files

---

## Step 1: Create S3 Bucket

```bash
aws s3api create-bucket \
  --bucket cbaas-static-files \
  --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1
```

**Bucket Name**: `cbaas-static-files` (or your preferred name)

---

## Step 2: Set Bucket Policy

Create a file `s3-bucket-policy.json`:

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

Apply the policy:
```bash
aws s3api put-bucket-policy \
  --bucket cbaas-static-files \
  --policy file://s3-bucket-policy.json
```

**Note**: Only `/static/*` is public. `/media/*` stays private.

---

## Step 3: Create IAM User for S3 Access

```bash
# Create IAM user
aws iam create-user --user-name cbaas-s3-user

# Create access key
aws iam create-access-key --user-name cbaas-s3-user
```

**Save the output**:
```json
{
  "AccessKey": {
    "UserName": "cbaas-s3-user",
    "AccessKeyId": "AKIA...",  // ← Save this
    "SecretAccessKey": "..."    // ← Save this
  }
}
```

---

## Step 4: Attach IAM Policy to User

Create `s3-user-policy.json`:

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

Create and attach the policy:
```bash
# Create policy
aws iam create-policy \
  --policy-name cbaas-s3-access-policy \
  --policy-document file://s3-user-policy.json

# Attach to user
aws iam attach-user-policy \
  --user-name cbaas-s3-user \
  --policy-arn arn:aws:iam::577897067437:policy/cbaas-s3-access-policy
```

---

## Step 5: Update Secrets Manager

### Option A: Using AWS Console

1. Go to **AWS Secrets Manager** → `cbaas/backend/env`
2. Click **"Retrieve secret value"**
3. Click **"Edit"**
4. Add the new key-value pairs:
   ```json
   {
     "DJANGO_SECRET_KEY": "existing-value",
     "DEBUG": "true",
     "ALLOWED_HOSTS": "*",
     "DATABASE_URL": "existing-value",
     "CORS_ALLOWED_ORIGINS": "existing-value",
     "CORS_ALLOW_CREDENTIALS": "true",
     "AWS_ACCESS_KEY_ID": "AKIA...",
     "AWS_SECRET_ACCESS_KEY": "your-secret-key",
     "AWS_STORAGE_BUCKET_NAME": "cbaas-static-files"
   }
   ```
5. Click **"Save"**

### Option B: Using AWS CLI

```bash
# Get current secret
aws secretsmanager get-secret-value \
  --secret-id cbaas/backend/env \
  --region ap-south-1 \
  --query SecretString \
  --output text > current-secret.json

# Edit current-secret.json to add new keys
# Then update:

aws secretsmanager update-secret \
  --secret-id cbaas/backend/env \
  --region ap-south-1 \
  --secret-string file://current-secret.json
```

---

## Step 6: Enable CORS on S3 Bucket (if frontend is separate domain)

Create `s3-cors-policy.json`:

```json
{
  "CORSRules": [
    {
      "AllowedOrigins": ["https://your-frontend-domain.com"],
      "AllowedMethods": ["GET", "HEAD"],
      "AllowedHeaders": ["*"],
      "MaxAgeSeconds": 3600
    }
  ]
}
```

Apply:
```bash
aws s3api put-bucket-cors \
  --bucket cbaas-static-files \
  --cors-configuration file://s3-cors-policy.json
```

---

## Step 7: Update ECS Task Definition

The task definition has been updated with:

### New Secrets (from AWS Secrets Manager):
```json
{
  "name": "AWS_ACCESS_KEY_ID",
  "valueFrom": "arn:aws:secretsmanager:ap-south-1:577897067437:secret:cbaas/backend/env:AWS_ACCESS_KEY_ID::"
},
{
  "name": "AWS_SECRET_ACCESS_KEY",
  "valueFrom": "arn:aws:secretsmanager:ap-south-1:577897067437:secret:cbaas/backend/env:AWS_SECRET_ACCESS_KEY::"
},
{
  "name": "AWS_STORAGE_BUCKET_NAME",
  "valueFrom": "arn:aws:secretsmanager:ap-south-1:577897067437:secret:cbaas/backend/env:AWS_STORAGE_BUCKET_NAME::"
}
```

### New Environment Variables (plain text):
```json
{
  "name": "AWS_S3_REGION_NAME",
  "value": "ap-south-1"
},
{
  "name": "SERVE_STATIC_FILES",
  "value": "false"
}
```

---

## Step 8: Register Updated Task Definition

```bash
# Register the new task definition
aws ecs register-task-definition \
  --cli-input-json file://infra/aws/task-definition.json \
  --region ap-south-1

# Update the service to use the new task definition
aws ecs update-service \
  --cluster cbaas-cluster \
  --service cbaas-backend-service \
  --task-definition cbaas-backend-task \
  --force-new-deployment \
  --region ap-south-1
```

---

## Step 9: Verify Deployment

### Check ECS Task Logs
```bash
aws logs tail /ecs/cbaas-backend --follow --region ap-south-1
```

Look for:
- ✅ No errors about missing AWS credentials
- ✅ `collectstatic` running successfully
- ✅ Files uploaded to S3

### Check Configuration Endpoint
```bash
curl https://your-api-domain.com/api/debug/static
```

Expected response:
```json
{
  "STATIC_URL": "https://cbaas-static-files.s3.amazonaws.com/static/",
  "STATIC_ROOT": "/app/staticfiles",
  "DEBUG": true,
  "SERVE_STATIC_FILES": false,
  "STATICFILES_STORAGE": "common.storage_backends.StaticStorage",
  "DEFAULT_FILE_STORAGE": "common.storage_backends.MediaStorage"
}
```

### Test Static File Access
```bash
# Should serve from S3
curl https://cbaas-static-files.s3.amazonaws.com/static/admin/css/base.css
```

---

## Summary of Changes

| Component | What Changed |
|-----------|--------------|
| **S3 Bucket** | Created `cbaas-static-files` |
| **IAM User** | Created `cbaas-s3-user` with S3 access |
| **Secrets Manager** | Added 3 new keys: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` |
| **Task Definition** | Added 3 secrets from ASM, 2 environment variables |
| **Django Settings** | Already configured in `prod.py` to use S3 when `SERVE_STATIC_FILES=false` |

---

## Security Checklist

✅ **S3 bucket**: Only `/static/*` is public, `/media/*` is private  
✅ **IAM user**: Minimal permissions (only S3 bucket access)  
✅ **Secrets Manager**: Credentials encrypted at rest  
✅ **ECS Task Role**: Has permission to read from Secrets Manager  
✅ **HTTPS**: S3 URLs use HTTPS by default  
✅ **Environment separation**: Dev uses local files, prod uses S3  

---

## Quick Commands Reference

```bash
# Create S3 bucket
aws s3 mb s3://cbaas-static-files --region ap-south-1

# Create IAM user and access key
aws iam create-user --user-name cbaas-s3-user
aws iam create-access-key --user-name cbaas-s3-user

# Update Secrets Manager (after editing current-secret.json)
aws secretsmanager update-secret \
  --secret-id cbaas/backend/env \
  --secret-string file://current-secret.json \
  --region ap-south-1

# Register new task definition
aws ecs register-task-definition \
  --cli-input-json file://infra/aws/task-definition.json \
  --region ap-south-1

# Force new deployment
aws ecs update-service \
  --cluster cbaas-cluster \
  --service cbaas-backend-service \
  --force-new-deployment \
  --region ap-south-1
```

---

## Troubleshooting

### Issue: "NoCredentialsError"
**Cause**: AWS credentials not properly loaded from Secrets Manager  
**Fix**: Verify secret keys exist and task role has `secretsmanager:GetSecretValue` permission

### Issue: "AccessDenied" on S3
**Cause**: IAM user doesn't have S3 permissions  
**Fix**: Check IAM policy is attached to `cbaas-s3-user`

### Issue: Static files not found (404)
**Cause**: `collectstatic` didn't run or failed  
**Fix**: Check ECS logs, ensure `Dockerfile.backend` runs `collectstatic` during build

### Issue: CORS errors
**Cause**: S3 bucket doesn't have CORS policy  
**Fix**: Apply CORS configuration to bucket (Step 6)

---

## Cost Estimate

- **S3 Storage**: ~$0.023/GB/month (first 50 TB)
- **S3 Requests**: ~$0.0004/1000 GET requests
- **Secrets Manager**: $0.40/month per secret
- **Data Transfer**: $0.00/GB (CloudFront → Internet), $0.09/GB (S3 → Internet)

**Estimated**: ~$1-5/month for typical usage

---

## Next Steps After Setup

1. ✅ Update CI/CD pipeline to deploy to S3 on release
2. ✅ Consider adding CloudFront CDN in front of S3 for better performance
3. ✅ Set up S3 lifecycle policies to clean up old media files
4. ✅ Enable S3 versioning for static files
5. ✅ Monitor S3 costs in AWS Cost Explorer
