#!/bin/bash
# =============================================================================
# Setup ECR Repositories
# =============================================================================
# Creates ECR repositories for:
# - Backend (Django + Gunicorn)
# - Worker (Celery worker - uses same image as backend)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

print_info "=========================================="
print_info "Setting up ECR Repositories"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create Backend ECR Repository
# -----------------------------------------------------------------------------
print_info "Creating ECR repository for backend..."

aws ecr create-repository \
    --repository-name "$ECR_BACKEND_REPO" \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256 \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || print_warning "ECR repository $ECR_BACKEND_REPO already exists"

# Set lifecycle policy to keep only last 10 images
LIFECYCLE_POLICY=$(cat <<EOF
{
    "rules": [{
        "rulePriority": 1,
        "description": "Keep only last 10 images",
        "selection": {
            "tagStatus": "any",
            "countType": "imageCountMoreThan",
            "countNumber": 10
        },
        "action": {
            "type": "expire"
        }
    }]
}
EOF
)

aws ecr put-lifecycle-policy \
    --repository-name "$ECR_BACKEND_REPO" \
    --lifecycle-policy-text "$LIFECYCLE_POLICY" \
    2>/dev/null || true

BACKEND_ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_BACKEND_REPO}"
print_success "Backend ECR URI: $BACKEND_ECR_URI"

# -----------------------------------------------------------------------------
# Note: Worker uses same backend image, no separate repo needed
# -----------------------------------------------------------------------------
print_info "Worker will use the same backend image (different CMD in task definition)"

# -----------------------------------------------------------------------------
# Save ECR Information
# -----------------------------------------------------------------------------
ECR_INFO_FILE="${SCRIPT_DIR}/ecr-info.env"
cat > "$ECR_INFO_FILE" <<EOF
# ECR Repository Information
export ECR_BACKEND_REPO="$ECR_BACKEND_REPO"
export BACKEND_ECR_URI="$BACKEND_ECR_URI"
export ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
EOF

print_success "ECR information saved to: $ECR_INFO_FILE"

print_success "=========================================="
print_success "ECR repositories setup completed!"
print_success "=========================================="
print_info "Login to ECR with: aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
