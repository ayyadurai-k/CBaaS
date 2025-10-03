# AWS Infrastructure Scripts Summary

This directory contains production-ready infrastructure automation for deploying CBaaS to AWS.

## 📁 Files Overview

### Configuration
- **config.sh** - Central configuration file (edit this first!)

### Infrastructure Setup (Run in Order)
1. **01-setup-vpc.sh** - VPC, subnets, NAT gateways, route tables
2. **02-setup-security-groups.sh** - Security groups (ALB, ECS, RDS, Redis)
3. **03-setup-s3.sh** - S3 buckets for frontend, static, media files
4. **04-setup-secrets.sh** - AWS Secrets Manager entries
5. **05-setup-rds.sh** - RDS PostgreSQL (Multi-AZ)
6. **06-setup-redis.sh** - ElastiCache Redis (TLS enabled)
7. **07-setup-iam.sh** - IAM roles and policies
8. **08-setup-ecr.sh** - ECR repositories
9. **09-setup-alb.sh** - Application Load Balancer
10. **10-setup-ecs.sh** - ECS cluster, task definitions, services
11. **11-setup-cloudfront.sh** - CloudFront distribution
12. **12-setup-waf.sh** - AWS WAF (optional)

### Master Scripts
- **infra-setup.sh** - Runs all setup scripts in order (ONE-TIME SETUP)
- **deploy-backend.sh** - Deploy Django backend to ECS
- **deploy-frontend.sh** - Deploy React frontend to CloudFront/S3
- **cleanup.sh** - Delete all AWS resources (⚠️ DANGEROUS)

### Generated Files (Do Not Edit)
- **vpc-info.env** - VPC resource IDs
- **sg-info.env** - Security group IDs
- **s3-info.env** - S3 bucket names
- **secrets-info.env** - Secrets Manager secret names
- **rds-info.env** - RDS endpoint and credentials
- **redis-info.env** - Redis endpoint
- **iam-info.env** - IAM role ARNs
- **ecr-info.env** - ECR repository URIs
- **alb-info.env** - ALB DNS and ARNs
- **ecs-info.env** - ECS cluster and service names
- **cloudfront-info.env** - CloudFront distribution ID and domain
- **waf-info.env** - WAF ACL ARN
- **backend-task-definition.json** - ECS backend task definition
- **worker-task-definition.json** - ECS worker task definition
- **infrastructure-summary.txt** - Complete infrastructure summary

## 🚀 Quick Start

### First Time Setup
```bash
cd infra/aws

# 1. Configure
nano config.sh  # or vim, or any editor

# 2. Run infrastructure setup (takes ~30-40 minutes)
bash infra-setup.sh

# 3. Deploy backend
bash deploy-backend.sh

# 4. Deploy frontend
bash deploy-frontend.sh
```

### Subsequent Deployments
```bash
# Deploy only backend
bash deploy-backend.sh

# Deploy only frontend
bash deploy-frontend.sh
```

### Optional: Enable WAF
```bash
bash 12-setup-waf.sh
```

## 📖 Documentation

- **README.md** - Complete documentation with architecture, security, costs
- **QUICKSTART.md** - Step-by-step deployment guide
- See also: `.github/workflows/deploy-aws.yml` for CI/CD automation

## ⚙️ Configuration

Edit `config.sh` before running any scripts:

```bash
# Mandatory
export AWS_REGION="ap-south-1"
export PROJECT_NAME="cbaas"
export ENVIRONMENT="prod"

# Optional (for custom domains)
export DOMAIN_NAME="yourdomain.com"
export FRONTEND_DOMAIN="app.yourdomain.com"
export BACKEND_DOMAIN="api.yourdomain.com"
export CLOUDFRONT_CERT_ARN="arn:aws:acm:..."
export ALB_CERT_ARN="arn:aws:acm:..."
```

## 🔒 Security Features

- ✅ Private subnets for ECS, RDS, Redis
- ✅ Security groups with least privilege
- ✅ Secrets in AWS Secrets Manager
- ✅ RDS encryption at rest
- ✅ Redis TLS + AUTH token
- ✅ S3 private with CloudFront OAC
- ✅ HTTPS only (CloudFront + ALB)
- ✅ WAF protection (optional)

## 💰 Estimated Costs

- **Development**: ~$50-80/month
- **Production**: ~$140-170/month
- **Enterprise**: ~$300-500/month

See README.md for detailed breakdown.

## 🛠️ Troubleshooting

### Scripts fail on Windows
**Solution**: Use Git Bash, not PowerShell

### Permission errors
**Solution**: Ensure AWS credentials have admin access

### NAT Gateway costs too high
**Solution**: Use single NAT or VPC endpoints (edit 01-setup-vpc.sh)

### CloudFront takes forever
**Solution**: Normal - CloudFront deployments take 15-30 minutes

## 🧹 Cleanup

⚠️ **WARNING**: This deletes ALL resources!

```bash
bash cleanup.sh
```

You'll need to confirm 3 times. This is irreversible!

## 📝 Notes

- All scripts are **idempotent** - safe to rerun
- Generated `.env` files are sourced by deployment scripts
- Task definitions are regenerated on each backend deployment
- CloudFront invalidations can take 5-15 minutes

## 🆘 Need Help?

1. Check logs: `aws logs tail /ecs/cbaas/backend --follow`
2. Review README.md troubleshooting section
3. Check AWS Console for detailed error messages
4. Verify configuration in `config.sh`

---

**Made with ❤️ for CBaaS**
