# AWS Secrets Manager - Required Secret Structure

## Secret Name
```
cbaas/backend/env
```

## Region
```
ap-south-1
```

## Secret Type
**Key-value pairs stored as JSON**

---

## Complete Secret Structure (JSON)

```json
{
  "DJANGO_SECRET_KEY": "your-django-secret-key-here",
  "DEBUG": "true",
  "ALLOWED_HOSTS": "*",
  "DATABASE_URL": "postgresql://user:password@host:5432/dbname",
  "CORS_ALLOWED_ORIGINS": "https://your-frontend-domain.com",
  "CORS_ALLOW_CREDENTIALS": "true",
  "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
  "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
  "AWS_STORAGE_BUCKET_NAME": "cbaas-static-files"
}
```

---

## How to Update Using AWS Console

### Method 1: AWS Console (Easiest)

1. **Navigate to Secrets Manager**:
   - Go to: https://console.aws.amazon.com/secretsmanager/
   - Region: `ap-south-1`

2. **Find the Secret**:
   - Search for: `cbaas/backend/env`
   - Click on the secret name

3. **Edit Secret**:
   - Click **"Retrieve secret value"**
   - Click **"Edit"**
   - Switch to **"Plaintext"** tab

4. **Add New Keys**:
   ```json
   {
     ... existing keys ...,
     "AWS_ACCESS_KEY_ID": "AKIA...",
     "AWS_SECRET_ACCESS_KEY": "your-secret-key",
     "AWS_STORAGE_BUCKET_NAME": "cbaas-static-files"
   }
   ```

5. **Save**:
   - Click **"Save"**

---

## How to Update Using AWS CLI

### Method 2: AWS CLI (Programmatic)

```bash
# 1. Get current secret
aws secretsmanager get-secret-value \
  --secret-id cbaas/backend/env \
  --region ap-south-1 \
  --query SecretString \
  --output text > current-secret.json

# 2. Edit current-secret.json to add:
#    - AWS_ACCESS_KEY_ID
#    - AWS_SECRET_ACCESS_KEY
#    - AWS_STORAGE_BUCKET_NAME

# 3. Update secret
aws secretsmanager update-secret \
  --secret-id cbaas/backend/env \
  --region ap-south-1 \
  --secret-string file://current-secret.json

# 4. Verify
aws secretsmanager get-secret-value \
  --secret-id cbaas/backend/env \
  --region ap-south-1 \
  --query SecretString \
  --output text | jq 'keys'
```

---

## How to Update Using Helper Scripts

### Method 3: PowerShell Script (Windows)

```powershell
.\infra\aws\update-secrets.ps1
```

The script will:
- ✅ Check AWS credentials
- ✅ Verify/create S3 bucket
- ✅ Prompt for IAM credentials
- ✅ Fetch current secret
- ✅ Add new keys
- ✅ Update Secrets Manager
- ✅ Show summary

### Method 4: Bash Script (Linux/Mac)

```bash
chmod +x infra/aws/update-secrets.sh
./infra/aws/update-secrets.sh
```

---

## Key Descriptions

### Existing Keys

| Key | Example Value | Description |
|-----|---------------|-------------|
| `DJANGO_SECRET_KEY` | `pHGgxiiy2Pc...` | Django's secret key for cryptographic signing |
| `DEBUG` | `true` | Enable detailed error logging (kept true for error tracking) |
| `ALLOWED_HOSTS` | `*` | Allowed hosts (ALB restricts access) |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `CORS_ALLOWED_ORIGINS` | `https://app.example.com` | Allowed CORS origins |
| `CORS_ALLOW_CREDENTIALS` | `true` | Allow credentials in CORS requests |

### New Keys (S3 Storage)

| Key | Example Value | Description |
|-----|---------------|-------------|
| `AWS_ACCESS_KEY_ID` | `AKIAIOSFODNN7EXAMPLE` | IAM user access key for S3 |
| `AWS_SECRET_ACCESS_KEY` | `wJalrXUt...` | IAM user secret key for S3 |
| `AWS_STORAGE_BUCKET_NAME` | `cbaas-static-files` | S3 bucket name for static/media files |

---

## Verification Checklist

After updating the secret, verify:

### ✅ Secret Updated
```bash
aws secretsmanager get-secret-value \
  --secret-id cbaas/backend/env \
  --region ap-south-1 \
  --query SecretString \
  --output text | jq -r 'keys[]'
```

**Expected output should include**:
```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_STORAGE_BUCKET_NAME
CORS_ALLOW_CREDENTIALS
CORS_ALLOWED_ORIGINS
DATABASE_URL
DEBUG
DJANGO_SECRET_KEY
```

### ✅ Task Definition References Secrets
```bash
cat infra/aws/task-definition.json | jq '.containerDefinitions[0].secrets[] | .name'
```

**Expected output**:
```
"DJANGO_SECRET_KEY"
"DEBUG"
"ALLOWED_HOSTS"
"DATABASE_URL"
"CORS_ALLOWED_ORIGINS"
"CORS_ALLOW_CREDENTIALS"
"AWS_ACCESS_KEY_ID"
"AWS_SECRET_ACCESS_KEY"
"AWS_STORAGE_BUCKET_NAME"
```

### ✅ ECS Task Has Access
The task execution role must have:
```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": [
    "arn:aws:secretsmanager:ap-south-1:577897067437:secret:cbaas/backend/env*"
  ]
}
```

**Verify**:
```bash
aws iam get-role-policy \
  --role-name cbaas-task-execution-role \
  --policy-name SecretsManagerPolicy
```

---

## Common Issues

### Issue: "ResourceNotFoundException"
**Cause**: Secret doesn't exist  
**Fix**: Create secret first:
```bash
aws secretsmanager create-secret \
  --name cbaas/backend/env \
  --secret-string '{"DJANGO_SECRET_KEY":"temp"}' \
  --region ap-south-1
```

### Issue: "AccessDeniedException" when updating
**Cause**: IAM user doesn't have permission  
**Fix**: Ensure your IAM user has `secretsmanager:UpdateSecret` permission

### Issue: ECS task can't read secret
**Cause**: Task execution role missing permissions  
**Fix**: Attach policy to `cbaas-task-execution-role`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:ap-south-1:577897067437:secret:cbaas/backend/env*"
    }
  ]
}
```

---

## Security Best Practices

✅ **Rotation**: Enable automatic rotation for sensitive keys  
✅ **Least Privilege**: Task execution role only has read access to this specific secret  
✅ **Encryption**: Secrets are encrypted at rest using AWS KMS  
✅ **Audit**: CloudTrail logs all secret access  
✅ **No Hardcoding**: Never commit secrets to git  

---

## Cost

- **Secrets Manager**: $0.40/month per secret
- **API Calls**: $0.05 per 10,000 API calls
- **Estimated**: ~$0.50/month for this secret

---

## Next Steps

1. ✅ Update secret with S3 credentials (use helper script or AWS Console)
2. ✅ Register updated task definition
3. ✅ Deploy to ECS
4. ✅ Verify at `/api/debug/static` endpoint
5. ✅ Test static file access from S3
