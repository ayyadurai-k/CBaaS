#!/bin/bash

##############################################################################
# Static File Debug Script for CBaaS Backend
# 
# This script helps debug static file serving issues in the ECS deployment
##############################################################################

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

CLUSTER_NAME="cbaas-cluster"
SERVICE_NAME="cbaas-backend-service"
CONTAINER_NAME="cbaas-backend"
ALB_URL="http://cbaas-alb-1444354359.ap-south-1.elb.amazonaws.com"

log_info "Static File Debug Script for CBaaS Backend"
echo "=============================================="

# Step 1: Get running task
log_step "Getting running task ARN..."
TASK_ARN=$(aws ecs list-tasks \
    --cluster "$CLUSTER_NAME" \
    --service-name "$SERVICE_NAME" \
    --query 'taskArns[0]' \
    --output text)

if [ "$TASK_ARN" = "None" ] || [ -z "$TASK_ARN" ]; then
    log_error "No running tasks found for service $SERVICE_NAME"
    exit 1
fi

log_info "Task ARN: $TASK_ARN"

# Step 2: Check static files in container
log_step "Checking static files in container..."
echo "Executing: ls -la /app/staticfiles/"
aws ecs execute-command \
    --cluster "$CLUSTER_NAME" \
    --task "$TASK_ARN" \
    --container "$CONTAINER_NAME" \
    --interactive \
    --command "ls -la /app/staticfiles/"

echo ""

# Step 3: Check admin static files specifically
log_step "Checking admin static files..."
echo "Executing: ls -la /app/staticfiles/admin/"
aws ecs execute-command \
    --cluster "$CLUSTER_NAME" \
    --task "$TASK_ARN" \
    --container "$CONTAINER_NAME" \
    --interactive \
    --command "ls -la /app/staticfiles/admin/"

echo ""

# Step 4: Check DRF static files
log_step "Checking Django REST Framework static files..."
echo "Executing: ls -la /app/staticfiles/rest_framework/"
aws ecs execute-command \
    --cluster "$CLUSTER_NAME" \
    --task "$TASK_ARN" \
    --container "$CONTAINER_NAME" \
    --interactive \
    --command "ls -la /app/staticfiles/rest_framework/ 2>/dev/null || echo 'DRF static files not found'"

echo ""

# Step 5: Test static file URLs
log_step "Testing static file URLs from outside..."

# Test admin CSS
echo "Testing admin base CSS:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$ALB_URL/static/admin/css/base.css")
echo "  $ALB_URL/static/admin/css/base.css - HTTP $HTTP_CODE"

# Test DRF CSS
echo "Testing DRF CSS:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$ALB_URL/static/rest_framework/css/bootstrap.min.css")
echo "  $ALB_URL/static/rest_framework/css/bootstrap.min.css - HTTP $HTTP_CODE"

# Test any CSS file
echo "Testing any available CSS file:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$ALB_URL/static/admin/css/fonts.css")
echo "  $ALB_URL/static/admin/css/fonts.css - HTTP $HTTP_CODE"

echo ""

# Step 6: Check Django settings
log_step "Checking Django settings in container..."
echo "Checking STATIC_ROOT and STATIC_URL:"
aws ecs execute-command \
    --cluster "$CLUSTER_NAME" \
    --task "$TASK_ARN" \
    --container "$CONTAINER_NAME" \
    --interactive \
    --command "python -c \"from django.conf import settings; print(f'STATIC_ROOT: {settings.STATIC_ROOT}'); print(f'STATIC_URL: {settings.STATIC_URL}'); print(f'DEBUG: {settings.DEBUG}')\""

echo ""

# Step 7: Test health endpoint
log_step "Testing health endpoint..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$ALB_URL/api/healthz")
echo "Health endpoint - HTTP $HTTP_CODE"

echo ""
log_info "Debug script completed!"
echo "=============================================="