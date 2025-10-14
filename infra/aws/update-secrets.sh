#!/bin/bash
# Script to update AWS Secrets Manager with S3 configuration
# Usage: ./update-secrets.sh

set -e

REGION="ap-south-1"
SECRET_NAME="cbaas/backend/env"
BUCKET_NAME="cbaas-static-files"

echo "🔐 Updating AWS Secrets Manager for CBaaS Backend"
echo "=================================================="
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ Error: AWS CLI is not installed"
    echo "   Install: https://aws.amazon.com/cli/"
    exit 1
fi

# Check AWS credentials
echo "✅ Checking AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ Error: AWS credentials not configured"
    echo "   Run: aws configure"
    exit 1
fi

echo "✅ AWS credentials verified"
echo ""

# Prompt for S3 bucket name
read -p "Enter S3 bucket name [default: cbaas-static-files]: " input_bucket
BUCKET_NAME="${input_bucket:-$BUCKET_NAME}"

echo ""
echo "📦 S3 Bucket: $BUCKET_NAME"
echo ""

# Check if bucket exists
if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
    echo "✅ S3 bucket '$BUCKET_NAME' exists"
else
    echo "⚠️  S3 bucket '$BUCKET_NAME' not found"
    read -p "Do you want to create it? (y/n): " create_bucket
    if [ "$create_bucket" = "y" ]; then
        echo "Creating bucket..."
        aws s3api create-bucket \
            --bucket "$BUCKET_NAME" \
            --region "$REGION" \
            --create-bucket-configuration LocationConstraint="$REGION"
        echo "✅ Bucket created"
    else
        echo "❌ Bucket required. Exiting."
        exit 1
    fi
fi

echo ""

# Prompt for AWS credentials
echo "🔑 Enter AWS IAM User Credentials for S3 Access"
echo "(You can create these with: aws iam create-access-key --user-name cbaas-s3-user)"
echo ""

read -p "AWS_ACCESS_KEY_ID: " aws_access_key_id
read -s -p "AWS_SECRET_ACCESS_KEY: " aws_secret_access_key
echo ""
echo ""

# Validate inputs
if [ -z "$aws_access_key_id" ] || [ -z "$aws_secret_access_key" ]; then
    echo "❌ Error: AWS credentials cannot be empty"
    exit 1
fi

# Get current secret value
echo "📥 Fetching current secret from Secrets Manager..."
CURRENT_SECRET=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --query SecretString \
    --output text)

if [ $? -ne 0 ]; then
    echo "❌ Error: Could not fetch secret '$SECRET_NAME'"
    exit 1
fi

echo "✅ Current secret retrieved"
echo ""

# Update secret with new values using jq
echo "🔄 Updating secret with S3 configuration..."

UPDATED_SECRET=$(echo "$CURRENT_SECRET" | jq \
    --arg access_key "$aws_access_key_id" \
    --arg secret_key "$aws_secret_access_key" \
    --arg bucket "$BUCKET_NAME" \
    '. + {
        "AWS_ACCESS_KEY_ID": $access_key,
        "AWS_SECRET_ACCESS_KEY": $secret_key,
        "AWS_STORAGE_BUCKET_NAME": $bucket
    }')

# Update the secret
aws secretsmanager update-secret \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" \
    --secret-string "$UPDATED_SECRET"

if [ $? -eq 0 ]; then
    echo "✅ Secret updated successfully!"
else
    echo "❌ Error: Failed to update secret"
    exit 1
fi

echo ""
echo "📋 Summary of Updated Secret Keys:"
echo "$UPDATED_SECRET" | jq -r 'keys[]' | sed 's/^/  - /'

echo ""
echo "✅ Done! Next steps:"
echo "   1. Register updated task definition:"
echo "      aws ecs register-task-definition --cli-input-json file://infra/aws/task-definition.json"
echo ""
echo "   2. Force new deployment:"
echo "      aws ecs update-service --cluster cbaas-cluster --service cbaas-backend-service --force-new-deployment"
echo ""
echo "   3. Verify at: https://your-api.com/api/debug/static"
