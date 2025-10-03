#!/bin/bash
# =============================================================================
# Cleanup AWS Infrastructure
# =============================================================================
# WARNING: This script deletes ALL AWS resources created by infra-setup.sh
# Use with extreme caution! This is irreversible!
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

print_error "=========================================="
print_error "AWS INFRASTRUCTURE CLEANUP"
print_error "=========================================="
print_warning "This will DELETE all AWS resources for:"
print_warning "  Project: $PROJECT_NAME"
print_warning "  Environment: $ENVIRONMENT"
print_warning "  Region: $AWS_REGION"
print_error "=========================================="
print_error "THIS IS IRREVERSIBLE!"
print_error "=========================================="

# Triple confirmation
read -p "Type 'DELETE' to confirm: " CONFIRM1
if [ "$CONFIRM1" != "DELETE" ]; then
    print_info "Cleanup cancelled"
    exit 0
fi

read -p "Type the project name '${PROJECT_NAME}' to confirm: " CONFIRM2
if [ "$CONFIRM2" != "$PROJECT_NAME" ]; then
    print_info "Cleanup cancelled"
    exit 0
fi

read -p "Are you absolutely sure? (yes/no): " CONFIRM3
if [ "$CONFIRM3" != "yes" ]; then
    print_info "Cleanup cancelled"
    exit 0
fi

print_warning "Starting cleanup in 5 seconds... Press Ctrl+C to abort"
sleep 5

# Load all resource IDs
if [ -f "${SCRIPT_DIR}/ecs-info.env" ]; then source "${SCRIPT_DIR}/ecs-info.env"; fi
if [ -f "${SCRIPT_DIR}/alb-info.env" ]; then source "${SCRIPT_DIR}/alb-info.env"; fi
if [ -f "${SCRIPT_DIR}/cloudfront-info.env" ]; then source "${SCRIPT_DIR}/cloudfront-info.env"; fi
if [ -f "${SCRIPT_DIR}/ecr-info.env" ]; then source "${SCRIPT_DIR}/ecr-info.env"; fi
if [ -f "${SCRIPT_DIR}/rds-info.env" ]; then source "${SCRIPT_DIR}/rds-info.env"; fi
if [ -f "${SCRIPT_DIR}/redis-info.env" ]; then source "${SCRIPT_DIR}/redis-info.env"; fi
if [ -f "${SCRIPT_DIR}/vpc-info.env" ]; then source "${SCRIPT_DIR}/vpc-info.env"; fi
if [ -f "${SCRIPT_DIR}/sg-info.env" ]; then source "${SCRIPT_DIR}/sg-info.env"; fi
if [ -f "${SCRIPT_DIR}/s3-info.env" ]; then source "${SCRIPT_DIR}/s3-info.env"; fi
if [ -f "${SCRIPT_DIR}/waf-info.env" ]; then source "${SCRIPT_DIR}/waf-info.env"; fi

# -----------------------------------------------------------------------------
# Delete ECS Services and Cluster
# -----------------------------------------------------------------------------
if [ -n "${ECS_CLUSTER_NAME:-}" ]; then
    print_info "Deleting ECS services..."
    
    if [ -n "${ECS_BACKEND_SERVICE:-}" ]; then
        aws ecs update-service \
            --cluster "$ECS_CLUSTER_NAME" \
            --service "$ECS_BACKEND_SERVICE" \
            --desired-count 0 2>/dev/null || true
        
        aws ecs delete-service \
            --cluster "$ECS_CLUSTER_NAME" \
            --service "$ECS_BACKEND_SERVICE" \
            --force 2>/dev/null || true
    fi
    
    if [ -n "${ECS_WORKER_SERVICE:-}" ]; then
        aws ecs update-service \
            --cluster "$ECS_CLUSTER_NAME" \
            --service "$ECS_WORKER_SERVICE" \
            --desired-count 0 2>/dev/null || true
        
        aws ecs delete-service \
            --cluster "$ECS_CLUSTER_NAME" \
            --service "$ECS_WORKER_SERVICE" \
            --force 2>/dev/null || true
    fi
    
    sleep 10
    
    print_info "Deleting ECS cluster..."
    aws ecs delete-cluster --cluster "$ECS_CLUSTER_NAME" 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# Delete CloudFront Distribution
# -----------------------------------------------------------------------------
if [ -n "${CF_DISTRIBUTION_ID:-}" ]; then
    print_info "Disabling CloudFront distribution..."
    
    ETAG=$(aws cloudfront get-distribution \
        --id "$CF_DISTRIBUTION_ID" \
        --query 'ETag' \
        --output text 2>/dev/null)
    
    if [ -n "$ETAG" ]; then
        aws cloudfront get-distribution-config \
            --id "$CF_DISTRIBUTION_ID" \
            --query 'DistributionConfig' \
            --output json > /tmp/cf-config.json
        
        jq '.Enabled = false' /tmp/cf-config.json > /tmp/cf-config-disabled.json
        
        aws cloudfront update-distribution \
            --id "$CF_DISTRIBUTION_ID" \
            --if-match "$ETAG" \
            --distribution-config file:///tmp/cf-config-disabled.json 2>/dev/null || true
        
        print_info "Waiting for CloudFront to deploy..."
        aws cloudfront wait distribution-deployed --id "$CF_DISTRIBUTION_ID" 2>/dev/null || true
        
        ETAG=$(aws cloudfront get-distribution \
            --id "$CF_DISTRIBUTION_ID" \
            --query 'ETag' \
            --output text 2>/dev/null)
        
        aws cloudfront delete-distribution \
            --id "$CF_DISTRIBUTION_ID" \
            --if-match "$ETAG" 2>/dev/null || true
    fi
fi

# -----------------------------------------------------------------------------
# Delete WAF
# -----------------------------------------------------------------------------
if [ -n "${WAF_ACL_ARN:-}" ]; then
    print_info "Deleting WAF Web ACL..."
    
    # Disassociate from CloudFront first
    aws wafv2 disassociate-web-acl \
        --region us-east-1 \
        --resource-arn "$CF_ARN" 2>/dev/null || true
    
    # Get lock token
    LOCK_TOKEN=$(aws wafv2 get-web-acl \
        --region us-east-1 \
        --scope CLOUDFRONT \
        --id "${WAF_ACL_ARN##*/}" \
        --name "$WAF_WEB_ACL_NAME" \
        --query 'LockToken' \
        --output text 2>/dev/null)
    
    if [ -n "$LOCK_TOKEN" ]; then
        aws wafv2 delete-web-acl \
            --region us-east-1 \
            --scope CLOUDFRONT \
            --id "${WAF_ACL_ARN##*/}" \
            --name "$WAF_WEB_ACL_NAME" \
            --lock-token "$LOCK_TOKEN" 2>/dev/null || true
    fi
fi

# -----------------------------------------------------------------------------
# Delete ALB
# -----------------------------------------------------------------------------
if [ -n "${ALB_ARN:-}" ]; then
    print_info "Deleting ALB listeners..."
    
    LISTENERS=$(aws elbv2 describe-listeners \
        --load-balancer-arn "$ALB_ARN" \
        --query 'Listeners[].ListenerArn' \
        --output text 2>/dev/null)
    
    for LISTENER in $LISTENERS; do
        aws elbv2 delete-listener --listener-arn "$LISTENER" 2>/dev/null || true
    done
    
    print_info "Deleting ALB..."
    aws elbv2 delete-load-balancer --load-balancer-arn "$ALB_ARN" 2>/dev/null || true
fi

if [ -n "${TARGET_GROUP_ARN:-}" ]; then
    sleep 5
    print_info "Deleting target group..."
    aws elbv2 delete-target-group --target-group-arn "$TARGET_GROUP_ARN" 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# Delete RDS
# -----------------------------------------------------------------------------
if [ -n "${RDS_INSTANCE_ID:-}" ]; then
    print_info "Deleting RDS instance (this may take several minutes)..."
    
    # Modify to remove deletion protection
    aws rds modify-db-instance \
        --db-instance-identifier "$RDS_INSTANCE_ID" \
        --no-deletion-protection 2>/dev/null || true
    
    sleep 5
    
    aws rds delete-db-instance \
        --db-instance-identifier "$RDS_INSTANCE_ID" \
        --skip-final-snapshot \
        --delete-automated-backups 2>/dev/null || true
fi

# Delete DB subnet group
aws rds delete-db-subnet-group \
    --db-subnet-group-name "${PROJECT_NAME}-db-subnet-group-${ENVIRONMENT}" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Delete ElastiCache
# -----------------------------------------------------------------------------
if [ -n "${REDIS_CLUSTER_ID:-}" ]; then
    print_info "Deleting Redis cluster..."
    aws elasticache delete-cache-cluster \
        --cache-cluster-id "$REDIS_CLUSTER_ID" 2>/dev/null || true
fi

aws elasticache delete-cache-subnet-group \
    --cache-subnet-group-name "${PROJECT_NAME}-redis-subnet-group-${ENVIRONMENT}" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Delete S3 Buckets
# -----------------------------------------------------------------------------
for BUCKET in "${S3_FRONTEND_BUCKET:-}" "${S3_STATIC_BUCKET:-}" "${S3_MEDIA_BUCKET:-}"; do
    if [ -n "$BUCKET" ]; then
        print_info "Emptying and deleting S3 bucket: $BUCKET"
        aws s3 rm "s3://${BUCKET}" --recursive 2>/dev/null || true
        aws s3 rb "s3://${BUCKET}" --force 2>/dev/null || true
    fi
done

# -----------------------------------------------------------------------------
# Delete ECR Repositories
# -----------------------------------------------------------------------------
if [ -n "${ECR_BACKEND_REPO:-}" ]; then
    print_info "Deleting ECR repository..."
    aws ecr delete-repository \
        --repository-name "$ECR_BACKEND_REPO" \
        --force 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# Delete CloudWatch Log Groups
# -----------------------------------------------------------------------------
for LOG_GROUP in "${LOG_GROUP_BACKEND:-}" "${LOG_GROUP_WORKER:-}"; do
    if [ -n "$LOG_GROUP" ]; then
        print_info "Deleting CloudWatch log group: $LOG_GROUP"
        aws logs delete-log-group --log-group-name "$LOG_GROUP" 2>/dev/null || true
    fi
done

# -----------------------------------------------------------------------------
# Delete NAT Gateways and Elastic IPs
# -----------------------------------------------------------------------------
if [ -n "${NAT_GW_1_ID:-}" ]; then
    print_info "Deleting NAT Gateway 1..."
    aws ec2 delete-nat-gateway --nat-gateway-id "$NAT_GW_1_ID" 2>/dev/null || true
fi

if [ -n "${NAT_GW_2_ID:-}" ]; then
    print_info "Deleting NAT Gateway 2..."
    aws ec2 delete-nat-gateway --nat-gateway-id "$NAT_GW_2_ID" 2>/dev/null || true
fi

# Wait for NAT Gateways to be deleted
print_info "Waiting for NAT Gateways to be deleted..."
sleep 60

# Release Elastic IPs
EIPS=$(aws ec2 describe-addresses \
    --filters "Name=tag:Project,Values=${PROJECT_NAME}" \
    --query 'Addresses[].AllocationId' \
    --output text 2>/dev/null)

for EIP in $EIPS; do
    print_info "Releasing Elastic IP: $EIP"
    aws ec2 release-address --allocation-id "$EIP" 2>/dev/null || true
done

# -----------------------------------------------------------------------------
# Delete VPC Resources
# -----------------------------------------------------------------------------
if [ -n "${VPC_ID:-}" ]; then
    print_info "Deleting VPC resources..."
    
    # Delete route table associations
    for RT in "${PUBLIC_RT_ID:-}" "${PRIVATE_RT_1_ID:-}" "${PRIVATE_RT_2_ID:-}"; do
        if [ -n "$RT" ]; then
            ASSOCIATIONS=$(aws ec2 describe-route-tables \
                --route-table-ids "$RT" \
                --query 'RouteTables[].Associations[?!Main].RouteTableAssociationId' \
                --output text 2>/dev/null)
            
            for ASSOC in $ASSOCIATIONS; do
                aws ec2 disassociate-route-table --association-id "$ASSOC" 2>/dev/null || true
            done
        fi
    done
    
    # Delete route tables
    for RT in "${PUBLIC_RT_ID:-}" "${PRIVATE_RT_1_ID:-}" "${PRIVATE_RT_2_ID:-}"; do
        if [ -n "$RT" ]; then
            aws ec2 delete-route-table --route-table-id "$RT" 2>/dev/null || true
        fi
    done
    
    # Detach and delete internet gateway
    if [ -n "${IGW_ID:-}" ]; then
        aws ec2 detach-internet-gateway --internet-gateway-id "$IGW_ID" --vpc-id "$VPC_ID" 2>/dev/null || true
        aws ec2 delete-internet-gateway --internet-gateway-id "$IGW_ID" 2>/dev/null || true
    fi
    
    # Delete subnets
    for SUBNET in "${PUBLIC_SUBNET_1_ID:-}" "${PUBLIC_SUBNET_2_ID:-}" "${PRIVATE_SUBNET_1_ID:-}" "${PRIVATE_SUBNET_2_ID:-}"; do
        if [ -n "$SUBNET" ]; then
            aws ec2 delete-subnet --subnet-id "$SUBNET" 2>/dev/null || true
        fi
    done
    
    # Delete security groups (except default)
    for SG in "${ALB_SG_ID:-}" "${ECS_SG_ID:-}" "${RDS_SG_ID:-}" "${REDIS_SG_ID:-}"; do
        if [ -n "$SG" ]; then
            aws ec2 delete-security-group --group-id "$SG" 2>/dev/null || true
        fi
    done
    
    # Delete VPC
    aws ec2 delete-vpc --vpc-id "$VPC_ID" 2>/dev/null || true
fi

# -----------------------------------------------------------------------------
# Delete Secrets
# -----------------------------------------------------------------------------
for SECRET in "${SECRET_DJANGO_SECRET:-}" "${SECRET_DB_CREDENTIALS:-}" "${SECRET_REDIS_AUTH:-}"; do
    if [ -n "$SECRET" ]; then
        print_info "Deleting secret: $SECRET"
        aws secretsmanager delete-secret \
            --secret-id "$SECRET" \
            --force-delete-without-recovery 2>/dev/null || true
    fi
done

# -----------------------------------------------------------------------------
# Delete IAM Roles and Policies
# -----------------------------------------------------------------------------
print_info "Deleting IAM roles..."

# Detach policies from execution role
if [ -n "${ECS_EXECUTION_ROLE_NAME:-}" ]; then
    aws iam detach-role-policy \
        --role-name "$ECS_EXECUTION_ROLE_NAME" \
        --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" 2>/dev/null || true
    
    aws iam detach-role-policy \
        --role-name "$ECS_EXECUTION_ROLE_NAME" \
        --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${PROJECT_NAME}-ecs-execution-policy-${ENVIRONMENT}" 2>/dev/null || true
    
    aws iam delete-role --role-name "$ECS_EXECUTION_ROLE_NAME" 2>/dev/null || true
fi

# Detach policies from task role
if [ -n "${ECS_TASK_ROLE_NAME:-}" ]; then
    aws iam detach-role-policy \
        --role-name "$ECS_TASK_ROLE_NAME" \
        --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${PROJECT_NAME}-ecs-task-policy-${ENVIRONMENT}" 2>/dev/null || true
    
    aws iam delete-role --role-name "$ECS_TASK_ROLE_NAME" 2>/dev/null || true
fi

# Delete policies
aws iam delete-policy \
    --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${PROJECT_NAME}-ecs-execution-policy-${ENVIRONMENT}" 2>/dev/null || true

aws iam delete-policy \
    --policy-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${PROJECT_NAME}-ecs-task-policy-${ENVIRONMENT}" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Delete Generated Files
# -----------------------------------------------------------------------------
print_info "Deleting generated files..."
rm -f "${SCRIPT_DIR}"/*.env
rm -f "${SCRIPT_DIR}"/backend-task-definition.json
rm -f "${SCRIPT_DIR}"/worker-task-definition.json
rm -f "${SCRIPT_DIR}"/cloudfront-config.json
rm -f "${SCRIPT_DIR}"/waf-config.json
rm -f "${SCRIPT_DIR}"/infrastructure-summary.txt

print_success "=========================================="
print_success "Cleanup completed!"
print_success "=========================================="
print_warning "Some resources may take time to fully delete:"
print_warning "  - RDS instances: ~5-10 minutes"
print_warning "  - CloudFront distributions: ~15-20 minutes"
print_warning "  - NAT Gateways: ~5 minutes"
print_info ""
print_info "Verify cleanup in AWS Console after 30 minutes"
