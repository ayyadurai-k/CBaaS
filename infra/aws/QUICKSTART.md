# Quick Start Guide - AWS Deployment

## Prerequisites Setup

### 1. Install Required Tools

**Windows (PowerShell)**:
```powershell
# AWS CLI
msiexec.exe /i https://awscli.amazonaws.com/AWSCLIV2.msi

# Docker Desktop
# Download from: https://www.docker.com/products/docker-desktop

# Node.js
# Download from: https://nodejs.org/

# jq (JSON processor)
choco install jq

# Git Bash (for running shell scripts)
# Download from: https://git-scm.com/download/win
```

**Linux/macOS**:
```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Docker
# Follow: https://docs.docker.com/engine/install/

# Node.js
# Use nvm or download from nodejs.org

# jq
sudo apt install jq  # Ubuntu/Debian
brew install jq      # macOS
```

### 2. Configure AWS Credentials

```bash
aws configure
```

Enter:
- **AWS Access Key ID**: Your IAM access key
- **AWS Secret Access Key**: Your IAM secret key
- **Default region**: `ap-south-1` (or your preferred region)
- **Default output format**: `json`

Verify:
```bash
aws sts get-caller-identity
```

### 3. (Optional) Request ACM Certificates

For custom domains with HTTPS:

**CloudFront Certificate (us-east-1)**:
```bash
aws acm request-certificate \
  --domain-name app.yourdomain.com \
  --validation-method DNS \
  --region us-east-1
```

**ALB Certificate (your region)**:
```bash
aws acm request-certificate \
  --domain-name api.yourdomain.com \
  --validation-method DNS \
  --region ap-south-1
```

Validate via DNS records, then note the ARNs.

## Deployment Steps

### Step 1: Configure Project

Edit `infra/aws/config.sh`:

```bash
export AWS_REGION="ap-south-1"
export PROJECT_NAME="cbaas"
export ENVIRONMENT="prod"

# Optional - for custom domains
export DOMAIN_NAME="yourdomain.com"
export FRONTEND_DOMAIN="app.yourdomain.com"
export BACKEND_DOMAIN="api.yourdomain.com"
export CLOUDFRONT_CERT_ARN="arn:aws:acm:us-east-1:123456789012:certificate/..."
export ALB_CERT_ARN="arn:aws:acm:ap-south-1:123456789012:certificate/..."
```

### Step 2: Run Infrastructure Setup

**On Windows** (use Git Bash):
```bash
cd infra/aws
bash infra-setup.sh
```

**On Linux/macOS**:
```bash
cd infra/aws
chmod +x *.sh
./infra-setup.sh
```

This will:
- ✅ Create VPC and networking (5 min)
- ✅ Create security groups (1 min)
- ✅ Create S3 buckets (1 min)
- ✅ Create secrets (1 min)
- ✅ Create RDS PostgreSQL (15 min) ⏰
- ✅ Create ElastiCache Redis (10 min) ⏰
- ✅ Create IAM roles (2 min)
- ✅ Create ECR repositories (1 min)
- ✅ Create ALB (5 min)
- ✅ Create ECS cluster (2 min)
- ✅ Create CloudFront (20 min) ⏰

**Total time**: ~30-40 minutes

### Step 3: Update Django Settings

Edit `backend/config/environments/prod.py`:

```python
# Change to use prod_aws.py
from .prod_aws import *
```

Or set environment variable in task definition:
```json
{"name": "DJANGO_SETTINGS_MODULE", "value": "config.environments.prod_aws"}
```

### Step 4: Deploy Backend

```bash
cd infra/aws
bash deploy-backend.sh
```

This will:
1. Build Django Docker image (~5 min)
2. Push to ECR (~2 min)
3. Run migrations (~1 min)
4. Collect static files (~1 min)
5. Update ECS services (~3 min)

**Total time**: ~12 minutes

### Step 5: Deploy Frontend

```bash
cd infra/aws
bash deploy-frontend.sh
```

This will:
1. Build React app (~2 min)
2. Sync to S3 (~1 min)
3. Invalidate CloudFront (~5 min)

**Total time**: ~8 minutes

### Step 6: Verify Deployment

**Check Backend**:
```bash
# Get ALB DNS
source infra/aws/alb-info.env
echo $ALB_DNS

# Test health endpoint
curl http://$ALB_DNS/api/healthz
```

Expected response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok"
  }
}
```

**Check Frontend**:
```bash
# Get CloudFront URL
source infra/aws/cloudfront-info.env
echo $CF_DOMAIN

# Open in browser
curl https://$CF_DOMAIN
```

### Step 7: Configure DNS (Optional)

If using custom domains, create DNS records:

**Frontend (CloudFront)**:
```
Type: CNAME
Name: app.yourdomain.com
Value: d123456789.cloudfront.net  # Your CF_DOMAIN
TTL: 300
```

**Backend (ALB)**:
```
Type: CNAME
Name: api.yourdomain.com
Value: cbaas-alb-prod-123456789.ap-south-1.elb.amazonaws.com  # Your ALB_DNS
TTL: 300
```

## Common Issues

### Issue: "Permission denied" on Windows

**Solution**: Run Git Bash as Administrator

### Issue: Docker not found

**Solution**: 
1. Install Docker Desktop
2. Start Docker Desktop
3. Verify: `docker --version`

### Issue: AWS CLI not found

**Solution**:
1. Install AWS CLI v2
2. Restart terminal
3. Verify: `aws --version`

### Issue: jq not found

**Solution**:
- Windows: `choco install jq` or download from https://stedolan.github.io/jq/
- Linux: `sudo apt install jq`
- macOS: `brew install jq`

### Issue: RDS creation failed - "DBSubnetGroupDoesNotCoverEnoughAZs"

**Solution**: Verify your region has at least 2 availability zones in `config.sh`:
```bash
export AVAILABILITY_ZONE_1="${AWS_REGION}a"
export AVAILABILITY_ZONE_2="${AWS_REGION}b"
```

### Issue: ECS tasks not starting

**Check logs**:
```bash
aws logs tail /ecs/cbaas/backend --follow
```

**Common causes**:
- Wrong environment variables
- Secrets not accessible
- Docker image pull failed

## Next Steps

1. **Enable Monitoring**:
   - Set up CloudWatch alarms
   - Configure SNS for alerts

2. **Set Up CI/CD**:
   - Use provided GitHub Actions workflow
   - Automate deployments on push to `release` branch

3. **Configure Backups**:
   - RDS automated backups (already enabled)
   - Test restore process

4. **Security Hardening**:
   - Enable WAF (script available)
   - Review security group rules
   - Enable CloudTrail

5. **Performance Optimization**:
   - Monitor CloudWatch metrics
   - Adjust ECS task sizes
   - Tune database parameters

## Cost Estimate

**Monthly costs (approximate)**:
- Development: ~$50-80
- Production: ~$140-170
- Enterprise: ~$300-500

See README.md for detailed breakdown.

## Support

- Documentation: `infra/aws/README.md`
- AWS Console: https://console.aws.amazon.com/
- CloudWatch Logs: Check `/ecs/cbaas/backend` log group

---

**Ready to deploy?** Start with Step 1! 🚀
