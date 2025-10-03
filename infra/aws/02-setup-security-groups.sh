#!/bin/bash
# =============================================================================
# Setup Security Groups
# =============================================================================
# Creates security groups with least privilege:
# - ALB SG: Allows 80/443 from internet
# - ECS SG: Allows 8000 from ALB only
# - RDS SG: Allows 5432 from ECS only
# - Redis SG: Allows 6379 from ECS only
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/vpc-info.env"

print_info "=========================================="
print_info "Setting up Security Groups"
print_info "=========================================="

# -----------------------------------------------------------------------------
# ALB Security Group
# -----------------------------------------------------------------------------
print_info "Creating ALB Security Group..."
ALB_SG_ID=$(aws ec2 create-security-group \
    --group-name "${PROJECT_NAME}-alb-sg-${ENVIRONMENT}" \
    --description "Security group for Application Load Balancer" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-alb-sg-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-alb-sg-${ENVIRONMENT}" "Name=vpc-id,Values=$VPC_ID" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)

print_success "ALB Security Group ID: $ALB_SG_ID"

# Allow HTTP and HTTPS from internet
aws ec2 authorize-security-group-ingress \
    --group-id "$ALB_SG_ID" \
    --protocol tcp \
    --port 80 \
    --cidr 0.0.0.0/0 2>/dev/null || true

aws ec2 authorize-security-group-ingress \
    --group-id "$ALB_SG_ID" \
    --protocol tcp \
    --port 443 \
    --cidr 0.0.0.0/0 2>/dev/null || true

# -----------------------------------------------------------------------------
# ECS Security Group
# -----------------------------------------------------------------------------
print_info "Creating ECS Security Group..."
ECS_SG_ID=$(aws ec2 create-security-group \
    --group-name "${PROJECT_NAME}-ecs-sg-${ENVIRONMENT}" \
    --description "Security group for ECS tasks" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-ecs-sg-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-ecs-sg-${ENVIRONMENT}" "Name=vpc-id,Values=$VPC_ID" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)

print_success "ECS Security Group ID: $ECS_SG_ID"

# Allow port 8000 from ALB only
aws ec2 authorize-security-group-ingress \
    --group-id "$ECS_SG_ID" \
    --protocol tcp \
    --port 8000 \
    --source-group "$ALB_SG_ID" 2>/dev/null || true

# Allow all outbound traffic (required for pulling images, accessing RDS, etc.)
aws ec2 authorize-security-group-egress \
    --group-id "$ECS_SG_ID" \
    --protocol -1 \
    --cidr 0.0.0.0/0 2>/dev/null || true

# -----------------------------------------------------------------------------
# RDS Security Group
# -----------------------------------------------------------------------------
print_info "Creating RDS Security Group..."
RDS_SG_ID=$(aws ec2 create-security-group \
    --group-name "${PROJECT_NAME}-rds-sg-${ENVIRONMENT}" \
    --description "Security group for RDS PostgreSQL" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-rds-sg-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-rds-sg-${ENVIRONMENT}" "Name=vpc-id,Values=$VPC_ID" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)

print_success "RDS Security Group ID: $RDS_SG_ID"

# Allow PostgreSQL port from ECS only
aws ec2 authorize-security-group-ingress \
    --group-id "$RDS_SG_ID" \
    --protocol tcp \
    --port 5432 \
    --source-group "$ECS_SG_ID" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Redis Security Group
# -----------------------------------------------------------------------------
print_info "Creating Redis Security Group..."
REDIS_SG_ID=$(aws ec2 create-security-group \
    --group-name "${PROJECT_NAME}-redis-sg-${ENVIRONMENT}" \
    --description "Security group for ElastiCache Redis" \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=${PROJECT_NAME}-redis-sg-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'GroupId' \
    --output text 2>/dev/null || \
    aws ec2 describe-security-groups \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-redis-sg-${ENVIRONMENT}" "Name=vpc-id,Values=$VPC_ID" \
        --query 'SecurityGroups[0].GroupId' \
        --output text)

print_success "Redis Security Group ID: $REDIS_SG_ID"

# Allow Redis port from ECS only
aws ec2 authorize-security-group-ingress \
    --group-id "$REDIS_SG_ID" \
    --protocol tcp \
    --port 6379 \
    --source-group "$ECS_SG_ID" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Save Security Group Information
# -----------------------------------------------------------------------------
SG_INFO_FILE="${SCRIPT_DIR}/sg-info.env"
cat > "$SG_INFO_FILE" <<EOF
# Security Group IDs
export ALB_SG_ID="$ALB_SG_ID"
export ECS_SG_ID="$ECS_SG_ID"
export RDS_SG_ID="$RDS_SG_ID"
export REDIS_SG_ID="$REDIS_SG_ID"
EOF

print_success "Security group information saved to: $SG_INFO_FILE"

print_success "=========================================="
print_success "Security groups setup completed!"
print_success "=========================================="
