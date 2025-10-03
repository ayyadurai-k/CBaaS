#!/bin/bash
# =============================================================================
# AWS Infrastructure Configuration
# =============================================================================
# This file contains all configuration variables used across deployment scripts.
# Modify these values to match your environment.
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# General Configuration
# -----------------------------------------------------------------------------
export AWS_REGION="${AWS_REGION:-ap-south-1}"
export AWS_ACCOUNT_ID="${AWS_ACCOUNT_ID:-$(aws sts get-caller-identity --query Account --output text)}"
export PROJECT_NAME="${PROJECT_NAME:-cbaas}"
export ENVIRONMENT="${ENVIRONMENT:-prod}"

# -----------------------------------------------------------------------------
# VPC Configuration
# -----------------------------------------------------------------------------
export VPC_CIDR="10.0.0.0/16"
export PUBLIC_SUBNET_1_CIDR="10.0.1.0/24"
export PUBLIC_SUBNET_2_CIDR="10.0.2.0/24"
export PRIVATE_SUBNET_1_CIDR="10.0.10.0/24"
export PRIVATE_SUBNET_2_CIDR="10.0.20.0/24"
export AVAILABILITY_ZONE_1="${AWS_REGION}a"
export AVAILABILITY_ZONE_2="${AWS_REGION}b"

# -----------------------------------------------------------------------------
# S3 Bucket Names
# -----------------------------------------------------------------------------
export S3_FRONTEND_BUCKET="${PROJECT_NAME}-frontend-origin-${ENVIRONMENT}"
export S3_STATIC_BUCKET="${PROJECT_NAME}-django-static-${ENVIRONMENT}"
export S3_MEDIA_BUCKET="${PROJECT_NAME}-django-media-${ENVIRONMENT}"

# -----------------------------------------------------------------------------
# CloudFront Configuration
# -----------------------------------------------------------------------------
export CLOUDFRONT_PRICE_CLASS="PriceClass_All"
export CLOUDFRONT_CERT_ARN="${CLOUDFRONT_CERT_ARN:-}"  # Set via environment or manually

# -----------------------------------------------------------------------------
# ECR Configuration
# -----------------------------------------------------------------------------
export ECR_BACKEND_REPO="${PROJECT_NAME}-backend"
export ECR_WORKER_REPO="${PROJECT_NAME}-worker"

# -----------------------------------------------------------------------------
# ECS Configuration
# -----------------------------------------------------------------------------
export ECS_CLUSTER_NAME="${PROJECT_NAME}-cluster-${ENVIRONMENT}"
export ECS_BACKEND_SERVICE="${PROJECT_NAME}-backend-service"
export ECS_WORKER_SERVICE="${PROJECT_NAME}-worker-service"
export ECS_TASK_CPU="512"       # 0.5 vCPU
export ECS_TASK_MEMORY="1024"   # 1 GB
export ECS_BACKEND_DESIRED_COUNT="2"
export ECS_WORKER_DESIRED_COUNT="1"

# -----------------------------------------------------------------------------
# ALB Configuration
# -----------------------------------------------------------------------------
export ALB_NAME="${PROJECT_NAME}-alb-${ENVIRONMENT}"
export ALB_TARGET_GROUP="${PROJECT_NAME}-backend-tg"
export ALB_CERT_ARN="${ALB_CERT_ARN:-}"  # Set via environment or manually

# -----------------------------------------------------------------------------
# RDS Configuration
# -----------------------------------------------------------------------------
export RDS_INSTANCE_ID="${PROJECT_NAME}-postgres-${ENVIRONMENT}"
export RDS_INSTANCE_CLASS="db.t3.micro"
export RDS_ENGINE="postgres"
export RDS_ENGINE_VERSION="16.1"
export RDS_ALLOCATED_STORAGE="20"
export RDS_DB_NAME="cbaas_db"
export RDS_MASTER_USERNAME="cbaas_admin"

# -----------------------------------------------------------------------------
# ElastiCache Configuration
# -----------------------------------------------------------------------------
export REDIS_CLUSTER_ID="${PROJECT_NAME}-redis-${ENVIRONMENT}"
export REDIS_NODE_TYPE="cache.t3.micro"
export REDIS_ENGINE_VERSION="7.1"
export REDIS_NUM_CACHE_NODES="1"

# -----------------------------------------------------------------------------
# Secrets Manager
# -----------------------------------------------------------------------------
export SECRET_DJANGO_SECRET="${PROJECT_NAME}/${ENVIRONMENT}/django-secret"
export SECRET_DB_CREDENTIALS="${PROJECT_NAME}/${ENVIRONMENT}/db-credentials"
export SECRET_REDIS_AUTH="${PROJECT_NAME}/${ENVIRONMENT}/redis-auth"

# -----------------------------------------------------------------------------
# WAF Configuration
# -----------------------------------------------------------------------------
export WAF_WEB_ACL_NAME="${PROJECT_NAME}-waf-${ENVIRONMENT}"

# -----------------------------------------------------------------------------
# Route 53 Configuration
# -----------------------------------------------------------------------------
export DOMAIN_NAME="${DOMAIN_NAME:-}"  # e.g., example.com
export FRONTEND_DOMAIN="${FRONTEND_DOMAIN:-app.${DOMAIN_NAME}}"
export BACKEND_DOMAIN="${BACKEND_DOMAIN:-api.${DOMAIN_NAME}}"

# -----------------------------------------------------------------------------
# CloudWatch Logs
# -----------------------------------------------------------------------------
export LOG_GROUP_BACKEND="/ecs/${PROJECT_NAME}/backend"
export LOG_GROUP_WORKER="/ecs/${PROJECT_NAME}/worker"
export LOG_RETENTION_DAYS="30"

# -----------------------------------------------------------------------------
# Tags
# -----------------------------------------------------------------------------
export TAG_PROJECT="Project=${PROJECT_NAME}"
export TAG_ENVIRONMENT="Environment=${ENVIRONMENT}"
export TAG_MANAGED_BY="ManagedBy=aws-cli-automation"

# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------

# Print colored output
print_info() {
    echo -e "\e[34m[INFO]\e[0m $1"
}

print_success() {
    echo -e "\e[32m[SUCCESS]\e[0m $1"
}

print_error() {
    echo -e "\e[31m[ERROR]\e[0m $1"
}

print_warning() {
    echo -e "\e[33m[WARNING]\e[0m $1"
}

# Check if AWS CLI is installed
check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        print_error "AWS CLI is not installed. Please install it first."
        exit 1
    fi
    print_success "AWS CLI is installed"
}

# Check if Docker is installed
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install it first."
        exit 1
    fi
    print_success "Docker is installed"
}

# Validate AWS credentials
validate_aws_credentials() {
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials are not configured properly"
        exit 1
    fi
    print_success "AWS credentials are valid"
}

# Check if resource exists by tag
resource_exists_by_tag() {
    local resource_type=$1
    local tag_key=$2
    local tag_value=$3
    
    local result=$(aws resourcegroupstaggingapi get-resources \
        --resource-type-filters "$resource_type" \
        --tag-filters "Key=${tag_key},Values=${tag_value}" \
        --query 'ResourceTagMappingList[0].ResourceARN' \
        --output text 2>/dev/null)
    
    if [ "$result" != "None" ] && [ -n "$result" ]; then
        echo "$result"
        return 0
    else
        return 1
    fi
}

# Generate random password
generate_password() {
    openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
}

# Export all functions
export -f print_info
export -f print_success
export -f print_error
export -f print_warning
export -f check_aws_cli
export -f check_docker
export -f validate_aws_credentials
export -f resource_exists_by_tag
export -f generate_password
