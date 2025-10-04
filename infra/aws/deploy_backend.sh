#!/bin/bash

##############################################################################
# Manual Backend Deployment Script for CBaaS Django on AWS ECS
# 
# This script:
# 1. Builds and pushes Docker image to ECR
# 2. Updates ECS task definition with new image
# 3. Updates ECS service to use new task definition
# 4. Waits for deployment to complete
# 5. Verifies service health
#
# Usage: ./deploy_backend.sh <project-name> <aws-account-id> [image-tag]
# Example: ./deploy_backend.sh cbaas 577897067437 v1.0.0
##############################################################################

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Validate inputs
if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    log_error "Usage: $0 <project-name> <aws-account-id> [image-tag]"
    log_error "Example: $0 cbaas 577897067437 v1.0.0"
    exit 1
fi

PROJECT_NAME=$1
AWS_ACCOUNT_ID=$2
IMAGE_TAG=${3:-"$(date +%Y%m%d-%H%M%S)"}
AWS_REGION="ap-south-1"
ECR_REPO="${PROJECT_NAME}-backend"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
SERVICE_NAME="${PROJECT_NAME}-backend-service"
TASK_FAMILY="${PROJECT_NAME}-backend-task"

# Verify we're in the right directory
if [ ! -f "backend/Dockerfile.backend" ]; then
    log_error "Please run this script from the project root directory"
    log_error "Expected: backend/Dockerfile.backend"
    exit 1
fi

# Verify AWS CLI and Docker
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install it first."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install it first."
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"
FULL_IMAGE_URI="${ECR_URI}:${IMAGE_TAG}"

log_info "Starting backend deployment..."
log_info "Project: $PROJECT_NAME"
log_info "Image: $FULL_IMAGE_URI"
log_info "Cluster: $CLUSTER_NAME"
log_info "Service: $SERVICE_NAME"

# Step 1: Login to ECR
log_step "Logging into ECR..."
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "$ECR_URI"

# Step 2: Build Docker image
log_step "Building Docker image..."
docker build -f backend/Dockerfile.backend -t "$FULL_IMAGE_URI" backend/

# Step 3: Push image to ECR
log_step "Pushing image to ECR..."
docker push "$FULL_IMAGE_URI"
log_info "Image pushed: $FULL_IMAGE_URI"

# Step 4: Get current task definition
log_step "Updating ECS task definition..."

# Get the current task definition
CURRENT_TASK_DEF=$(aws ecs describe-task-definition \
    --task-definition "$TASK_FAMILY" \
    --query 'taskDefinition' \
    --output json 2>/dev/null || echo "null")

if [ "$CURRENT_TASK_DEF" = "null" ]; then
    log_error "Task definition $TASK_FAMILY not found. Please run setup-aws-backend.sh first."
    exit 1
fi

# Create new task definition with updated image using AWS CLI
# Get current revision to increment
CURRENT_REVISION=$(aws ecs describe-task-definition \
    --task-definition "$TASK_FAMILY" \
    --query 'taskDefinition.revision' \
    --output text)

# Create a temporary task definition file with updated image
cat > temp-task-def.json <<EOF
{
  "family": "$TASK_FAMILY",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::577897067437:role/cbaas-task-execution-role",
  "taskRoleArn": "arn:aws:iam::577897067437:role/cbaas-task-execution-role",
  "containerDefinitions": [
    {
      "name": "cbaas-backend",
      "image": "$FULL_IMAGE_URI",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "essential": true,
      "secrets": [
        {
          "name": "DJANGO_SECRET_KEY",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:577897067437:secret:cbaas/backend/env:DJANGO_SECRET_KEY::"
        },
        {
          "name": "DEBUG",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:577897067437:secret:cbaas/backend/env:DEBUG::"
        },
        {
          "name": "ALLOWED_HOSTS",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:577897067437:secret:cbaas/backend/env:ALLOWED_HOSTS::"
        },
        {
          "name": "DATABASE_URL",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:577897067437:secret:cbaas/backend/env:DATABASE_URL::"
        },
        {
          "name": "CORS_ALLOWED_ORIGINS",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:577897067437:secret:cbaas/backend/env:CORS_ALLOWED_ORIGINS::"
        },
        {
          "name": "CORS_ALLOW_CREDENTIALS",
          "valueFrom": "arn:aws:secretsmanager:${AWS_REGION}:577897067437:secret:cbaas/backend/env:CORS_ALLOW_CREDENTIALS::"
        }
      ],
      "environment": [
        {
          "name": "DJANGO_ENV",
          "value": "prod"
        },
        {
          "name": "AWS_DEFAULT_REGION",
          "value": "$AWS_REGION"
        }
      ],
      "healthCheck": {
        "command": [
          "CMD-SHELL",
          "curl -f http://localhost:8000/api/healthz || exit 1"
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 60
      }
    }
  ]
}
EOF

# Register new task definition
NEW_REVISION=$(aws ecs register-task-definition \
    --cli-input-json file://temp-task-def.json \
    --query 'taskDefinition.revision' \
    --output text)

# Clean up temporary file
rm -f temp-task-def.json

log_info "New task definition registered: ${TASK_FAMILY}:${NEW_REVISION}"

# Step 5: Check if service exists, create if not
log_step "Updating ECS service..."

if aws ecs describe-services --cluster "$CLUSTER_NAME" --services "$SERVICE_NAME" --query 'services[0].serviceName' --output text 2>/dev/null | grep -q "$SERVICE_NAME"; then
    log_info "Service exists, updating..."
    
    # Update existing service
    aws ecs update-service \
        --cluster "$CLUSTER_NAME" \
        --service "$SERVICE_NAME" \
        --task-definition "${TASK_FAMILY}:${NEW_REVISION}" \
        --force-new-deployment > /dev/null
    
    log_info "Service update initiated"
else
    log_info "Service doesn't exist, creating..."
    
    # Get network configuration from setup
    VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text)
    SUBNET_ID_1=$(echo $SUBNET_IDS | cut -d' ' -f1)
    SUBNET_ID_2=$(echo $SUBNET_IDS | cut -d' ' -f2)
    ECS_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=${PROJECT_NAME}-ecs-sg" --query 'SecurityGroups[0].GroupId' --output text)
    TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups --names "${PROJECT_NAME}-tg" --query 'TargetGroups[0].TargetGroupArn' --output text)
    
    if [ -z "$SUBNET_ID_2" ]; then
        SUBNET_ID_2="$SUBNET_ID_1"
    fi
    
    # Create service
    aws ecs create-service \
        --cluster "$CLUSTER_NAME" \
        --service-name "$SERVICE_NAME" \
        --task-definition "${TASK_FAMILY}:${NEW_REVISION}" \
        --desired-count 1 \
        --launch-type FARGATE \
        --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID_1,$SUBNET_ID_2],securityGroups=[$ECS_SG_ID],assignPublicIp=ENABLED}" \
        --load-balancers "targetGroupArn=$TARGET_GROUP_ARN,containerName=${PROJECT_NAME}-backend,containerPort=8000" \
        --enable-execute-command > /dev/null
    
    log_info "Service created"
fi

# Step 6: Wait for deployment to stabilize
log_step "Waiting for deployment to complete..."
log_info "This may take 2-5 minutes..."

aws ecs wait services-stable \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME"

# Step 7: Get service status
log_step "Checking deployment status..."

SERVICE_STATUS=$(aws ecs describe-services \
    --cluster "$CLUSTER_NAME" \
    --services "$SERVICE_NAME" \
    --query 'services[0].{running:runningCount,desired:desiredCount,pending:pendingCount,status:status}' \
    --output table)

echo "$SERVICE_STATUS"

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --names "${PROJECT_NAME}-alb" \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

# Step 8: Verify health
log_step "Verifying service health..."

# Wait a bit for ALB to register targets
sleep 30

# Check target group health
TG_HEALTH=$(aws elbv2 describe-target-health \
    --target-group-arn "$(aws elbv2 describe-target-groups --names "${PROJECT_NAME}-tg" --query 'TargetGroups[0].TargetGroupArn' --output text)" \
    --query 'TargetHealthDescriptions[*].{Target:Target.Id,Health:TargetHealth.State}' \
    --output table 2>/dev/null || echo "No targets registered yet")

echo "Target Group Health:"
echo "$TG_HEALTH"

# Test endpoint
log_info "Testing backend endpoint..."
if curl -s -o /dev/null -w "%{http_code}" "http://${ALB_DNS}/api/healthz" | grep -q "200"; then
    log_info "✅ Backend is responding!"
else
    log_warn "⚠️  Backend might still be starting up. Check logs if issues persist."
fi

echo ""
echo "======================================================================"
log_info "🚀 Backend Deployment Complete!"
echo "======================================================================"
echo ""
echo "📋 Deployment Summary:"
echo "  Image: $FULL_IMAGE_URI"
echo "  Task Definition: ${TASK_FAMILY}:${NEW_REVISION}"
echo "  Service: $SERVICE_NAME"
echo "  Cluster: $CLUSTER_NAME"
echo ""
echo "🌐 Backend URL: http://${ALB_DNS}"
echo "🔍 Admin Panel: http://${ALB_DNS}/admin/"
echo ""
echo "🔧 Useful Commands:"
echo "  Service status: aws ecs describe-services --cluster $CLUSTER_NAME --services $SERVICE_NAME"
echo "  Task details: aws ecs describe-tasks --cluster $CLUSTER_NAME --tasks \$(aws ecs list-tasks --cluster $CLUSTER_NAME --service-name $SERVICE_NAME --query 'taskArns[0]' --output text)"
echo "  Container logs: aws ecs execute-command --cluster $CLUSTER_NAME --task <task-arn> --container ${PROJECT_NAME}-backend --interactive --command '/bin/bash'"
echo "======================================================================"

exit 0