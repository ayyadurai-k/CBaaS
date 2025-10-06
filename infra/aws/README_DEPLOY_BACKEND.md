# 🚀 Backend Deployment Guide - Django on AWS ECS

Complete guide for deploying the CBaaS Django backend to AWS ECS Fargate with PostgreSQL RDS, using GitHub Actions and OIDC authentication.

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   GitHub        │    │   AWS ECS        │    │   AWS RDS       │
│   Actions       │    │   (Fargate)      │    │   (PostgreSQL)  │
│                 │────▶│                  │────▶│                 │
│  OIDC Auth      │    │  Django App      │    │  Database       │
│  Docker Build   │    │  Auto-scaling    │    │  Private subnet │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │
         │                        │
         ▼                        ▼
┌─────────────────┐    ┌──────────────────┐
│   Amazon ECR    │    │   Load Balancer  │
│   (Docker       │    │   (Public HTTPS) │
│    Registry)    │    │                  │
└─────────────────┘    └──────────────────┘
         │                        │
         │                        ▼
         │              ┌──────────────────┐
         │              │   CloudWatch     │
         │              │   (Logs &        │
         └──────────────▶   Monitoring)    │
                        └──────────────────┘
```

### Key Components

| Component | Purpose | Configuration |
|-----------|---------|---------------|
| **Amazon ECR** | Docker image registry | `cbaas-backend` repository |
| **ECS Fargate** | Containerized compute | 0.5 vCPU, 1GB RAM, auto-scaling |
| **RDS PostgreSQL** | Database | `db.t4g.micro`, private subnet |
| **Application Load Balancer** | HTTPS endpoint | Public-facing, health checks |
| **Secrets Manager** | Environment variables | Django settings, DB credentials |
| **CloudWatch** | Logging & monitoring | 7-day retention |
| **IAM + OIDC** | GitHub Actions auth | No long-lived credentials |

---

## 🚦 Prerequisites

### Required Tools
- **AWS CLI v2** configured with administrative permissions
- **Docker** for building images locally (optional)
- **Git** for repository operations
- **Bash** shell (Windows: Git Bash or WSL)

### AWS Account Setup
- AWS Account with billing configured
- Default VPC in `ap-south-1` region (or modify scripts for custom VPC)
- Sufficient service quotas for ECS and RDS

### GitHub Repository
- Repository: `ayyadurai-k/CBaaS`
- Admin access to configure secrets
- Actions enabled

---

## 🛠️ Initial Setup

### Step 1: Run Infrastructure Script

```bash
# Make script executable (Linux/Mac/Git Bash)
chmod +x infra/aws/setup-aws-backend.sh

# Run setup
./infra/aws/setup-aws-backend.sh cbaas 577897067437

# Expected runtime: 10-15 minutes (RDS creation is slow)
```

**What This Creates:**
- ✅ ECR repository: `cbaas-backend`
- ✅ VPC security groups (ALB, ECS, RDS)
- ✅ RDS PostgreSQL instance (`db.t4g.micro`)
- ✅ Application Load Balancer with target group
- ✅ ECS Cluster: `cbaas-cluster`
- ✅ IAM roles for ECS tasks and GitHub Actions
- ✅ Secrets Manager entry with Django environment variables
- ✅ CloudWatch log group

### Step 2: Configure GitHub Secrets

Add these secrets to your GitHub repository (`Settings` → `Secrets and variables` → `Actions`):

| Secret Name | Value | Example |
|-------------|--------|---------|
| `AWS_ROLE_ARN` | IAM role for OIDC | `arn:aws:iam::577897067437:role/GitHubActionsBackendDeployRole` |
| `ECR_REPOSITORY` | ECR repository URI | `577897067437.dkr.ecr.ap-south-1.amazonaws.com/cbaas-backend` |
| `ECS_CLUSTER` | ECS cluster name | `cbaas-cluster` |
| `ECS_SERVICE` | ECS service name | `cbaas-backend-service` |
| `TARGET_GROUP_ARN` | ALB target group ARN | `arn:aws:elasticloadbalancing:ap-south-1:...` |

**Copy values from setup script output**

### Step 3: Verify Django Configuration

Ensure your Django settings work with environment variables:

```python
# config/environments/prod.py
import os
from .base import *

DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database from environment
DATABASES = {
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL'))
}

# CORS settings
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS', 'True').lower() == 'true'
```

---

## 🚀 Deployment Methods

### Method 1: Automated (Recommended)
Push to `release` branch triggers automatic deployment:

```bash
git checkout main
git pull origin main

# Make your changes to backend/
git add backend/
git commit -m "feat: add new API endpoint"

# Deploy via release branch
git checkout release
git merge main
git push origin release
```

**GitHub Actions will:**
1. Build Docker image
2. Push to ECR with tag `release-<commit-sha>`
3. Update ECS task definition
4. Deploy to ECS service
5. Wait for stability
6. Verify health

### Method 2: Manual Deployment

```bash
# From project root
chmod +x infra/aws/deploy_backend.sh
./infra/aws/deploy_backend.sh cbaas 577897067437 v1.0.0
```

**Runtime:** 3-5 minutes

---

## 🔧 Configuration Management

### Environment Variables (AWS Secrets Manager)

Located at: `cbaas/backend/env`

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django cryptographic key | Auto-generated 50-char string |
| `DEBUG` | Debug mode | `False` |
| `ALLOWED_HOSTS` | Permitted hosts | `alb-dns-name.amazonaws.com,api.yourdomain.com` |
| `DATABASE_URL` | PostgreSQL connection | `postgres://user:pass@host:5432/db` |
| `CORS_ALLOWED_ORIGINS` | Frontend origins | `https://yourdomain.com` |

**Update secrets:**
```bash
aws secretsmanager update-secret \
  --secret-id cbaas/backend/env \
  --secret-string '{"DEBUG":"False","NEW_VAR":"value"}'
```

### Database Migrations

**Automatic** (in Dockerfile):
```dockerfile
RUN python manage.py migrate --settings=config.environments.prod
```

**Manual** (via ECS exec):
```bash
# Get running task ARN
TASK_ARN=$(aws ecs list-tasks --cluster cbaas-cluster --service-name cbaas-backend-service --query 'taskArns[0]' --output text)

# Execute migration
aws ecs execute-command \
  --cluster cbaas-cluster \
  --task $TASK_ARN \
  --container cbaas-backend \
  --interactive \
  --command "python manage.py migrate"
```

---

## 📊 Monitoring & Debugging

### Application Logs

```bash
# View container logs via Docker (local development)
docker logs <container-id> --follow

# For production debugging, use ECS exec to access running containers
aws ecs execute-command \
  --cluster cbaas-cluster \
  --task <task-arn> \
  --container cbaas-backend \
  --interactive \
  --command "/bin/bash"
```

### Service Health

```bash
# ECS service status
aws ecs describe-services \
  --cluster cbaas-cluster \
  --services cbaas-backend-service

# Task details
aws ecs describe-tasks \
  --cluster cbaas-cluster \
  --tasks $(aws ecs list-tasks --cluster cbaas-cluster --service-name cbaas-backend-service --query 'taskArns[0]' --output text)

# ALB target health
aws elbv2 describe-target-health \
  --target-group-arn <TARGET_GROUP_ARN>
```

### Application Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `http://alb-dns/admin/` | Django admin | HTTP 200/302 |
| `http://alb-dns/health/` | Health check | HTTP 200 |
| `http://alb-dns/api/v1/` | API root | HTTP 200 |

---

## 🔒 Security Configuration

### Network Security
- **ECS tasks**: Private subnets, no public IP required
- **RDS**: Private subnet, only accessible from ECS security group
- **ALB**: Public subnet, HTTPS only (add SSL certificate)

### IAM Permissions

**ECS Task Execution Role:**
- ECR image pull
- CloudWatch log creation
- Secrets Manager read

**GitHub Actions Role:**
- ECR push/pull
- ECS service updates
- Task definition registration
- Limited to `ayyadurai-k/CBaaS:release` branch

### Secrets Management
- No hardcoded credentials in code
- All sensitive data in AWS Secrets Manager
- Automatic rotation available for RDS passwords

---

## 🚨 Troubleshooting

### Common Issues

#### 1. Service Won't Start
```bash
# Check task logs
aws logs tail /aws/ecs/cbaas-backend --follow

# Common causes:
# - Missing environment variables
# - Database connection failure
# - Image build errors
```

#### 2. "Service is unable to consistently start tasks"
```bash
# Check task definition resource allocation
aws ecs describe-task-definition --task-definition cbaas-backend-task

# Increase CPU/memory if needed:
# Edit task definition and redeploy
```

#### 3. ALB Health Checks Failing
```bash
# Check target group configuration
aws elbv2 describe-target-groups --names cbaas-tg

# Verify health check path exists in Django:
# Should respond with HTTP 200 at /health/ or /admin/
```

#### 4. Database Connection Issues
```bash
# Test RDS connectivity from ECS
aws ecs execute-command \
  --cluster cbaas-cluster \
  --task $TASK_ARN \
  --container cbaas-backend \
  --interactive \
  --command "python manage.py dbshell"
```

#### 5. GitHub Actions Failing
- **ECR Authentication**: Check `AWS_ROLE_ARN` secret
- **Task Definition**: Ensure it exists from initial setup
- **ECS Permissions**: Verify IAM role permissions

### Recovery Procedures

#### Rollback Deployment
```bash
# Get previous task definition revision
aws ecs describe-task-definition --task-definition cbaas-backend-task

# Update service to previous revision
aws ecs update-service \
  --cluster cbaas-cluster \
  --service cbaas-backend-service \
  --task-definition cbaas-backend-task:PREVIOUS_REVISION
```

#### Reset RDS Database
```bash
# Create snapshot before reset
aws rds create-db-snapshot \
  --db-instance-identifier cbaas-postgres \
  --db-snapshot-identifier cbaas-backup-$(date +%Y%m%d)

# Connect and reset (use carefully!)
# aws ecs execute-command to connect to Django and run migrations
```

---

## 💰 Cost Optimization

### Current Configuration Costs (ap-south-1)
- **ECS Fargate**: ~$15/month (0.5 vCPU, 1GB RAM, always on)
- **RDS db.t4g.micro**: ~$12/month
- **ALB**: ~$16/month
- **ECR**: ~$1/month (< 1GB)
- **CloudWatch**: ~$3/month (basic logs)

**Total: ~$47/month**

### Optimization Tips
1. **Use spot instances** for development environments
2. **Schedule ECS service** to 0 desired count during off-hours
3. **RDS**: Use Aurora Serverless for variable workloads
4. **CloudWatch**: Adjust log retention (currently 7 days)

---

## 🔄 Maintenance

### Regular Tasks

#### Weekly
- Check CloudWatch logs for errors
- Review RDS performance metrics
- Monitor ALB response times

#### Monthly
- Update base Docker images for security patches
- Review AWS costs and optimize
- Test backup/recovery procedures

#### Security Updates
```bash
# Update ECS task definition with new base image
# Rebuild and deploy with latest security patches
./infra/aws/deploy_backend.sh cbaas 577897067437 security-patch-$(date +%Y%m%d)
```

### Scaling Configuration

**Horizontal Scaling:**
```bash
# Update service desired count
aws ecs update-service \
  --cluster cbaas-cluster \
  --service cbaas-backend-service \
  --desired-count 3
```

**Vertical Scaling:**
Update task definition CPU/memory and redeploy.

---

## 🌐 Production Enhancements

### Custom Domain Setup
1. **Request SSL certificate** via ACM
2. **Update ALB listener** to use HTTPS
3. **Configure Route 53** DNS records
4. **Update CORS settings** for your domain

### Auto Scaling
```bash
# Create auto scaling target
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/cbaas-cluster/cbaas-backend-service \
  --min-capacity 1 \
  --max-capacity 10

# Create scaling policy based on CPU utilization
aws application-autoscaling put-scaling-policy \
  --policy-name cbaas-cpu-scaling \
  --service-namespace ecs \
  --scalable-dimension ecs:service:DesiredCount \
  --resource-id service/cbaas-cluster/cbaas-backend-service \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ECSServiceAverageCPUUtilization"
    }
  }'
```

### Monitoring & Alerting
- Set up CloudWatch alarms for service health
- Configure SNS notifications for deployment failures
- Implement application-level health checks

---

## 📋 Checklist

### Initial Setup
- [ ] Run `setup-aws-backend.sh`
- [ ] Configure GitHub secrets
- [ ] Update Django settings for environment variables
- [ ] Test manual deployment
- [ ] Verify GitHub Actions workflow

### Production Readiness
- [ ] Configure custom domain with SSL
- [ ] Set up auto scaling
- [ ] Configure monitoring and alerting
- [ ] Test backup and recovery procedures
- [ ] Document environment-specific configurations
- [ ] Security review and penetration testing

### Operations
- [ ] Monitor logs regularly
- [ ] Update Docker base images monthly
- [ ] Review AWS costs
- [ ] Test disaster recovery procedures
- [ ] Keep documentation updated

---

**🎉 Your Django backend is now production-ready on AWS ECS!**

For issues or questions, check the troubleshooting section or review CloudWatch logs for detailed error information.