# API Key Security Guide

## 🔐 Comprehensive API Key Protection for CBaaS

This document outlines the complete API key security implementation for the CBaaS (Chatbot-as-a-Service) platform, following industry best practices.

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication vs Authorization](#authentication-vs-authorization)
3. [API Key Scopes](#api-key-scopes)
4. [Security Features](#security-features)
5. [Usage Guidelines](#usage-guidelines)
6. [Rate Limiting](#rate-limiting)
7. [Quota Management](#quota-management)
8. [IP Whitelisting](#ip-whitelisting)
9. [Key Rotation](#key-rotation)
10. [Monitoring & Analytics](#monitoring--analytics)
11. [Best Practices](#best-practices)
12. [Troubleshooting](#troubleshooting)

---

## Overview

CBaaS uses API keys for programmatic access to chat, search, and document management endpoints. Each API key provides secure, auditable access with granular permission control.

### Key Features

✅ **Encryption at Rest** - Keys encrypted using Fernet (AES-256)  
✅ **Constant-Time Lookup** - HMAC-based authentication prevents timing attacks  
✅ **Scope-Based Authorization** - Granular permissions (full-access, read-only, upload-only)  
✅ **Per-Key Rate Limiting** - Custom rate limits per API key  
✅ **Quota Enforcement** - Request limits with automatic blocking  
✅ **IP Whitelisting** - Restrict keys to specific IP addresses  
✅ **Expiration Dates** - Automatic key expiration  
✅ **Comprehensive Logging** - Detailed usage tracking for analytics and auditing  
✅ **Revocation** - Instant key deactivation with reason tracking  

---

## Authentication vs Authorization

### Authentication
**"Who are you?"** - Verifies the API key is valid and active.

Process:
1. Client sends `X-API-Key` header
2. System looks up key via HMAC (constant-time)
3. Validates: status, expiration, quota, IP whitelist
4. Sets `request.organization` and `request.auth_api_key`

### Authorization
**"What can you do?"** - Checks if the key has permission for the operation.

Process:
1. Permission class checks `api_key.scope`
2. Validates scope matches endpoint requirements
3. Allows or denies request based on scope rules

---

## API Key Scopes

### 1. Full Access (`full-access`)
**Permissions:**
- ✅ Chat completions (POST /api/chat/completions)
- ✅ Chat streaming (POST /api/chat/stream)
- ✅ Search (GET /api/search/)
- ✅ Document upload (POST /api/documents/)
- ✅ Document management (GET, PUT, DELETE /api/documents/)

**Use Cases:**
- Production integrations
- Backend services
- Full-featured applications

### 2. Read-Only (`read-only`)
**Permissions:**
- ✅ Search (GET /api/search/)
- ✅ List documents (GET /api/documents/)
- ❌ Chat (blocked)
- ❌ Upload (blocked)
- ❌ Modify/Delete (blocked)

**Use Cases:**
- Analytics tools
- Monitoring dashboards
- Public search interfaces

### 3. Upload-Only (`upload-only`)
**Permissions:**
- ✅ Document upload (POST /api/documents/)
- ✅ Document management (GET, PUT, DELETE /api/documents/)
- ❌ Chat (blocked)
- ❌ Search (blocked)

**Use Cases:**
- Document ingestion pipelines
- Batch upload services
- Content management systems

---

## Security Features

### 1. Encryption at Rest

**Algorithm:** Fernet (symmetric encryption with AES-128-CBC + HMAC)

```python
# Keys are never stored in plaintext
api_key.key = "generated_plaintext_key"  # Setter encrypts automatically
encrypted_value = api_key.key_encrypted  # Stored in DB
plaintext = api_key.key  # Getter decrypts on-the-fly
```

**Security Properties:**
- Keys cannot be recovered from database dumps
- Requires `ENCRYPTION_SECRET_KEY` environment variable
- Automatic rotation support via key re-encryption

### 2. HMAC Lookup

**Algorithm:** HMAC-SHA256

```python
# Fast, constant-time lookup without decryption
hmac_hash = hmac.new(secret, key_plaintext, sha256).hexdigest()
api_key = APIKey.objects.get(key_hmac=hmac_hash)  # DB indexed
```

**Benefits:**
- O(1) lookup performance
- Prevents timing attacks
- No decryption needed for authentication

### 3. Status Validation

```python
class Status:
    ACTIVE = "active"      # Key is usable
    REVOKED = "revoked"    # Permanently disabled
    EXPIRED = "expired"    # Automatically disabled after expires_at
```

**Validation:**
- Checked on every request
- Auto-updates from ACTIVE → EXPIRED when expires_at is reached
- Revocation includes reason tracking

### 4. Quota Enforcement

```python
# Atomic increment (thread-safe)
APIKey.objects.filter(pk=key.pk).update(
    usage_count=F("usage_count") + 1,
    last_used_at=timezone.now()
)

# Validation
if api_key.quota and api_key.usage_count >= api_key.quota:
    raise AuthenticationFailed("Quota exceeded")
```

**Features:**
- Atomic counters prevent race conditions
- Soft limit (returns 401 when exceeded)
- Tracks last_used_at for dormancy detection

### 5. IP Whitelisting

```python
allowed_ips = ["203.0.113.5", "198.51.100.42"]
api_key.allowed_ips = allowed_ips

# Validation
client_ip = request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0]
if not api_key.is_ip_allowed(client_ip):
    raise AuthenticationFailed("Unauthorized IP")
```

**Use Cases:**
- Lock keys to office IPs
- Restrict to VPN ranges
- Prevent stolen key abuse

### 6. Expiration Dates

```python
from datetime import timedelta
from django.utils import timezone

# Set expiration 90 days from now
api_key.expires_at = timezone.now() + timedelta(days=90)

# Auto-validation
if api_key.is_expired():
    api_key.status = APIKey.Status.EXPIRED
    api_key.save()
```

**Benefits:**
- Automatic cleanup of old keys
- Compliance with security policies
- Forces regular key rotation

---

## Usage Guidelines

### Creating an API Key

**Via Django Admin:**
1. Navigate to Admin → API Keys → Add
2. Select organization
3. Enter unique name
4. Choose scope (full-access, read-only, upload-only)
5. Optional: Set quota, expiration, allowed IPs
6. Save (key is generated automatically)
7. **IMPORTANT:** Copy the key immediately (shown only once)

**Via API (future):**
```bash
curl -X POST https://api.cbaas.com/api/keys/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Integration",
    "scope": "full-access",
    "quota": 100000,
    "rate_limit_per_minute": 120,
    "allowed_ips": ["203.0.113.0/24"],
    "expires_at": "2025-12-31T23:59:59Z"
  }'
```

### Using an API Key

**Authentication:**
```bash
# Method 1: X-API-Key header (recommended)
curl -X POST https://api.cbaas.com/api/chat/completions \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -H "Idempotency-Key: unique-request-id-123" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 512
  }'
```

**Response (Success):**
```json
{
  "id": "msg_abc123",
  "session_id": null,
  "model": "gpt-4",
  "answer": "Hello! How can I help you?",
  "citations": [],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 8,
    "total_tokens": 18
  },
  "latency_ms": 450
}
```

**Response (Quota Exceeded):**
```json
{
  "error": "API key quota exceeded. Used 10000 of 10000 requests."
}
```

### Revoking an API Key

**Via Django Admin:**
1. Navigate to API Key detail
2. Click "Revoke"
3. Enter reason (optional but recommended)
4. Confirm

**Via API (future):**
```bash
curl -X PATCH https://api.cbaas.com/api/keys/{id}/revoke/ \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -d '{"reason": "Security incident - compromised key"}'
```

**Effect:**
- Key status changes to REVOKED
- All subsequent requests with this key return 401
- Existing in-flight requests may complete
- Cannot be un-revoked (create new key instead)

---

## Rate Limiting

### Per-Key Rate Limits

**Default Limits (configurable in settings):**
- API Keys: `60/min` (global default)
- Chat: `60/min` (scoped)
- Search: `120/min` (scoped)
- Documents: `10/min` (scoped)

**Custom Per-Key Limits:**
```python
api_key.rate_limit_per_minute = 200  # Override default
api_key.save()
```

**Precedence:**
1. API key's custom `rate_limit_per_minute`
2. Scope-based limit from `REST_FRAMEWORK['DEFAULT_THROTTLE_RATES']`
3. Global default (60/min)

### Burstable Rate Limiting

Allows short bursts while maintaining overall limits:

```python
# Short-term: 10 requests per second
# Long-term: 100 requests per minute

throttle_classes = [BurstableAPIKeyThrottle]
```

**Use Cases:**
- Handle traffic spikes
- Support batch operations
- Smooth user experience

### Response Headers

Rate limit information returned in headers:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
Retry-After: 15  (if throttled)
```

---

## Quota Management

### Setting Quotas

```python
# Unlimited requests
api_key.quota = None

# 10,000 request limit
api_key.quota = 10000

# Check remaining
remaining = api_key.quota - api_key.usage_count
```

### Monitoring Usage

**Admin Dashboard:**
- Shows usage/quota with percentage bar
- Color-coded (green <70%, orange 70-90%, red >90%)
- Alerts when approaching limit

**Programmatic:**
```python
# Check quota status
if api_key.is_quota_exceeded():
    notify_admin("API key nearing quota limit")
```

### Resetting Usage Count

```python
# Manual reset (admin only)
api_key.usage_count = 0
api_key.save()

# Scheduled reset (e.g., monthly)
from celery import shared_task

@shared_task
def reset_monthly_quotas():
    APIKey.objects.filter(status='active').update(usage_count=0)
```

---

## IP Whitelisting

### Configuration

```python
# Allow specific IPs
api_key.allowed_ips = ["203.0.113.5", "198.51.100.42"]

# Allow CIDR range (requires additional logic)
api_key.allowed_ips = ["203.0.113.0/24"]

# Allow all (empty list)
api_key.allowed_ips = []
```

### Validation

```python
def is_ip_allowed(self, ip_address: str) -> bool:
    if not self.allowed_ips:
        return True  # No restrictions
    return ip_address in self.allowed_ips
```

### Behind Proxies

When behind load balancers or proxies:

```python
# Uses X-Forwarded-For header
x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
client_ip = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
```

**Important:** Configure trusted proxy IPs to prevent spoofing.

---

## Key Rotation

### When to Rotate

🔄 **Regular Rotation:** Every 90 days (recommended)  
⚠️ **Security Incident:** Immediately if key is compromised  
🔧 **Personnel Changes:** When team members leave  
📝 **Compliance:** As required by security policies  

### Rotation Process

1. **Generate New Key** (while old key still active)
2. **Deploy New Key** to applications
3. **Grace Period** (both keys work)
4. **Monitor Usage** of old key
5. **Revoke Old Key** when usage drops to zero
6. **Verify** all services using new key

### Implementation

```python
# Step 1: Create new key
new_key = APIKey.objects.create(
    organization=old_key.organization,
    name=f"{old_key.name} (Rotated {timezone.now().date()})",
    scope=old_key.scope,
    quota=old_key.quota,
    allowed_ips=old_key.allowed_ips
)
plaintext = APIKey.generate_plaintext()
new_key.key = plaintext
new_key.save()

# Step 2: Mark old key for deprecation
old_key.metadata = {
    **old_key.metadata,
    'deprecated': True,
    'replaced_by': str(new_key.id),
    'deprecation_date': timezone.now().isoformat()
}
old_key.save()

# Step 3: Grace period (e.g., 7 days)
old_key.expires_at = timezone.now() + timedelta(days=7)
old_key.save()

# Step 4: Monitor old key usage
# (Check APIKeyUsageLog for entries with old_key.id)

# Step 5: Revoke old key
old_key.revoke(reason="Replaced by rotated key")
```

---

## Monitoring & Analytics

### Usage Logs

Every API key request is logged to `APIKeyUsageLog`:

```python
class APIKeyUsageLog:
    timestamp: datetime
    endpoint: str
    method: str
    ip_address: str
    user_agent: str
    status_code: int
    response_time_ms: int
    tokens_used: int  # For billing
    documents_searched: int
    error_message: str
    metadata: dict
```

### Analytics Queries

**Most Used Endpoints:**
```python
from django.db.models import Count
APIKeyUsageLog.objects.filter(api_key=key) \
    .values('endpoint') \
    .annotate(count=Count('id')) \
    .order_by('-count')[:10]
```

**Token Consumption:**
```python
from django.db.models import Sum
APIKeyUsageLog.objects.filter(api_key=key) \
    .aggregate(total_tokens=Sum('tokens_used'))
```

**Error Rate:**
```python
total = APIKeyUsageLog.objects.filter(api_key=key).count()
errors = APIKeyUsageLog.objects.filter(api_key=key, status_code__gte=400).count()
error_rate = (errors / total) * 100
```

**Unique IPs:**
```python
APIKeyUsageLog.objects.filter(api_key=key) \
    .values('ip_address') \
    .distinct() \
    .count()
```

### Alerting

**Quota Threshold:**
```python
if api_key.quota:
    usage_percent = (api_key.usage_count / api_key.quota) * 100
    if usage_percent >= 80:
        send_alert(f"API key {api_key.name} at {usage_percent}% quota")
```

**Anomalous Usage:**
```python
# Spike detection
recent_hour = APIKeyUsageLog.objects.filter(
    api_key=key,
    timestamp__gte=timezone.now() - timedelta(hours=1)
).count()

if recent_hour > key.rate_limit_per_minute * 60 * 0.8:
    send_alert(f"Unusual spike: {recent_hour} requests in last hour")
```

**Unauthorized IP:**
```python
# All failed auth attempts
failed_auths = APIKeyUsageLog.objects.filter(
    api_key=key,
    status_code=401
).values('ip_address').distinct()
```

---

## Best Practices

### ✅ DO

1. **Store Keys Securely**
   - Use environment variables
   - Never commit to Git
   - Use secret management (AWS Secrets Manager, HashiCorp Vault)

2. **Use Narrow Scopes**
   - read-only for analytics
   - upload-only for ingestion
   - full-access only when necessary

3. **Set Quotas**
   - Prevent runaway costs
   - Detect abnormal usage
   - Force explicit increases

4. **Monitor Usage**
   - Review usage logs regularly
   - Set up alerts
   - Track costs

5. **Rotate Regularly**
   - 90-day rotation policy
   - Automated rotation pipelines
   - Grace period for updates

6. **Document Keys**
   - Name keys descriptively
   - Track which services use which keys
   - Maintain rotation schedule

### ❌ DON'T

1. **Never Log Keys**
   - Don't include in application logs
   - Sanitize request/response logs
   - Use key_id for tracking, not key value

2. **Don't Share Keys**
   - One key per service/environment
   - Never email keys
   - Don't reuse across environments

3. **Don't Use Full-Access Unnecessarily**
   - Use narrowest scope possible
   - Separate keys for different functions
   - Principle of least privilege

4. **Don't Hardcode**
   - Never in source code
   - Never in client-side code
   - Always use environment variables

5. **Don't Ignore Alerts**
   - Investigate quota warnings
   - Review failed auth attempts
   - Respond to anomalous usage

---

## Troubleshooting

### "Invalid API key"

**Causes:**
- Typo in key value
- Key was revoked
- Key was deleted

**Solutions:**
- Double-check key value (no spaces)
- Verify key status in admin
- Generate new key if needed

### "API key quota exceeded"

**Causes:**
- usage_count >= quota
- No quota reset

**Solutions:**
```python
# Check current usage
api_key.usage_count  # e.g., 10000
api_key.quota  # e.g., 10000

# Option 1: Increase quota
api_key.quota = 20000
api_key.save()

# Option 2: Reset usage (monthly cycle)
api_key.usage_count = 0
api_key.save()
```

### "API key not authorized from IP address"

**Causes:**
- IP not in allowed_ips list
- Behind proxy/load balancer
- IP whitelist misconfigured

**Solutions:**
```python
# Check current IP restrictions
api_key.allowed_ips  # e.g., ["203.0.113.5"]

# Option 1: Add IP to whitelist
api_key.allowed_ips.append("198.51.100.42")
api_key.save()

# Option 2: Remove IP restrictions
api_key.allowed_ips = []
api_key.save()

# Option 3: Check X-Forwarded-For header
# Ensure proxy is properly configured
```

### "API key has expired"

**Causes:**
- expires_at date passed
- Auto-expired by system

**Solutions:**
```python
# Check expiration
api_key.expires_at  # e.g., 2024-12-31 23:59:59

# Option 1: Extend expiration
api_key.expires_at = timezone.now() + timedelta(days=90)
api_key.status = APIKey.Status.ACTIVE
api_key.save()

# Option 2: Create new key
new_key = APIKey.objects.create(...)
```

### Rate Limit Exceeded

**Error:**
```
HTTP 429 Too Many Requests
Retry-After: 45
```

**Solutions:**
- Wait for rate limit window to reset
- Increase custom rate limit
- Implement exponential backoff
- Distribute load across multiple keys

---

## Security Incident Response

### Compromised Key Detected

1. **Immediate Actions:**
   ```python
   # Revoke immediately
   api_key.revoke(reason="Security incident - key compromised")
   
   # Review recent usage
   suspicious_logs = APIKeyUsageLog.objects.filter(
       api_key=api_key,
       timestamp__gte=timezone.now() - timedelta(hours=24)
   )
   ```

2. **Investigation:**
   - Review usage logs for anomalous patterns
   - Check IP addresses
   - Identify affected resources

3. **Recovery:**
   - Generate new key
   - Update all services
   - Notify stakeholders

4. **Prevention:**
   - Implement IP whitelisting
   - Reduce quota
   - Add monitoring alerts

---

## Compliance & Auditing

### Audit Trail

All API key operations are logged:

```python
# Creation
logger.info(f"API key created: {api_key.name}", extra={
    'api_key_id': api_key.id,
    'organization': api_key.organization.name,
    'scope': api_key.scope
})

# Usage
logger.info(f"API key used", extra={
    'api_key_id': api_key.id,
    'endpoint': request.path,
    'ip_address': client_ip
})

# Revocation
logger.warning(f"API key revoked: {reason}", extra={
    'api_key_id': api_key.id,
    'revoked_by': admin_user.email
})
```

### Retention Policy

```python
# Delete old usage logs (GDPR compliance)
cutoff_date = timezone.now() - timedelta(days=365)
APIKeyUsageLog.objects.filter(timestamp__lt=cutoff_date).delete()
```

---

## Summary

This comprehensive API key implementation provides:

✅ Military-grade encryption (AES-256)  
✅ Scope-based authorization  
✅ Per-key rate limiting  
✅ Quota management  
✅ IP whitelisting  
✅ Automatic expiration  
✅ Detailed usage tracking  
✅ Instant revocation  
✅ Comprehensive logging  
✅ Analytics & alerting  

**Remember:** Security is a process, not a product. Regularly review and update your API key policies!

---

## Additional Resources

- [Django REST Framework Authentication](https://www.django-rest-framework.org/api-guide/authentication/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [OAuth 2.0 RFC 6749](https://datatracker.ietf.org/doc/html/rfc6749)
- [NIST Digital Identity Guidelines](https://pages.nist.gov/800-63-3/)

---

**Last Updated:** 2025-01-17  
**Version:** 1.0.0  
**Maintained By:** CBaaS Security Team
