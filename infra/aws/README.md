# CBaaS AWS Infrastructure Automation

Production-ready infrastructure automation for deploying CBaaS (Chatbot-as-a-Service) to AWS using Docker and AWS CLI.

## 🏗️ Architecture Overview

```
┌─────────────────┐
│   Route 53      │ (DNS)
└────────┬────────┘
         │
    ┌────┴────────────────┐
    │                     │
┌───▼──────────┐    ┌────▼────────────┐
│ CloudFront   │    │ ALB (HTTPS)     │
│ + WAF        │    │ + ACM Cert      │
└───┬──────────┘    └────┬────────────┘
    │                    │
┌───▼──────────┐    ┌────▼────────────┐
│ S3 (React)   │    │ ECS Fargate     │
│ Private +OAC │    │ - Backend       │
└──────────────┘    │ - Worker        │
                    └────┬────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         ┌────▼─────┐        ┌─────▼─────┐
         │ RDS PG   │        │ ElastiCache│
         │ Multi-AZ │        │ Redis+TLS  │
         └──────────┘        └───────────┘
```

### Key Components

- **Frontend**: React SPA → S3 → CloudFront (OAC, edge caching)
- **Backend**: Django + Gunicorn → ECS Fargate → ALB
- **Worker**: Celery → ECS Fargate (same image as backend)
- **Database**: RDS PostgreSQL 16 (Multi-AZ, encrypted)
- **Cache**: ElastiCache Redis 7.1 (TLS + AUTH token)
- **Storage**: S3 buckets (static files + private media)
- **Networking**: VPC with public/private subnets, NAT Gateways (HA)
- **Security**: WAF, Security Groups (least privilege), Secrets Manager

## 📋 Prerequisites

### Required Tools
- **AWS CLI v2** ([install](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html))
- **Docker** ([install](https://docs.docker.com/get-docker/))
- **Node.js 20+** ([install](https://nodejs.org/))
- **Git**
- **jq** (JSON processor) - `apt install jq` or `brew install jq`
- **openssl** (for password generation)

### AWS Account Setup
1. **AWS Account** with admin access
2. **AWS CLI configured**:
   ```bash
   aws configure
   # Enter: Access Key, Secret Key, Region (e.g., ap-south-1), Output format (json)
   ```
3. **ACM Certificates** (optional, for custom domains):
   - CloudFront certificate: us-east-1 region
   - ALB certificate: your deployment region

## 🚀 Quick Start

### 1. Configuration

Edit `infra/aws/config.sh`:

```bash
# Mandatory
export AWS_REGION="ap-south-1"
export PROJECT_NAME="cbaas"
export ENVIRONMENT="prod"

# Optional - for custom domains
export DOMAIN_NAME="yourdomain.com"
export FRONTEND_DOMAIN="app.yourdomain.com"
export BACKEND_DOMAIN="api.yourdomain.com"
export CLOUDFRONT_CERT_ARN="arn:aws:acm:us-east-1:..."  # CloudFront cert
export ALB_CERT_ARN="arn:aws:acm:ap-south-1:..."        # ALB cert
```

### 2. Infrastructure Setup (One-Time)

Run the master setup script:

```bash
cd infra/aws
bash infra-setup.sh
```

This will provision (in order):
1. VPC, subnets, NAT gateways
2. Security groups
3. S3 buckets (frontend, static, media)
4. Secrets Manager entries
5. RDS PostgreSQL (Multi-AZ)
6. ElastiCache Redis
7. IAM roles
8. ECR repositories
9. Application Load Balancer
10. ECS cluster and services
11. CloudFront distribution

**Duration**: ~20-30 minutes (RDS and CloudFront are slow)

### 3. Deploy Backend

```bash
cd infra/aws
bash deploy-backend.sh
```

This will:
- Build Django Docker image
- Push to ECR
- Run database migrations
- Collect static files to S3
- Update ECS services (blue/green deployment)

### 4. Deploy Frontend

```bash
cd infra/aws
bash deploy-frontend.sh
```

This will:
- Build React production bundle
- Sync to S3 (with optimal cache headers)
- Invalidate CloudFront cache

### 5. Verify Deployment

```bash
# Check backend health
curl http://<ALB_DNS>/api/healthz

# Check frontend
curl https://<CLOUDFRONT_DOMAIN>

# View logs
aws logs tail /ecs/cbaas/backend --follow
```

## 📂 Project Structure

```
infra/aws/
├── config.sh                    # Configuration variables
├── infra-setup.sh              # Master setup script
├── 01-setup-vpc.sh             # VPC and networking
├── 02-setup-security-groups.sh # Security groups
├── 03-setup-s3.sh              # S3 buckets
├── 04-setup-secrets.sh         # Secrets Manager
├── 05-setup-rds.sh             # RDS PostgreSQL
├── 06-setup-redis.sh           # ElastiCache Redis
├── 07-setup-iam.sh             # IAM roles
├── 08-setup-ecr.sh             # ECR repositories
├── 09-setup-alb.sh             # Application Load Balancer
├── 10-setup-ecs.sh             # ECS cluster and services
├── 11-setup-cloudfront.sh      # CloudFront distribution
├── deploy-backend.sh           # Backend deployment
├── deploy-frontend.sh          # Frontend deployment
└── *.env                       # Generated resource IDs
```

## 🔒 Security Features

### Network Security
- ✅ Private subnets for ECS, RDS, Redis
- ✅ Public subnets only for ALB and NAT Gateways
- ✅ Security groups with least privilege
- ✅ No public RDS/Redis access

### Data Security
- ✅ RDS encryption at rest
- ✅ S3 encryption (AES-256)
- ✅ Redis TLS + AUTH token
- ✅ Secrets in AWS Secrets Manager
- ✅ IAM roles (no hardcoded credentials)

### Application Security
- ✅ HTTPS only (CloudFront + ALB)
- ✅ WAF protection (SQL injection, XSS, rate limiting)
- ✅ CORS configured
- ✅ CSRF protection
- ✅ Secure headers (HSTS, etc.)

## 📊 Monitoring & Logs

### CloudWatch Logs
```bash
# Backend logs
aws logs tail /ecs/cbaas/backend --follow --format short

# Worker logs
aws logs tail /ecs/cbaas/worker --follow --format short

# RDS logs
aws rds describe-db-log-files --db-instance-identifier cbaas-postgres-prod
```

### Metrics
- ECS service metrics: CPU, memory, task count
- ALB metrics: Request count, latency, 5xx errors
- RDS metrics: Connections, CPU, storage
- Redis metrics: CPU, memory, connections

### Alerts (Manual Setup Required)
Create CloudWatch alarms for:
- ECS task failures
- ALB 5xx errors > threshold
- RDS CPU > 80%
- Redis memory > 80%

## 💰 Cost Optimization

### Current Setup (Approximate Monthly Costs)
- **ECS Fargate**: ~$30 (0.5 vCPU, 1GB RAM, 2 backend + 1 worker)
- **RDS t3.micro**: ~$15 (Multi-AZ: ~$30)
- **ElastiCache t3.micro**: ~$12
- **ALB**: ~$18
- **NAT Gateways**: ~$65 (2 AZs)
- **CloudFront**: ~$1 + data transfer
- **S3**: ~$1
- **Total**: ~$140-170/month

### Savings Tips
1. **NAT Gateways**: Use single NAT (not HA) or VPC endpoints
2. **RDS**: Use single-AZ for dev/staging
3. **Fargate Spot**: Enable for worker tasks
4. **Reserved Instances**: For predictable workloads
5. **S3 Lifecycle**: Delete old versions/incomplete uploads

## 🔄 CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deploy-prod.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [release]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1
      
      - name: Deploy Backend
        run: |
          cd infra/aws
          bash deploy-backend.sh

  deploy-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: ap-south-1
      
      - name: Deploy Frontend
        run: |
          cd infra/aws
          bash deploy-frontend.sh
```

## 🛠️ Maintenance

### Update Backend
```bash
# Make code changes, then:
cd infra/aws
bash deploy-backend.sh
```

### Update Frontend
```bash
# Make code changes, then:
cd infra/aws
bash deploy-frontend.sh
```

### Scale ECS Services
```bash
# Update desired count
aws ecs update-service \
  --cluster cbaas-cluster-prod \
  --service cbaas-backend-service \
  --desired-count 4
```

### Database Migrations
```bash
# Migrations run automatically during deploy-backend.sh
# Or run manually:
aws ecs run-task \
  --cluster cbaas-cluster-prod \
  --task-definition cbaas-backend-prod \
  --launch-type FARGATE \
  --overrides '{"containerOverrides":[{"name":"backend","command":["python","manage.py","migrate"]}]}'
```

### Backup & Restore

**RDS Backups**:
- Automated daily backups (7-day retention)
- Manual snapshot before major changes:
  ```bash
  aws rds create-db-snapshot \
    --db-instance-identifier cbaas-postgres-prod \
    --db-snapshot-identifier cbaas-manual-$(date +%Y%m%d)
  ```

**Restore from Snapshot**:
```bash
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier cbaas-postgres-restored \
  --db-snapshot-identifier cbaas-manual-20250101
```

## 🐛 Troubleshooting

### ECS Tasks Failing to Start

**Check logs**:
```bash
aws logs tail /ecs/cbaas/backend --follow
```

**Common issues**:
- Secrets not found → Check Secrets Manager permissions
- Can't connect to RDS → Check security groups
- Image pull errors → Check ECR permissions

### 502 Bad Gateway from ALB

**Check target health**:
```bash
aws elbv2 describe-target-health \
  --target-group-arn <TARGET_GROUP_ARN>
```

**Common causes**:
- Health check failing (`/api/healthz` returns non-200)
- ECS tasks not registering with target group
- Security group blocking ALB → ECS

### CloudFront 403 Errors

**Check**:
- S3 bucket policy allows CloudFront OAC
- Distribution status is "Deployed"
- Origin Access Control is attached

**Fix**:
```bash
# Re-run CloudFront setup
bash 11-setup-cloudfront.sh
```

## 📚 Additional Resources

- [AWS ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [RDS Security](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.html)
- [CloudFront Performance](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/ConfiguringCaching.html)
- [Django on AWS](https://docs.djangoproject.com/en/4.2/howto/deployment/)

## 🤝 Contributing

1. Test changes in a separate AWS account/environment
2. Update documentation for any new features
3. Follow infrastructure-as-code best practices
4. Make scripts idempotent and error-resilient

## 📄 License

This infrastructure code is part of the CBaaS project.

---

**Need Help?** Open an issue or contact the DevOps team.
