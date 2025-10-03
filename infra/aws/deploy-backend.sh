#!/bin/bash
# =============================================================================
# Deploy Backend to ECS
# =============================================================================
# This script:
# 1. Builds Django Docker image
# 2. Pushes to ECR
# 3. Updates ECS task definition
# 4. Updates ECS services (backend and worker)
# 5. Runs database migrations
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
BACKEND_DIR="${PROJECT_ROOT}/backend"

source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/ecr-info.env"
source "${SCRIPT_DIR}/ecs-info.env"
source "${SCRIPT_DIR}/vpc-info.env"
source "${SCRIPT_DIR}/sg-info.env"

print_info "=========================================="
print_info "Deploying Backend to ECS"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Validate Prerequisites
# -----------------------------------------------------------------------------
check_aws_cli
check_docker
validate_aws_credentials

if [ ! -f "$BACKEND_DIR/Dockerfile.prod" ]; then
    print_error "Dockerfile.prod not found in backend directory"
    exit 1
fi

# -----------------------------------------------------------------------------
# Login to ECR
# -----------------------------------------------------------------------------
print_info "Logging in to ECR..."

aws ecr get-login-password --region "$AWS_REGION" | \
    docker login --username AWS --password-stdin "$ECR_REGISTRY"

print_success "Logged in to ECR"

# -----------------------------------------------------------------------------
# Build Docker Image
# -----------------------------------------------------------------------------
print_info "Building Docker image..."

cd "$BACKEND_DIR"

IMAGE_TAG="${BACKEND_ECR_URI}:$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')"
LATEST_TAG="${BACKEND_ECR_URI}:latest"

docker build \
    -f Dockerfile.prod \
    -t "$IMAGE_TAG" \
    -t "$LATEST_TAG" \
    .

print_success "Docker image built: $IMAGE_TAG"

# -----------------------------------------------------------------------------
# Push to ECR
# -----------------------------------------------------------------------------
print_info "Pushing image to ECR..."

docker push "$IMAGE_TAG"
docker push "$LATEST_TAG"

print_success "Image pushed to ECR"

# -----------------------------------------------------------------------------
# Update Task Definitions
# -----------------------------------------------------------------------------
print_info "Updating ECS task definitions..."

# Register new backend task definition
BACKEND_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://"${SCRIPT_DIR}/backend-task-definition.json" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

print_success "Backend task definition: $BACKEND_TASK_DEF_ARN"

# Register new worker task definition
WORKER_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json file://"${SCRIPT_DIR}/worker-task-definition.json" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

print_success "Worker task definition: $WORKER_TASK_DEF_ARN"

# -----------------------------------------------------------------------------
# Run Database Migrations
# -----------------------------------------------------------------------------
print_info "Running database migrations..."

# Run migrations as a one-off task
MIGRATION_TASK_ARN=$(aws ecs run-task \
    --cluster "$ECS_CLUSTER_NAME" \
    --task-definition "${PROJECT_NAME}-backend-${ENVIRONMENT}" \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PRIVATE_SUBNET_1_ID}],
        securityGroups=[${ECS_SG_ID}],
        assignPublicIp=DISABLED
    }" \
    --overrides '{
        "containerOverrides": [{
            "name": "backend",
            "command": ["python", "manage.py", "migrate", "--noinput"]
        }]
    }' \
    --query 'tasks[0].taskArn' \
    --output text)

print_info "Migration task started: $MIGRATION_TASK_ARN"
print_info "Waiting for migrations to complete..."

# Wait for migration task to complete
aws ecs wait tasks-stopped \
    --cluster "$ECS_CLUSTER_NAME" \
    --tasks "$MIGRATION_TASK_ARN"

# Check migration task exit code
MIGRATION_EXIT_CODE=$(aws ecs describe-tasks \
    --cluster "$ECS_CLUSTER_NAME" \
    --tasks "$MIGRATION_TASK_ARN" \
    --query 'tasks[0].containers[0].exitCode' \
    --output text)

if [ "$MIGRATION_EXIT_CODE" != "0" ]; then
    print_error "Migrations failed with exit code: $MIGRATION_EXIT_CODE"
    print_error "Check CloudWatch logs: $LOG_GROUP_BACKEND"
    exit 1
fi

print_success "Migrations completed successfully"

# -----------------------------------------------------------------------------
# Collect Static Files
# -----------------------------------------------------------------------------
print_info "Collecting static files to S3..."

COLLECTSTATIC_TASK_ARN=$(aws ecs run-task \
    --cluster "$ECS_CLUSTER_NAME" \
    --task-definition "${PROJECT_NAME}-backend-${ENVIRONMENT}" \
    --launch-type FARGATE \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PRIVATE_SUBNET_1_ID}],
        securityGroups=[${ECS_SG_ID}],
        assignPublicIp=DISABLED
    }" \
    --overrides '{
        "containerOverrides": [{
            "name": "backend",
            "command": ["python", "manage.py", "collectstatic", "--noinput"]
        }]
    }' \
    --query 'tasks[0].taskArn' \
    --output text)

print_info "Collectstatic task started: $COLLECTSTATIC_TASK_ARN"

# Wait for collectstatic to complete
aws ecs wait tasks-stopped \
    --cluster "$ECS_CLUSTER_NAME" \
    --tasks "$COLLECTSTATIC_TASK_ARN"

print_success "Static files collected"

# -----------------------------------------------------------------------------
# Update ECS Services
# -----------------------------------------------------------------------------
print_info "Updating backend ECS service..."

aws ecs update-service \
    --cluster "$ECS_CLUSTER_NAME" \
    --service "$ECS_BACKEND_SERVICE" \
    --task-definition "${PROJECT_NAME}-backend-${ENVIRONMENT}" \
    --force-new-deployment \
    --query 'service.serviceName' \
    --output text

print_success "Backend service update initiated"

print_info "Updating worker ECS service..."

aws ecs update-service \
    --cluster "$ECS_CLUSTER_NAME" \
    --service "$ECS_WORKER_SERVICE" \
    --task-definition "${PROJECT_NAME}-worker-${ENVIRONMENT}" \
    --force-new-deployment \
    --query 'service.serviceName' \
    --output text

print_success "Worker service update initiated"

# -----------------------------------------------------------------------------
# Wait for Services to Stabilize
# -----------------------------------------------------------------------------
print_info "Waiting for services to stabilize..."
print_info "This may take several minutes..."

aws ecs wait services-stable \
    --cluster "$ECS_CLUSTER_NAME" \
    --services "$ECS_BACKEND_SERVICE" "$ECS_WORKER_SERVICE" 2>/dev/null || \
    print_warning "Service stabilization check timed out - verify manually"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
print_success "=========================================="
print_success "Backend deployment completed!"
print_success "=========================================="

# Get ALB DNS if available
if [ -f "${SCRIPT_DIR}/alb-info.env" ]; then
    source "${SCRIPT_DIR}/alb-info.env"
    print_info "Backend URL: http://${ALB_DNS}"
fi

print_info "Monitor deployment:"
print_info "  ECS Console: https://console.aws.amazon.com/ecs/v2/clusters/${ECS_CLUSTER_NAME}/services"
print_info "  CloudWatch Logs: https://console.aws.amazon.com/cloudwatch/home?region=${AWS_REGION}#logsV2:log-groups/log-group/${LOG_GROUP_BACKEND}"

cd "$PROJECT_ROOT"
