#!/bin/bash

##############################################################################
# Deploy React Frontend to AWS S3 + CloudFront
# 
# Usage: ./deploy_frontend.sh <S3_BUCKET> <CLOUDFRONT_DISTRIBUTION_ID>
# 
# Example: ./deploy_frontend.sh my-app-bucket E1234ABCDEFGH
##############################################################################

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Validate inputs
if [ $# -ne 2 ]; then
    log_error "Usage: $0 <S3_BUCKET> <CLOUDFRONT_DISTRIBUTION_ID>"
    exit 1
fi

S3_BUCKET=$1
CF_DIST_ID=$2
BUILD_DIR="dist"  # Vite outputs to dist/ by default

# Validate build directory exists
if [ ! -d "$BUILD_DIR" ]; then
    log_error "Build directory '$BUILD_DIR' not found. Run 'npm run build' first."
    exit 1
fi

log_info "Starting deployment to S3 bucket: $S3_BUCKET"

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install it first."
    exit 1
fi

# Verify AWS credentials are configured
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials not configured. Run 'aws configure' or set environment variables."
    exit 1
fi

log_info "AWS credentials verified"

# Step 1: Sync build files to S3
log_info "Uploading files to S3..."

# Delete old files first to ensure clean state
log_info "Removing old files from S3..."
aws s3 rm "s3://${S3_BUCKET}" --recursive

# Upload new files with proper cache headers
log_info "Uploading new build files..."

# Upload index.html with short cache (it contains references to hashed files)
aws s3 cp "${BUILD_DIR}/index.html" "s3://${S3_BUCKET}/index.html" \
    --content-type "text/html" \
    --cache-control "max-age=300, must-revalidate" \
    --metadata-directive REPLACE

log_info "Uploaded index.html with short cache"

# Upload hashed JS/CSS files with long cache (they are immutable)
find "${BUILD_DIR}" -type f \( -name "*.js" -o -name "*.css" \) | while read file; do
    relative_path="${file#$BUILD_DIR/}"
    
    if [[ "$file" == *.js ]]; then
        content_type="application/javascript"
    else
        content_type="text/css"
    fi
    
    aws s3 cp "$file" "s3://${S3_BUCKET}/${relative_path}" \
        --content-type "$content_type" \
        --cache-control "max-age=31536000, immutable"
done

log_info "Uploaded JS/CSS files with long cache"

# Upload other assets (images, fonts, etc.) with medium cache
find "${BUILD_DIR}" -type f ! \( -name "*.html" -o -name "*.js" -o -name "*.css" \) | while read file; do
    relative_path="${file#$BUILD_DIR/}"
    
    # Skip hidden files
    if [[ "$relative_path" == .* ]]; then
        continue
    fi
    
    aws s3 cp "$file" "s3://${S3_BUCKET}/${relative_path}" \
        --cache-control "max-age=86400"
done

log_info "Uploaded other assets with medium cache"

# Step 2: Set bucket policy for public read access (if not already set)
log_info "Ensuring bucket is publicly readable..."

BUCKET_POLICY=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::${S3_BUCKET}/*"
    }
  ]
}
EOF
)

# Create temp file for Windows compatibility
TEMP_POLICY="./temp-s3-policy.json"
echo "$BUCKET_POLICY" > "$TEMP_POLICY"
aws s3api put-bucket-policy \
    --bucket "$S3_BUCKET" \
    --policy "file://$TEMP_POLICY" || log_warn "Could not set bucket policy (may already exist)"
rm -f "$TEMP_POLICY"

# Step 3: Create CloudFront invalidation
log_info "Creating CloudFront invalidation for distribution: $CF_DIST_ID"

INVALIDATION_OUTPUT=$(aws cloudfront create-invalidation \
    --distribution-id "$CF_DIST_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text)

log_info "CloudFront invalidation created: $INVALIDATION_OUTPUT"
log_info "Waiting for invalidation to complete (this may take a few minutes)..."

# Optional: Wait for invalidation to complete
aws cloudfront wait invalidation-completed \
    --distribution-id "$CF_DIST_ID" \
    --id "$INVALIDATION_OUTPUT" || log_warn "Invalidation may still be in progress"

log_info "✅ Deployment completed successfully!"
log_info "Your app should be live at your CloudFront URL in a few minutes."

exit 0
