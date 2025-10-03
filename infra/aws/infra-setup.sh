#!/bin/bash
# =============================================================================
# Main Infrastructure Setup Script
# =============================================================================
# This master script orchestrates the complete AWS infrastructure setup.
# Run this once to provision all resources.
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

print_info "=========================================="
print_info "CBaaS AWS Infrastructure Setup"
print_info "=========================================="
print_info "Project: $PROJECT_NAME"
print_info "Environment: $ENVIRONMENT"
print_info "Region: $AWS_REGION"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Validate Prerequisites
# -----------------------------------------------------------------------------
print_info "Validating prerequisites..."
check_aws_cli

if ! validate_aws_credentials 2>/dev/null; then
    print_error "AWS credentials not configured!"
    echo ""
    print_info "Please configure AWS credentials:"
    print_info "  1. Run: aws configure"
    print_info "  2. Enter your AWS Access Key ID"
    print_info "  3. Enter your AWS Secret Access Key"
    print_info "  4. Enter region: ${AWS_REGION}"
    print_info "  5. Enter output format: json"
    echo ""
    print_info "Don't have AWS credentials? Create them:"
    print_info "  1. Login to AWS Console: https://console.aws.amazon.com/"
    print_info "  2. Go to IAM → Users → Your User → Security Credentials"
    print_info "  3. Create Access Key → CLI"
    print_info "  4. Copy the Access Key ID and Secret Access Key"
    echo ""
    print_info "Or run our helper script:"
    print_info "  bash setup-aws-credentials.sh"
    echo ""
    print_warning "Run this script again after configuring credentials"
    exit 1
fi

print_success "Prerequisites validated"

# Display AWS account info
AWS_ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)
AWS_USER=$(aws sts get-caller-identity --query 'Arn' --output text | cut -d'/' -f2)
print_info "AWS Account: $AWS_ACCOUNT"
print_info "AWS User: $AWS_USER"
print_info "AWS Region: $AWS_REGION"
echo ""

# Confirm with user
read -p "This will create AWS resources that may incur costs. Continue? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_warning "Setup cancelled by user"
    exit 0
fi

# -----------------------------------------------------------------------------
# Execute Setup Scripts in Order
# -----------------------------------------------------------------------------

SETUP_STEPS=(
    "01-setup-vpc.sh:VPC and Networking"
    "02-setup-security-groups.sh:Security Groups"
    "03-setup-s3.sh:S3 Buckets"
    "04-setup-secrets.sh:Secrets Manager"
    "05-setup-rds.sh:RDS PostgreSQL"
    "06-setup-redis.sh:ElastiCache Redis"
    "07-setup-iam.sh:IAM Roles and Policies"
    "08-setup-ecr.sh:ECR Repositories"
    "09-setup-alb.sh:Application Load Balancer"
    "10-setup-ecs.sh:ECS Cluster and Services"
    "11-setup-cloudfront.sh:CloudFront Distribution"
)

TOTAL_STEPS=${#SETUP_STEPS[@]}
CURRENT_STEP=0

for STEP in "${SETUP_STEPS[@]}"; do
    CURRENT_STEP=$((CURRENT_STEP + 1))
    SCRIPT_NAME="${STEP%%:*}"
    STEP_DESCRIPTION="${STEP##*:}"
    
    print_info ""
    print_info "=========================================="
    print_info "Step $CURRENT_STEP/$TOTAL_STEPS: $STEP_DESCRIPTION"
    print_info "=========================================="
    
    if [ -f "${SCRIPT_DIR}/${SCRIPT_NAME}" ]; then
        bash "${SCRIPT_DIR}/${SCRIPT_NAME}"
        
        if [ $? -ne 0 ]; then
            print_error "Step failed: $STEP_DESCRIPTION"
            print_error "Please check the error messages above and fix any issues"
            exit 1
        fi
    else
        print_error "Script not found: ${SCRIPT_NAME}"
        exit 1
    fi
done

# -----------------------------------------------------------------------------
# Generate Summary
# -----------------------------------------------------------------------------
print_success ""
print_success "=========================================="
print_success "Infrastructure Setup Complete!"
print_success "=========================================="

# Source all info files to display summary (check if they exist first)
for env_file in vpc-info.env alb-info.env cloudfront-info.env rds-info.env redis-info.env ecs-info.env; do
    if [ -f "${SCRIPT_DIR}/${env_file}" ]; then
        source "${SCRIPT_DIR}/${env_file}"
    fi
done

echo ""
print_info "=== Infrastructure Summary ==="
echo ""
print_info "VPC:"
print_info "  VPC ID: ${VPC_ID:-N/A}"
echo ""
print_info "Database:"
print_info "  RDS Endpoint: ${RDS_ENDPOINT:-N/A}"
print_info "  Database: ${RDS_DB_NAME:-N/A}"
echo ""
print_info "Cache:"
print_info "  Redis Endpoint: ${REDIS_ENDPOINT:-N/A}:${REDIS_PORT:-N/A}"
echo ""
print_info "Backend:"
print_info "  ALB URL: http://${ALB_DNS:-N/A}"
print_info "  ECS Cluster: ${ECS_CLUSTER_NAME:-N/A}"
echo ""
print_info "Frontend:"
print_info "  CloudFront URL: https://${CF_DOMAIN:-N/A}"
echo ""
print_warning "IMPORTANT NEXT STEPS:"
echo ""
print_warning "1. Deploy Backend:"
print_warning "   bash ${SCRIPT_DIR}/deploy-backend.sh"
echo ""
print_warning "2. Deploy Frontend:"
print_warning "   bash ${SCRIPT_DIR}/deploy-frontend.sh"
echo ""
print_warning "3. (Optional) Configure Custom Domains:"
print_warning "   - Set CLOUDFRONT_CERT_ARN and ALB_CERT_ARN in config.sh"
print_warning "   - Update Route 53 DNS records"
print_warning "   - Re-run 09-setup-alb.sh and 11-setup-cloudfront.sh"
echo ""
print_warning "4. Update Django Settings:"
print_warning "   - Configure ALLOWED_HOSTS with your domains"
print_warning "   - Update CORS_ALLOWED_ORIGINS"
echo ""
print_warning "5. Monitor Resources:"
print_warning "   - CloudWatch Logs: ${LOG_GROUP_BACKEND:-N/A}"
print_warning "   - ECS Console: https://console.aws.amazon.com/ecs/v2/clusters/${ECS_CLUSTER_NAME:-N/A}"
echo ""

# Save summary to file
SUMMARY_FILE="${SCRIPT_DIR}/infrastructure-summary.txt"
cat > "$SUMMARY_FILE" <<EOF
CBaaS Infrastructure Setup Summary
===================================
Generated: $(date)
Project: $PROJECT_NAME
Environment: $ENVIRONMENT
Region: $AWS_REGION

VPC
---
VPC ID: ${VPC_ID:-N/A}
Public Subnets: ${PUBLIC_SUBNET_1_ID:-N/A}, ${PUBLIC_SUBNET_2_ID:-N/A}
Private Subnets: ${PRIVATE_SUBNET_1_ID:-N/A}, ${PRIVATE_SUBNET_2_ID:-N/A}

Database (RDS PostgreSQL)
-------------------------
Endpoint: ${RDS_ENDPOINT:-N/A}
Database: ${RDS_DB_NAME:-N/A}
Port: 5432

Cache (ElastiCache Redis)
-------------------------
Endpoint: ${REDIS_ENDPOINT:-N/A}
Port: ${REDIS_PORT:-N/A}
TLS: Enabled

Backend (ECS)
-------------
ALB DNS: ${ALB_DNS:-N/A}
ECS Cluster: ${ECS_CLUSTER_NAME:-N/A}
Backend Service: ${ECS_BACKEND_SERVICE:-N/A}
Worker Service: ${ECS_WORKER_SERVICE:-N/A}
Logs: ${LOG_GROUP_BACKEND:-N/A}

Frontend (CloudFront + S3)
--------------------------
CloudFront Domain: ${CF_DOMAIN:-N/A}
S3 Bucket: ${S3_FRONTEND_BUCKET:-N/A}

Next Steps
----------
1. Deploy backend: bash deploy-backend.sh
2. Deploy frontend: bash deploy-frontend.sh
3. Configure custom domains (optional)
4. Update Django settings (ALLOWED_HOSTS, CORS)
EOF

print_success "Summary saved to: $SUMMARY_FILE"
