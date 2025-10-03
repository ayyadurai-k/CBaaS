#!/bin/bash
# =============================================================================
# Setup ECS Cluster and Services
# =============================================================================
# Creates:
# - ECS Cluster
# - CloudWatch Log Groups
# - ECS Task Definitions (backend and worker)
# - ECS Services (backend and worker)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/vpc-info.env"
source "${SCRIPT_DIR}/sg-info.env"
source "${SCRIPT_DIR}/alb-info.env"
source "${SCRIPT_DIR}/iam-info.env"
source "${SCRIPT_DIR}/ecr-info.env"
source "${SCRIPT_DIR}/rds-info.env"
source "${SCRIPT_DIR}/redis-info.env"
source "${SCRIPT_DIR}/secrets-info.env"
source "${SCRIPT_DIR}/s3-info.env"

print_info "=========================================="
print_info "Setting up ECS Cluster and Services"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create CloudWatch Log Groups
# -----------------------------------------------------------------------------
print_info "Creating CloudWatch log groups..."

aws logs create-log-group \
    --log-group-name "$LOG_GROUP_BACKEND" \
    --tags "Project=${PROJECT_NAME}" "Environment=${ENVIRONMENT}" "ManagedBy=aws-cli-automation" \
    2>/dev/null || print_warning "Backend log group already exists"

aws logs put-retention-policy \
    --log-group-name "$LOG_GROUP_BACKEND" \
    --retention-in-days "$LOG_RETENTION_DAYS" \
    2>/dev/null || true

aws logs create-log-group \
    --log-group-name "$LOG_GROUP_WORKER" \
    --tags "Project=${PROJECT_NAME}" "Environment=${ENVIRONMENT}" "ManagedBy=aws-cli-automation" \
    2>/dev/null || print_warning "Worker log group already exists"

aws logs put-retention-policy \
    --log-group-name "$LOG_GROUP_WORKER" \
    --retention-in-days "$LOG_RETENTION_DAYS" \
    2>/dev/null || true

print_success "CloudWatch log groups created"

# -----------------------------------------------------------------------------
# Create ECS Cluster
# -----------------------------------------------------------------------------
print_info "Creating ECS cluster..."

aws ecs create-cluster \
    --cluster-name "$ECS_CLUSTER_NAME" \
    --capacity-providers FARGATE FARGATE_SPOT \
    --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1 \
    --tags "key=Project,value=${PROJECT_NAME}" "key=Environment,value=${ENVIRONMENT}" "key=ManagedBy,value=aws-cli-automation" \
    2>/dev/null || print_warning "ECS cluster already exists"

print_success "ECS cluster created/exists: $ECS_CLUSTER_NAME"

# -----------------------------------------------------------------------------
# Create Backend Task Definition
# -----------------------------------------------------------------------------
print_info "Creating backend task definition..."

BACKEND_TASK_DEF=$(cat <<EOF
{
    "family": "${PROJECT_NAME}-backend-${ENVIRONMENT}",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "${ECS_TASK_CPU}",
    "memory": "${ECS_TASK_MEMORY}",
    "executionRoleArn": "${ECS_EXECUTION_ROLE_ARN}",
    "taskRoleArn": "${ECS_TASK_ROLE_ARN}",
    "containerDefinitions": [{
        "name": "backend",
        "image": "${BACKEND_ECR_URI}:latest",
        "essential": true,
        "portMappings": [{
            "containerPort": 8000,
            "protocol": "tcp"
        }],
        "environment": [
            {"name": "DJANGO_ENV", "value": "prod"},
            {"name": "AWS_REGION", "value": "${AWS_REGION}"},
            {"name": "AWS_STORAGE_BUCKET_NAME_STATIC", "value": "${S3_STATIC_BUCKET}"},
            {"name": "AWS_STORAGE_BUCKET_NAME_MEDIA", "value": "${S3_MEDIA_BUCKET}"},
            {"name": "DB_HOST", "value": "${RDS_ENDPOINT}"},
            {"name": "DB_PORT", "value": "5432"},
            {"name": "DB_NAME", "value": "${RDS_DB_NAME}"},
            {"name": "REDIS_HOST", "value": "${REDIS_ENDPOINT}"},
            {"name": "REDIS_PORT", "value": "${REDIS_PORT}"}
        ],
        "secrets": [
            {"name": "SECRET_KEY", "valueFrom": "${SECRET_DJANGO_SECRET}"},
            {"name": "DB_PASSWORD", "valueFrom": "${SECRET_DB_CREDENTIALS}:password::"},
            {"name": "DB_USER", "valueFrom": "${SECRET_DB_CREDENTIALS}:username::"},
            {"name": "REDIS_PASSWORD", "valueFrom": "${SECRET_REDIS_AUTH}"}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${LOG_GROUP_BACKEND}",
                "awslogs-region": "${AWS_REGION}",
                "awslogs-stream-prefix": "backend"
            }
        },
        "healthCheck": {
            "command": ["CMD-SHELL", "curl -f http://localhost:8000/healthz || exit 1"],
            "interval": 30,
            "timeout": 5,
            "retries": 3,
            "startPeriod": 60
        }
    }]
}
EOF
)

echo "$BACKEND_TASK_DEF" > "${SCRIPT_DIR}/backend-task-definition.json"

BACKEND_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json "$BACKEND_TASK_DEF" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

print_success "Backend task definition registered: $BACKEND_TASK_DEF_ARN"

# -----------------------------------------------------------------------------
# Create Worker Task Definition
# -----------------------------------------------------------------------------
print_info "Creating worker task definition..."

WORKER_TASK_DEF=$(cat <<EOF
{
    "family": "${PROJECT_NAME}-worker-${ENVIRONMENT}",
    "networkMode": "awsvpc",
    "requiresCompatibilities": ["FARGATE"],
    "cpu": "${ECS_TASK_CPU}",
    "memory": "${ECS_TASK_MEMORY}",
    "executionRoleArn": "${ECS_EXECUTION_ROLE_ARN}",
    "taskRoleArn": "${ECS_TASK_ROLE_ARN}",
    "containerDefinitions": [{
        "name": "worker",
        "image": "${BACKEND_ECR_URI}:latest",
        "essential": true,
        "command": ["celery", "-A", "config", "worker", "-l", "info"],
        "environment": [
            {"name": "DJANGO_ENV", "value": "prod"},
            {"name": "AWS_REGION", "value": "${AWS_REGION}"},
            {"name": "AWS_STORAGE_BUCKET_NAME_STATIC", "value": "${S3_STATIC_BUCKET}"},
            {"name": "AWS_STORAGE_BUCKET_NAME_MEDIA", "value": "${S3_MEDIA_BUCKET}"},
            {"name": "DB_HOST", "value": "${RDS_ENDPOINT}"},
            {"name": "DB_PORT", "value": "5432"},
            {"name": "DB_NAME", "value": "${RDS_DB_NAME}"},
            {"name": "REDIS_HOST", "value": "${REDIS_ENDPOINT}"},
            {"name": "REDIS_PORT", "value": "${REDIS_PORT}"}
        ],
        "secrets": [
            {"name": "SECRET_KEY", "valueFrom": "${SECRET_DJANGO_SECRET}"},
            {"name": "DB_PASSWORD", "valueFrom": "${SECRET_DB_CREDENTIALS}:password::"},
            {"name": "DB_USER", "valueFrom": "${SECRET_DB_CREDENTIALS}:username::"},
            {"name": "REDIS_PASSWORD", "valueFrom": "${SECRET_REDIS_AUTH}"}
        ],
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": "${LOG_GROUP_WORKER}",
                "awslogs-region": "${AWS_REGION}",
                "awslogs-stream-prefix": "worker"
            }
        }
    }]
}
EOF
)

echo "$WORKER_TASK_DEF" > "${SCRIPT_DIR}/worker-task-definition.json"

WORKER_TASK_DEF_ARN=$(aws ecs register-task-definition \
    --cli-input-json "$WORKER_TASK_DEF" \
    --query 'taskDefinition.taskDefinitionArn' \
    --output text)

print_success "Worker task definition registered: $WORKER_TASK_DEF_ARN"

# -----------------------------------------------------------------------------
# Create Backend ECS Service
# -----------------------------------------------------------------------------
print_info "Creating backend ECS service..."

aws ecs create-service \
    --cluster "$ECS_CLUSTER_NAME" \
    --service-name "$ECS_BACKEND_SERVICE" \
    --task-definition "${PROJECT_NAME}-backend-${ENVIRONMENT}" \
    --desired-count "$ECS_BACKEND_DESIRED_COUNT" \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PRIVATE_SUBNET_1_ID},${PRIVATE_SUBNET_2_ID}],
        securityGroups=[${ECS_SG_ID}],
        assignPublicIp=DISABLED
    }" \
    --load-balancers "targetGroupArn=${TARGET_GROUP_ARN},containerName=backend,containerPort=8000" \
    --health-check-grace-period-seconds 60 \
    --deployment-configuration "maximumPercent=200,minimumHealthyPercent=100,deploymentCircuitBreaker={enable=true,rollback=true}" \
    --enable-execute-command \
    --tags "key=Project,value=${PROJECT_NAME}" "key=Environment,value=${ENVIRONMENT}" "key=ManagedBy,value=aws-cli-automation" \
    2>/dev/null || print_warning "Backend service already exists or creation in progress"

print_success "Backend ECS service created/exists"

# -----------------------------------------------------------------------------
# Create Worker ECS Service
# -----------------------------------------------------------------------------
print_info "Creating worker ECS service..."

aws ecs create-service \
    --cluster "$ECS_CLUSTER_NAME" \
    --service-name "$ECS_WORKER_SERVICE" \
    --task-definition "${PROJECT_NAME}-worker-${ENVIRONMENT}" \
    --desired-count "$ECS_WORKER_DESIRED_COUNT" \
    --launch-type FARGATE \
    --platform-version LATEST \
    --network-configuration "awsvpcConfiguration={
        subnets=[${PRIVATE_SUBNET_1_ID},${PRIVATE_SUBNET_2_ID}],
        securityGroups=[${ECS_SG_ID}],
        assignPublicIp=DISABLED
    }" \
    --deployment-configuration "maximumPercent=200,minimumHealthyPercent=0,deploymentCircuitBreaker={enable=true,rollback=true}" \
    --enable-execute-command \
    --tags "key=Project,value=${PROJECT_NAME}" "key=Environment,value=${ENVIRONMENT}" "key=ManagedBy,value=aws-cli-automation" \
    2>/dev/null || print_warning "Worker service already exists or creation in progress"

print_success "Worker ECS service created/exists"

# -----------------------------------------------------------------------------
# Save ECS Information
# -----------------------------------------------------------------------------
ECS_INFO_FILE="${SCRIPT_DIR}/ecs-info.env"
cat > "$ECS_INFO_FILE" <<EOF
# ECS Cluster and Services Information
export ECS_CLUSTER_NAME="$ECS_CLUSTER_NAME"
export ECS_BACKEND_SERVICE="$ECS_BACKEND_SERVICE"
export ECS_WORKER_SERVICE="$ECS_WORKER_SERVICE"
export BACKEND_TASK_DEF_ARN="$BACKEND_TASK_DEF_ARN"
export WORKER_TASK_DEF_ARN="$WORKER_TASK_DEF_ARN"
export LOG_GROUP_BACKEND="$LOG_GROUP_BACKEND"
export LOG_GROUP_WORKER="$LOG_GROUP_WORKER"
EOF

print_success "ECS information saved to: $ECS_INFO_FILE"

print_success "=========================================="
print_success "ECS setup completed successfully!"
print_success "=========================================="
print_info "Waiting for services to stabilize (this may take a few minutes)..."
print_info "Monitor at: https://console.aws.amazon.com/ecs/v2/clusters/${ECS_CLUSTER_NAME}/services"
