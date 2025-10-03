# 🔧 Troubleshooting Guide

Common issues and solutions for AWS infrastructure deployment.

---

## 🚨 Script Execution Issues

### Issue: "Permission denied" on Windows
**Symptoms**: Scripts won't execute
**Solution**: 
```bash
# Use Git Bash instead of PowerShell
# Or WSL (Windows Subsystem for Linux)
```

### Issue: "bash: command not found"
**Symptoms**: Script commands fail
**Solution**:
```bash
# Make scripts executable (Linux/Mac)
chmod +x infra/aws/*.sh

# Ensure using bash, not sh
bash infra-setup.sh  # Correct
sh infra-setup.sh    # May fail
```

### Issue: "AWS CLI not found"
**Symptoms**: `aws: command not found`
**Solution**:
```bash
# Install AWS CLI v2
# Windows: https://awscli.amazonaws.com/AWSCLIV2.msi
# Linux: curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
# Mac: brew install awscli

# Verify
aws --version  # Should show v2.x
```

---

## 🔐 AWS Authentication Issues

### Issue: "Unable to locate credentials"
**Symptoms**: AWS commands fail with credential errors
**Solution**:
```bash
# Configure AWS CLI
aws configure

# Verify credentials work
aws sts get-caller-identity

# Should show:
# {
#   "UserId": "...",
#   "Account": "123456789012",
#   "Arn": "arn:aws:iam::123456789012:user/yourname"
# }
```

### Issue: "Access Denied" errors
**Symptoms**: AWS operations fail with 403 errors
**Solution**:
```bash
# Ensure IAM user/role has required permissions:
# - AdministratorAccess (for setup)
# - Or specific policies: EC2, ECS, RDS, S3, IAM, etc.

# Check current permissions
aws iam get-user
aws iam list-attached-user-policies --user-name YOUR_USERNAME
```

### Issue: "Region not configured"
**Symptoms**: Operations fail with missing region
**Solution**:
```bash
# Set default region
aws configure set region ap-south-1

# Or export in shell
export AWS_REGION=ap-south-1

# Verify
aws configure get region
```

---

## 🏗️ Infrastructure Setup Issues

### Issue: VPC creation fails - "CIDR overlap"
**Symptoms**: `01-setup-vpc.sh` fails with CIDR conflict
**Solution**:
```bash
# Edit config.sh, change VPC CIDR
export VPC_CIDR="10.1.0.0/16"  # Or another range
export PUBLIC_SUBNET_1_CIDR="10.1.1.0/24"
export PUBLIC_SUBNET_2_CIDR="10.1.2.0/24"
# ... update all subnets
```

### Issue: RDS creation fails - "DBSubnetGroupDoesNotCoverEnoughAZs"
**Symptoms**: `05-setup-rds.sh` fails
**Solution**:
```bash
# Verify AZs exist in your region
aws ec2 describe-availability-zones --region ap-south-1

# Update config.sh with valid AZs
export AVAILABILITY_ZONE_1="ap-south-1a"
export AVAILABILITY_ZONE_2="ap-south-1b"
```

### Issue: NAT Gateway creation slow
**Symptoms**: Script hangs at NAT Gateway creation
**Solution**:
```bash
# This is normal - NAT Gateways take 3-5 minutes
# Script includes wait command: aws ec2 wait nat-gateway-available

# To reduce costs, use single NAT Gateway:
# Edit 01-setup-vpc.sh, comment out NAT_GW_2 creation
# Update private route tables to use NAT_GW_1 only
```

### Issue: CloudFront distribution takes forever
**Symptoms**: `11-setup-cloudfront.sh` seems stuck
**Solution**:
```bash
# Normal - CloudFront deployments take 15-30 minutes
# Script doesn't wait by default to avoid blocking

# Check status manually:
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID \
  --query 'Distribution.Status'

# Status progression: InProgress → Deployed
```

---

## 🐳 Docker Issues

### Issue: "Docker not found"
**Symptoms**: `deploy-backend.sh` fails with docker errors
**Solution**:
```bash
# Install Docker Desktop
# Windows/Mac: https://www.docker.com/products/docker-desktop
# Linux: https://docs.docker.com/engine/install/

# Verify
docker --version
docker ps  # Should not error
```

### Issue: "Cannot connect to Docker daemon"
**Symptoms**: docker commands fail
**Solution**:
```bash
# Windows/Mac: Start Docker Desktop

# Linux: Start Docker service
sudo systemctl start docker

# Add user to docker group (Linux)
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Docker build fails - "no space left on device"
**Symptoms**: Build stops with disk space error
**Solution**:
```bash
# Clean up Docker
docker system prune -a --volumes

# Check disk space
docker system df
```

---

## 🚀 ECS Deployment Issues

### Issue: ECS tasks fail to start
**Symptoms**: Service shows 0 running tasks
**Solution**:
```bash
# Check CloudWatch Logs
aws logs tail /ecs/cbaas/backend --follow

# Common causes:
# 1. Image pull errors
aws ecr describe-images --repository-name cbaas-backend

# 2. Environment variable issues
aws ecs describe-task-definition --task-definition cbaas-backend-prod \
  --query 'taskDefinition.containerDefinitions[0].environment'

# 3. Secrets Manager access
aws secretsmanager get-secret-value --secret-id cbaas/prod/django-secret

# 4. Security group blocks traffic
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

### Issue: ECS tasks start but fail health checks
**Symptoms**: Tasks continuously restart
**Solution**:
```bash
# Check health check endpoint
# Get task public IP (if assignPublicIp=ENABLED) or use ECS Exec

# Verify health endpoint works:
curl http://TASK_IP:8000/api/healthz

# Common issues:
# - Database connection fails (check RDS endpoint)
# - Redis connection fails (check Redis endpoint)
# - Secret KEY missing (check Secrets Manager)

# View detailed logs
aws logs tail /ecs/cbaas/backend --follow --filter-pattern "ERROR"
```

### Issue: 502 Bad Gateway from ALB
**Symptoms**: ALB returns 502 error
**Solution**:
```bash
# Check target health
ALB_TG_ARN=$(cat infra/aws/alb-info.env | grep TARGET_GROUP_ARN | cut -d'=' -f2 | tr -d '"')
aws elbv2 describe-target-health --target-group-arn $ALB_TG_ARN

# Unhealthy reasons:
# - Target.FailedHealthChecks: Health endpoint failing
# - Target.NotRegistered: ECS tasks not registering
# - Target.Timeout: Security group blocking traffic

# Fix security group:
# Ensure ECS_SG allows inbound 8000 from ALB_SG
```

---

## 🗄️ Database Issues

### Issue: Can't connect to RDS from ECS
**Symptoms**: Database connection errors in logs
**Solution**:
```bash
# Verify RDS is running
aws rds describe-db-instances --db-instance-identifier cbaas-postgres-prod \
  --query 'DBInstances[0].DBInstanceStatus'

# Check security group
# RDS_SG should allow 5432 from ECS_SG

# Verify environment variables in task definition
aws ecs describe-task-definition --task-definition cbaas-backend-prod \
  --query 'taskDefinition.containerDefinitions[0].environment' | grep DB_

# Test connection from ECS task (using ECS Exec)
aws ecs execute-command \
  --cluster cbaas-cluster-prod \
  --task TASK_ID \
  --container backend \
  --interactive \
  --command "/bin/bash"

# Inside container:
python manage.py dbshell
```

### Issue: RDS storage full
**Symptoms**: "No space left on device" errors
**Solution**:
```bash
# Check current storage
aws rds describe-db-instances \
  --db-instance-identifier cbaas-postgres-prod \
  --query 'DBInstances[0].[AllocatedStorage,DBInstanceStatus]'

# Increase storage
aws rds modify-db-instance \
  --db-instance-identifier cbaas-postgres-prod \
  --allocated-storage 50 \
  --apply-immediately
```

### Issue: Redis connection timeout
**Symptoms**: Celery/cache operations fail
**Solution**:
```bash
# Verify Redis is running
aws elasticache describe-cache-clusters \
  --cache-cluster-id cbaas-redis-prod \
  --show-cache-node-info

# Check security group
# REDIS_SG should allow 6379 from ECS_SG

# Verify TLS connection (Redis uses 'rediss://')
# In task definition, REDIS_URL should be: rediss://...

# Test from ECS task
aws ecs execute-command \
  --cluster cbaas-cluster-prod \
  --task TASK_ID \
  --container backend \
  --interactive \
  --command "/bin/bash"

# Inside container:
redis-cli -h $REDIS_HOST -p $REDIS_PORT --tls -a $REDIS_PASSWORD ping
```

---

## ☁️ CloudFront Issues

### Issue: CloudFront returns 403 Forbidden
**Symptoms**: Frontend shows 403 error
**Solution**:
```bash
# Check S3 bucket policy
aws s3api get-bucket-policy --bucket cbaas-frontend-origin-prod

# Should allow cloudfront.amazonaws.com from your distribution
# Re-run CloudFront setup
bash infra/aws/11-setup-cloudfront.sh

# Verify OAC is attached
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID \
  --query 'Distribution.DistributionConfig.Origins.Items[0].OriginAccessControlId'
```

### Issue: CloudFront serves stale content
**Symptoms**: Changes not visible after deployment
**Solution**:
```bash
# Create cache invalidation
source infra/aws/cloudfront-info.env
aws cloudfront create-invalidation \
  --distribution-id $CF_DISTRIBUTION_ID \
  --paths "/*"

# Or run frontend deployment again
bash infra/aws/deploy-frontend.sh
```

### Issue: CloudFront SSL certificate error
**Symptoms**: HTTPS shows certificate warning
**Solution**:
```bash
# Certificate must be in us-east-1 for CloudFront
# Request new certificate:
aws acm request-certificate \
  --domain-name app.yourdomain.com \
  --validation-method DNS \
  --region us-east-1

# Add CNAME record for validation
# Update config.sh with certificate ARN
export CLOUDFRONT_CERT_ARN="arn:aws:acm:us-east-1:..."

# Re-run CloudFront setup
bash infra/aws/11-setup-cloudfront.sh
```

---

## 📦 S3 Issues

### Issue: S3 sync fails - "Access Denied"
**Symptoms**: `deploy-frontend.sh` can't upload to S3
**Solution**:
```bash
# Verify bucket exists
aws s3 ls s3://cbaas-frontend-origin-prod

# Check IAM permissions
# User needs s3:PutObject, s3:DeleteObject on bucket

# Check bucket policy (shouldn't block your IAM user)
aws s3api get-bucket-policy --bucket cbaas-frontend-origin-prod
```

### Issue: Static files not loading from S3
**Symptoms**: CSS/JS 404 errors
**Solution**:
```bash
# Ensure collectstatic ran
bash infra/aws/deploy-backend.sh  # Includes collectstatic

# Verify files in S3
aws s3 ls s3://cbaas-django-static-prod/static/

# Check Django settings
# STATIC_URL should point to S3 bucket URL
# STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
```

---

## 🔐 Secrets Manager Issues

### Issue: "SecretNotFoundException"
**Symptoms**: ECS tasks can't find secrets
**Solution**:
```bash
# Verify secrets exist
aws secretsmanager list-secrets | grep cbaas

# Create missing secrets
bash infra/aws/04-setup-secrets.sh

# Check task definition references correct secret ARNs
aws ecs describe-task-definition --task-definition cbaas-backend-prod \
  --query 'taskDefinition.containerDefinitions[0].secrets'
```

### Issue: Secrets not accessible by ECS
**Symptoms**: "Access denied" in task logs
**Solution**:
```bash
# Verify ECS execution role has secretsmanager:GetSecretValue permission
source infra/aws/iam-info.env
aws iam get-role-policy --role-name $ECS_EXECUTION_ROLE_NAME

# Re-run IAM setup if needed
bash infra/aws/07-setup-iam.sh
```

---

## 🌐 DNS Issues

### Issue: Domain not resolving to CloudFront
**Symptoms**: Custom domain shows DNS error
**Solution**:
```bash
# Create CNAME record in Route 53 or your DNS provider
# Name: app.yourdomain.com
# Type: CNAME
# Value: d123456789.cloudfront.net (your CF_DOMAIN)
# TTL: 300

# Verify DNS
nslookup app.yourdomain.com
dig app.yourdomain.com
```

### Issue: ALB domain not resolving
**Symptoms**: Backend API unreachable via custom domain
**Solution**:
```bash
# Create CNAME record
# Name: api.yourdomain.com
# Type: CNAME
# Value: cbaas-alb-prod-xxxxx.ap-south-1.elb.amazonaws.com

# Update Django ALLOWED_HOSTS
# backend/config/environments/prod_aws.py
ALLOWED_HOSTS = ['api.yourdomain.com', ...]
```

---

## 🚨 Emergency Procedures

### Complete Service Outage
```bash
# 1. Check service status
aws ecs describe-services \
  --cluster cbaas-cluster-prod \
  --services cbaas-backend-service

# 2. Check CloudWatch Logs for errors
aws logs tail /ecs/cbaas/backend --follow

# 3. Rollback to previous task definition
PREVIOUS_VERSION=12  # Check: aws ecs list-task-definitions
aws ecs update-service \
  --cluster cbaas-cluster-prod \
  --service cbaas-backend-service \
  --task-definition cbaas-backend-prod:$PREVIOUS_VERSION

# 4. If database corruption, restore from snapshot
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier cbaas-postgres-restored \
  --db-snapshot-identifier auto-snapshot-name
```

### Accidental Resource Deletion
```bash
# S3 buckets (if versioning enabled)
aws s3api list-object-versions --bucket YOUR_BUCKET
aws s3api restore-object --bucket YOUR_BUCKET --key FILE --version-id VERSION_ID

# RDS (from automated backup)
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier cbaas-postgres-prod \
  --target-db-instance-identifier cbaas-postgres-restored \
  --restore-time 2024-01-15T12:00:00Z

# ECS services (redeploy)
bash infra/aws/10-setup-ecs.sh
```

---

## 📊 Monitoring & Debugging

### View Real-Time Logs
```bash
# Backend logs
aws logs tail /ecs/cbaas/backend --follow

# Worker logs
aws logs tail /ecs/cbaas/worker --follow

# Filter for errors
aws logs tail /ecs/cbaas/backend --follow --filter-pattern "ERROR"

# Search logs
aws logs filter-log-events \
  --log-group-name /ecs/cbaas/backend \
  --filter-pattern "database connection" \
  --start-time $(date -u -d '1 hour ago' +%s)000
```

### Get ECS Task Metrics
```bash
# List tasks
aws ecs list-tasks --cluster cbaas-cluster-prod --service-name cbaas-backend-service

# Describe task
aws ecs describe-tasks --cluster cbaas-cluster-prod --tasks TASK_ARN

# Get CPU/Memory metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=cbaas-backend-service \
  --start-time 2024-01-15T00:00:00Z \
  --end-time 2024-01-15T23:59:59Z \
  --period 3600 \
  --statistics Average
```

### Interactive Shell in ECS Task
```bash
# List running tasks
TASK_ARN=$(aws ecs list-tasks \
  --cluster cbaas-cluster-prod \
  --service-name cbaas-backend-service \
  --query 'taskArns[0]' \
  --output text)

# Execute command
aws ecs execute-command \
  --cluster cbaas-cluster-prod \
  --task $TASK_ARN \
  --container backend \
  --interactive \
  --command "/bin/bash"

# Inside container, you can:
# - python manage.py shell
# - python manage.py dbshell
# - Check environment variables
# - Test connections
```

---

## 📞 Getting Help

### Useful AWS Documentation
- [ECS Troubleshooting](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/troubleshooting.html)
- [RDS Troubleshooting](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_Troubleshooting.html)
- [CloudFront Troubleshooting](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/troubleshooting.html)

### AWS Support Commands
```bash
# Get support cases
aws support describe-cases

# Create support case (requires Business/Enterprise plan)
aws support create-case \
  --subject "ECS Task Failing" \
  --communication-body "Detailed description..." \
  --severity-code "low"
```

### Community Resources
- AWS Forums: https://forums.aws.amazon.com/
- Stack Overflow: Tag `amazon-web-services`
- AWS re:Post: https://repost.aws/

---

## 🔍 Debug Checklist

When something goes wrong:

1. **Check CloudWatch Logs** - Most errors appear here first
2. **Verify Security Groups** - 90% of connectivity issues
3. **Check IAM Permissions** - Execution vs Task role confusion
4. **Validate Environment Variables** - Missing or wrong values
5. **Review Task Definition** - Ensure image URI is correct
6. **Check Service Events** - ECS service event tab shows errors
7. **Verify Secrets Exist** - Secrets Manager
8. **Test Connections** - Use ECS Exec to debug from inside container
9. **Check Resource Limits** - CPU/memory/storage quotas
10. **Review Recent Changes** - What changed before the issue?

---

**Last Updated**: 2025-01-15  
**Maintained by**: DevOps Team
