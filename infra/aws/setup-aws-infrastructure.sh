#!/bin/bash

##############################################################################
# AWS Infrastructure Setup Script for CBaaS Frontend Deployment
# 
# This script sets up:
# 1. S3 bucket for static hosting
# 2. CloudFront distribution
# 3. IAM OIDC provider for GitHub Actions
# 4. IAM role with appropriate permissions
#
# Usage: ./setup-aws-infrastructure.sh <bucket-name> <aws-account-id>
# Example: ./setup-aws-infrastructure.sh cbaas-frontend-prod 123456789012
##############################################################################

set -euo pipefail

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

# Validate inputs
if [ $# -ne 2 ]; then
    log_error "Usage: $0 <bucket-name> <aws-account-id>"
    log_error "Example: $0 cbaas-frontend-prod 123456789012"
    exit 1
fi

BUCKET_NAME=$1
AWS_ACCOUNT_ID=$2
AWS_REGION="ap-south-1"
ROLE_NAME="GitHubActionsDeployRole"
POLICY_DIR="$(dirname "$0")/policies"

# Verify AWS CLI
if ! command -v aws &> /dev/null; then
    log_error "AWS CLI not found. Please install it first."
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    log_error "AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

log_info "Starting AWS infrastructure setup..."
log_info "Bucket: $BUCKET_NAME"
log_info "Region: $AWS_REGION"
log_info "Account ID: $AWS_ACCOUNT_ID"

# Step 1: Create S3 bucket
log_step "Creating S3 bucket..."
if aws s3 ls "s3://${BUCKET_NAME}" 2>/dev/null; then
    log_warn "Bucket ${BUCKET_NAME} already exists, skipping creation"
else
    aws s3 mb "s3://${BUCKET_NAME}" --region "$AWS_REGION"
    log_info "Bucket created successfully"
fi

# Step 2: Enable static website hosting
log_step "Enabling static website hosting..."
aws s3 website "s3://${BUCKET_NAME}" \
    --index-document index.html \
    --error-document index.html

# Step 3: Disable block public access
log_step "Configuring public access settings..."
aws s3api put-public-access-block \
    --bucket "$BUCKET_NAME" \
    --public-access-block-configuration \
    "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Step 4: Apply bucket policy
log_step "Applying S3 bucket policy..."
BUCKET_POLICY=$(cat "$POLICY_DIR/s3-public-policy.json" | sed "s/your-app-bucket-name/$BUCKET_NAME/g")
# Create temp file for Windows compatibility
TEMP_POLICY="./temp-bucket-policy.json"
echo "$BUCKET_POLICY" > "$TEMP_POLICY"
aws s3api put-bucket-policy \
    --bucket "$BUCKET_NAME" \
    --policy "file://$TEMP_POLICY"
rm -f "$TEMP_POLICY"
log_info "Bucket policy applied"

# Step 5: Create OIDC provider (if not exists)
log_step "Setting up GitHub OIDC provider..."
if aws iam get-open-id-connect-provider \
    --open-id-connect-provider-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com" \
    &>/dev/null; then
    log_warn "OIDC provider already exists, skipping"
else
    aws iam create-open-id-connect-provider \
        --url https://token.actions.githubusercontent.com \
        --client-id-list sts.amazonaws.com \
        --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
    log_info "OIDC provider created"
fi

# Step 6: Create IAM role
log_step "Creating IAM role for GitHub Actions..."
TRUST_POLICY=$(cat "$POLICY_DIR/github-trust-policy.json" | sed "s/YOUR_AWS_ACCOUNT_ID/$AWS_ACCOUNT_ID/g")
TEMP_TRUST="./temp-trust-policy.json"
echo "$TRUST_POLICY" > "$TEMP_TRUST"

if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    log_warn "Role $ROLE_NAME already exists, updating trust policy"
    aws iam update-assume-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-document "file://$TEMP_TRUST"
else
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document "file://$TEMP_TRUST"
    log_info "Role created"
fi
rm -f "$TEMP_TRUST"

# Step 7: Attach permissions policy
log_step "Attaching permissions policy to role..."
PERMISSIONS_POLICY=$(cat "$POLICY_DIR/deploy-permissions.json" | \
    sed "s/your-app-bucket-name/$BUCKET_NAME/g" | \
    sed "s/YOUR_AWS_ACCOUNT_ID/$AWS_ACCOUNT_ID/g")
TEMP_PERMS="./temp-permissions-policy.json"
echo "$PERMISSIONS_POLICY" > "$TEMP_PERMS"
aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name DeployFrontendPolicy \
    --policy-document "file://$TEMP_PERMS"
rm -f "$TEMP_PERMS"
log_info "Permissions policy attached"

# Step 8: Create CloudFront distribution
log_step "Creating CloudFront distribution..."

# Get S3 website endpoint
S3_WEBSITE_ENDPOINT="${BUCKET_NAME}.s3-website.${AWS_REGION}.amazonaws.com"

# Create distribution config
DIST_CONFIG=$(cat "$POLICY_DIR/cloudfront-distribution.json" | \
    sed "s/your-app-bucket-name.s3-website.ap-south-1.amazonaws.com/$S3_WEBSITE_ENDPOINT/g" | \
    sed "s/cbaas-frontend-2025/cbaas-frontend-$(date +%s)/g")

# Check if distribution already exists for this origin
EXISTING_DIST=$(aws cloudfront list-distributions --query "DistributionList.Items[?Origins.Items[?DomainName=='$S3_WEBSITE_ENDPOINT']].Id" --output text 2>/dev/null || true)

if [ -n "$EXISTING_DIST" ]; then
    log_warn "CloudFront distribution already exists: $EXISTING_DIST"
    CF_DIST_ID="$EXISTING_DIST"
else
    TEMP_DIST="./temp-cloudfront-config.json"
    echo "$DIST_CONFIG" > "$TEMP_DIST"
    CF_DIST_ID=$(aws cloudfront create-distribution \
        --distribution-config "file://$TEMP_DIST" \
        --query 'Distribution.Id' \
        --output text)
    rm -f "$TEMP_DIST"
    log_info "CloudFront distribution created: $CF_DIST_ID"
    log_warn "Distribution deployment may take 15-30 minutes"
fi

# Get CloudFront domain
CF_DOMAIN=$(aws cloudfront get-distribution --id "$CF_DIST_ID" --query 'Distribution.DomainName' --output text)

# Step 9: Output summary
echo ""
echo "======================================================================"
log_info "✅ AWS Infrastructure Setup Complete!"
echo "======================================================================"
echo ""
echo "📋 Configuration Summary:"
echo "  S3 Bucket: $BUCKET_NAME"
echo "  S3 Website Endpoint: http://$S3_WEBSITE_ENDPOINT"
echo "  CloudFront Distribution ID: $CF_DIST_ID"
echo "  CloudFront Domain: https://$CF_DOMAIN"
echo "  IAM Role ARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
echo ""
echo "🔑 GitHub Secrets to Configure:"
echo "  AWS_ROLE_ARN: arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
echo "  S3_BUCKET: $BUCKET_NAME"
echo "  CF_DIST_ID: $CF_DIST_ID"
echo ""
echo "🌐 Your app will be accessible at: https://$CF_DOMAIN"
echo ""
log_info "Setup complete! You can now deploy using GitHub Actions."
echo "======================================================================"

exit 0
