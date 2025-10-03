#!/bin/bash
# =============================================================================
# Deploy Frontend to S3 and CloudFront
# =============================================================================
# This script:
# 1. Builds the React application
# 2. Syncs build artifacts to S3
# 3. Invalidates CloudFront cache
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
FRONTEND_DIR="${PROJECT_ROOT}/frontend"

source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/s3-info.env"
source "${SCRIPT_DIR}/cloudfront-info.env"

print_info "=========================================="
print_info "Deploying Frontend to S3 and CloudFront"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Validate Prerequisites
# -----------------------------------------------------------------------------
check_aws_cli
validate_aws_credentials

if [ ! -d "$FRONTEND_DIR" ]; then
    print_error "Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install it first."
    exit 1
fi

# -----------------------------------------------------------------------------
# Build Frontend
# -----------------------------------------------------------------------------
print_info "Building React application..."

cd "$FRONTEND_DIR"

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    print_info "Installing dependencies..."
    npm ci
fi

# Build production bundle
print_info "Running production build..."
npm run build

if [ ! -d "dist" ]; then
    print_error "Build failed - dist directory not found"
    exit 1
fi

print_success "Build completed successfully"

# -----------------------------------------------------------------------------
# Sync to S3
# -----------------------------------------------------------------------------
print_info "Syncing files to S3 bucket: $S3_FRONTEND_BUCKET"

# Sync all files
aws s3 sync dist/ "s3://${S3_FRONTEND_BUCKET}/" \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "index.html" \
    --exclude "*.html"

# Upload HTML files with short cache
aws s3 sync dist/ "s3://${S3_FRONTEND_BUCKET}/" \
    --cache-control "public, max-age=0, must-revalidate" \
    --exclude "*" \
    --include "*.html" \
    --content-type "text/html"

print_success "Files synced to S3"

# -----------------------------------------------------------------------------
# Invalidate CloudFront Cache
# -----------------------------------------------------------------------------
print_info "Creating CloudFront invalidation..."

INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id "$CF_DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

print_success "Invalidation created: $INVALIDATION_ID"
print_info "Waiting for invalidation to complete..."

# Wait for invalidation (optional - can be slow)
aws cloudfront wait invalidation-completed \
    --distribution-id "$CF_DISTRIBUTION_ID" \
    --id "$INVALIDATION_ID" 2>/dev/null || \
    print_warning "Invalidation in progress - check status later"

# -----------------------------------------------------------------------------
# Summary
# -----------------------------------------------------------------------------
print_success "=========================================="
print_success "Frontend deployment completed!"
print_success "=========================================="
print_info "Frontend URL: https://${CF_DOMAIN}"
if [ -n "${FRONTEND_DOMAIN:-}" ] && [ -n "${CLOUDFRONT_CERT_ARN:-}" ]; then
    print_info "Custom domain: https://${FRONTEND_DOMAIN}"
fi

cd "$PROJECT_ROOT"
