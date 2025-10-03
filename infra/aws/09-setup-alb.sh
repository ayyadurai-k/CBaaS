#!/bin/bash
# =============================================================================
# Setup Application Load Balancer (ALB)
# =============================================================================
# Creates:
# - Application Load Balancer in public subnets
# - Target group for backend ECS tasks
# - HTTP listener (redirects to HTTPS if cert provided)
# - HTTPS listener (if certificate ARN provided)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/vpc-info.env"
source "${SCRIPT_DIR}/sg-info.env"

print_info "=========================================="
print_info "Setting up Application Load Balancer"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create Application Load Balancer
# -----------------------------------------------------------------------------
print_info "Creating Application Load Balancer..."

ALB_ARN=$(aws elbv2 create-load-balancer \
    --name "$ALB_NAME" \
    --subnets "$PUBLIC_SUBNET_1_ID" "$PUBLIC_SUBNET_2_ID" \
    --security-groups "$ALB_SG_ID" \
    --scheme internet-facing \
    --type application \
    --ip-address-type ipv4 \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    --query 'LoadBalancers[0].LoadBalancerArn' \
    --output text 2>/dev/null || \
    aws elbv2 describe-load-balancers \
        --names "$ALB_NAME" \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text)

print_success "ALB ARN: $ALB_ARN"

# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers \
    --load-balancer-arns "$ALB_ARN" \
    --query 'LoadBalancers[0].DNSName' \
    --output text)

print_success "ALB DNS: $ALB_DNS"

# -----------------------------------------------------------------------------
# Create Target Group
# -----------------------------------------------------------------------------
print_info "Creating target group for backend..."

TARGET_GROUP_ARN=$(aws elbv2 create-target-group \
    --name "$ALB_TARGET_GROUP" \
    --protocol HTTP \
    --port 8000 \
    --vpc-id "$VPC_ID" \
    --target-type ip \
    --health-check-enabled \
    --health-check-protocol HTTP \
    --health-check-path "/healthz" \
    --health-check-interval-seconds 30 \
    --health-check-timeout-seconds 5 \
    --healthy-threshold-count 2 \
    --unhealthy-threshold-count 3 \
    --matcher HttpCode=200 \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text 2>/dev/null || \
    aws elbv2 describe-target-groups \
        --names "$ALB_TARGET_GROUP" \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)

print_success "Target Group ARN: $TARGET_GROUP_ARN"

# Configure target group attributes
aws elbv2 modify-target-group-attributes \
    --target-group-arn "$TARGET_GROUP_ARN" \
    --attributes \
        Key=deregistration_delay.timeout_seconds,Value=30 \
        Key=stickiness.enabled,Value=true \
        Key=stickiness.type,Value=lb_cookie \
        Key=stickiness.lb_cookie.duration_seconds,Value=86400

# -----------------------------------------------------------------------------
# Create Listeners
# -----------------------------------------------------------------------------
if [ -n "$ALB_CERT_ARN" ]; then
    print_info "Creating HTTPS listener with certificate..."
    
    # HTTPS Listener
    HTTPS_LISTENER_ARN=$(aws elbv2 create-listener \
        --load-balancer-arn "$ALB_ARN" \
        --protocol HTTPS \
        --port 443 \
        --certificates CertificateArn="$ALB_CERT_ARN" \
        --default-actions Type=forward,TargetGroupArn="$TARGET_GROUP_ARN" \
        --query 'Listeners[0].ListenerArn' \
        --output text 2>/dev/null || \
        aws elbv2 describe-listeners \
            --load-balancer-arn "$ALB_ARN" \
            --query "Listeners[?Port==\`443\`].ListenerArn | [0]" \
            --output text)
    
    print_success "HTTPS Listener ARN: $HTTPS_LISTENER_ARN"
    
    # HTTP Listener (redirect to HTTPS)
    HTTP_LISTENER_ARN=$(aws elbv2 create-listener \
        --load-balancer-arn "$ALB_ARN" \
        --protocol HTTP \
        --port 80 \
        --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}" \
        --query 'Listeners[0].ListenerArn' \
        --output text 2>/dev/null || \
        aws elbv2 describe-listeners \
            --load-balancer-arn "$ALB_ARN" \
            --query "Listeners[?Port==\`80\`].ListenerArn | [0]" \
            --output text)
    
    print_success "HTTP Listener ARN (redirects to HTTPS): $HTTP_LISTENER_ARN"
else
    print_warning "No certificate ARN provided, creating HTTP listener only"
    
    # HTTP Listener only
    HTTP_LISTENER_ARN=$(aws elbv2 create-listener \
        --load-balancer-arn "$ALB_ARN" \
        --protocol HTTP \
        --port 80 \
        --default-actions Type=forward,TargetGroupArn="$TARGET_GROUP_ARN" \
        --query 'Listeners[0].ListenerArn' \
        --output text 2>/dev/null || \
        aws elbv2 describe-listeners \
            --load-balancer-arn "$ALB_ARN" \
            --query "Listeners[?Port==\`80\`].ListenerArn | [0]" \
            --output text)
    
    print_success "HTTP Listener ARN: $HTTP_LISTENER_ARN"
fi

# -----------------------------------------------------------------------------
# Save ALB Information
# -----------------------------------------------------------------------------
ALB_INFO_FILE="${SCRIPT_DIR}/alb-info.env"
cat > "$ALB_INFO_FILE" <<EOF
# Application Load Balancer Information
export ALB_ARN="$ALB_ARN"
export ALB_DNS="$ALB_DNS"
export TARGET_GROUP_ARN="$TARGET_GROUP_ARN"
export ALB_NAME="$ALB_NAME"
EOF

print_success "ALB information saved to: $ALB_INFO_FILE"

print_success "=========================================="
print_success "ALB setup completed successfully!"
print_success "=========================================="
print_info "Backend will be accessible at: http://${ALB_DNS}"
if [ -n "$ALB_CERT_ARN" ]; then
    print_info "HTTPS enabled - configure DNS to point to this ALB"
fi
