#!/bin/bash
# =============================================================================
# Setup S3 Buckets
# =============================================================================
# Creates S3 buckets for:
# - Frontend static files (with OAC for CloudFront)
# - Django static files
# - Django media files (private)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

print_info "=========================================="
print_info "Setting up S3 Buckets"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create Frontend Bucket
# -----------------------------------------------------------------------------
print_info "Creating frontend S3 bucket: $S3_FRONTEND_BUCKET"

aws s3api create-bucket \
    --bucket "$S3_FRONTEND_BUCKET" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION" \
    2>/dev/null || print_warning "Bucket $S3_FRONTEND_BUCKET already exists"

# Block all public access (CloudFront will use OAC)
aws s3api put-public-access-block \
    --bucket "$S3_FRONTEND_BUCKET" \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket "$S3_FRONTEND_BUCKET" \
    --versioning-configuration Status=Enabled

# Add bucket tags
aws s3api put-bucket-tagging \
    --bucket "$S3_FRONTEND_BUCKET" \
    --tagging "TagSet=[{Key=Project,Value=${PROJECT_NAME}},{Key=Environment,Value=${ENVIRONMENT}},{Key=ManagedBy,Value=aws-cli-automation}]"

print_success "Frontend bucket created and configured"

# -----------------------------------------------------------------------------
# Create Django Static Bucket
# -----------------------------------------------------------------------------
print_info "Creating Django static S3 bucket: $S3_STATIC_BUCKET"

aws s3api create-bucket \
    --bucket "$S3_STATIC_BUCKET" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION" \
    2>/dev/null || print_warning "Bucket $S3_STATIC_BUCKET already exists"

# Block all public access (will use CloudFront or presigned URLs)
aws s3api put-public-access-block \
    --bucket "$S3_STATIC_BUCKET" \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket "$S3_STATIC_BUCKET" \
    --versioning-configuration Status=Enabled

# Add bucket tags
aws s3api put-bucket-tagging \
    --bucket "$S3_STATIC_BUCKET" \
    --tagging "TagSet=[{Key=Project,Value=${PROJECT_NAME}},{Key=Environment,Value=${ENVIRONMENT}},{Key=ManagedBy,Value=aws-cli-automation}]"

print_success "Django static bucket created and configured"

# -----------------------------------------------------------------------------
# Create Django Media Bucket
# -----------------------------------------------------------------------------
print_info "Creating Django media S3 bucket: $S3_MEDIA_BUCKET"

aws s3api create-bucket \
    --bucket "$S3_MEDIA_BUCKET" \
    --region "$AWS_REGION" \
    --create-bucket-configuration LocationConstraint="$AWS_REGION" \
    2>/dev/null || print_warning "Bucket $S3_MEDIA_BUCKET already exists"

# Block all public access (media served via presigned URLs)
aws s3api put-public-access-block \
    --bucket "$S3_MEDIA_BUCKET" \
    --public-access-block-configuration \
        BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Enable versioning
aws s3api put-bucket-versioning \
    --bucket "$S3_MEDIA_BUCKET" \
    --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
    --bucket "$S3_MEDIA_BUCKET" \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "AES256"
            }
        }]
    }'

# Add bucket tags
aws s3api put-bucket-tagging \
    --bucket "$S3_MEDIA_BUCKET" \
    --tagging "TagSet=[{Key=Project,Value=${PROJECT_NAME}},{Key=Environment,Value=${ENVIRONMENT}},{Key=ManagedBy,Value=aws-cli-automation}]"

# Add lifecycle policy for multipart upload cleanup
aws s3api put-bucket-lifecycle-configuration \
    --bucket "$S3_MEDIA_BUCKET" \
    --lifecycle-configuration '{
        "Rules": [{
            "Id": "DeleteIncompleteMultipartUploads",
            "Status": "Enabled",
            "Prefix": "",
            "AbortIncompleteMultipartUpload": {
                "DaysAfterInitiation": 7
            }
        }]
    }'

print_success "Django media bucket created and configured"

# -----------------------------------------------------------------------------
# Create CloudFront Origin Access Control (OAC)
# -----------------------------------------------------------------------------
print_info "Creating CloudFront Origin Access Control..."

OAC_CONFIG=$(cat <<EOF
{
    "Name": "${PROJECT_NAME}-oac-${ENVIRONMENT}",
    "Description": "OAC for ${PROJECT_NAME} frontend bucket",
    "SigningProtocol": "sigv4",
    "SigningBehavior": "always",
    "OriginAccessControlOriginType": "s3"
}
EOF
)

OAC_ID=$(aws cloudfront create-origin-access-control \
    --origin-access-control-config "$OAC_CONFIG" \
    --query 'OriginAccessControl.Id' \
    --output text 2>/dev/null || \
    aws cloudfront list-origin-access-controls \
        --query "OriginAccessControlList.Items[?Name=='${PROJECT_NAME}-oac-${ENVIRONMENT}'].Id | [0]" \
        --output text)

print_success "Origin Access Control ID: $OAC_ID"

# -----------------------------------------------------------------------------
# Save S3 Information
# -----------------------------------------------------------------------------
S3_INFO_FILE="${SCRIPT_DIR}/s3-info.env"
cat > "$S3_INFO_FILE" <<EOF
# S3 Bucket Names and CloudFront OAC
export S3_FRONTEND_BUCKET="$S3_FRONTEND_BUCKET"
export S3_STATIC_BUCKET="$S3_STATIC_BUCKET"
export S3_MEDIA_BUCKET="$S3_MEDIA_BUCKET"
export OAC_ID="$OAC_ID"
EOF

print_success "S3 information saved to: $S3_INFO_FILE"

print_success "=========================================="
print_success "S3 buckets setup completed!"
print_success "=========================================="
print_info "Bucket URLs:"
print_info "  Frontend: s3://${S3_FRONTEND_BUCKET}"
print_info "  Static: s3://${S3_STATIC_BUCKET}"
print_info "  Media: s3://${S3_MEDIA_BUCKET}"
