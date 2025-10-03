#!/bin/bash
# =============================================================================
# AWS Credentials Setup Helper
# =============================================================================
# This script helps you configure AWS credentials for the first time
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

print_info "=========================================="
print_info "AWS Credentials Setup Helper"
print_info "=========================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed!"
    echo ""
    print_info "Please install AWS CLI first:"
    print_info "  Windows: https://awscli.amazonaws.com/AWSCLIV2.msi"
    print_info "  Linux: curl \"https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip\" -o \"awscliv2.zip\""
    print_info "  Mac: brew install awscli"
    exit 1
fi

print_success "AWS CLI is installed: $(aws --version)"
echo ""

# Check if credentials already exist
if aws sts get-caller-identity &> /dev/null; then
    print_warning "AWS credentials are already configured!"
    ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)
    USER=$(aws sts get-caller-identity --query 'Arn' --output text)
    REGION=$(aws configure get region || echo "not set")
    
    echo ""
    print_info "Current configuration:"
    print_info "  Account: $ACCOUNT"
    print_info "  User: $USER"
    print_info "  Region: $REGION"
    echo ""
    
    read -p "Do you want to reconfigure? (yes/no): " RECONFIGURE
    if [ "$RECONFIGURE" != "yes" ]; then
        print_info "Keeping existing configuration"
        exit 0
    fi
fi

# Guide user through creating credentials
echo ""
print_info "=========================================="
print_info "Step 1: Create AWS Access Keys"
print_info "=========================================="
echo ""
print_info "1. Login to AWS Console: https://console.aws.amazon.com/"
print_info "2. Click on your username (top right) → Security Credentials"
print_info "3. Scroll to 'Access keys' section"
print_info "4. Click 'Create access key'"
print_info "5. Select 'Command Line Interface (CLI)'"
print_info "6. Check 'I understand...' and click 'Next'"
print_info "7. (Optional) Add description and click 'Create access key'"
print_info "8. Copy both 'Access key ID' and 'Secret access key'"
echo ""
print_warning "IMPORTANT: Save the secret key securely - you can't view it again!"
echo ""

read -p "Press ENTER when you have your credentials ready..."

# Interactive configuration
echo ""
print_info "=========================================="
print_info "Step 2: Configure AWS CLI"
print_info "=========================================="
echo ""

# Get Access Key ID
while true; do
    read -p "Enter AWS Access Key ID: " AWS_ACCESS_KEY_ID
    if [ -n "$AWS_ACCESS_KEY_ID" ]; then
        break
    else
        print_error "Access Key ID cannot be empty"
    fi
done

# Get Secret Access Key
while true; do
    read -sp "Enter AWS Secret Access Key: " AWS_SECRET_ACCESS_KEY
    echo ""
    if [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
        break
    else
        print_error "Secret Access Key cannot be empty"
    fi
done

# Get Region
echo ""
print_info "Common AWS Regions:"
print_info "  us-east-1      (N. Virginia)"
print_info "  us-west-2      (Oregon)"
print_info "  eu-west-1      (Ireland)"
print_info "  ap-south-1     (Mumbai)"
print_info "  ap-southeast-1 (Singapore)"
echo ""

read -p "Enter AWS Region [ap-south-1]: " AWS_REGION
AWS_REGION=${AWS_REGION:-ap-south-1}

# Configure AWS CLI
echo ""
print_info "Configuring AWS CLI..."

aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID"
aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY"
aws configure set region "$AWS_REGION"
aws configure set output "json"

# Verify credentials
echo ""
print_info "Verifying credentials..."

if aws sts get-caller-identity &> /dev/null; then
    print_success "AWS credentials configured successfully!"
    echo ""
    
    ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)
    USER_ARN=$(aws sts get-caller-identity --query 'Arn' --output text)
    USER_NAME=$(echo "$USER_ARN" | cut -d'/' -f2)
    
    print_info "=========================================="
    print_info "Configuration Summary"
    print_info "=========================================="
    print_info "  AWS Account ID: $ACCOUNT"
    print_info "  User: $USER_NAME"
    print_info "  Region: $AWS_REGION"
    print_info "  Config location: ~/.aws/credentials"
    print_info "=========================================="
    echo ""
    
    print_success "You can now run the infrastructure setup:"
    print_info "  cd $(dirname "$0")"
    print_info "  bash infra-setup.sh"
    echo ""
else
    print_error "Credential verification failed!"
    print_error "Please check your Access Key ID and Secret Access Key"
    echo ""
    print_info "You can run this script again to retry"
    exit 1
fi

# Check IAM permissions
echo ""
print_info "Checking IAM permissions..."

if aws iam get-user &> /dev/null; then
    print_success "IAM read access confirmed"
    
    # Check for admin access
    POLICIES=$(aws iam list-attached-user-policies --user-name "$USER_NAME" --query 'AttachedPolicies[*].PolicyName' --output text 2>/dev/null || echo "")
    
    if echo "$POLICIES" | grep -q "AdministratorAccess"; then
        print_success "Administrator access detected - you have full permissions"
    else
        print_warning "Administrator access not detected"
        print_warning "You may need additional permissions for infrastructure setup"
        echo ""
        print_info "Required permissions include:"
        print_info "  - VPC, EC2, RDS, ElastiCache"
        print_info "  - ECS, ECR, ELB"
        print_info "  - S3, CloudFront, Route53"
        print_info "  - IAM, Secrets Manager"
        print_info "  - CloudWatch Logs"
    fi
else
    print_warning "Could not verify IAM permissions"
    print_warning "If infrastructure setup fails, ensure your user has sufficient permissions"
fi

echo ""
print_success "Setup complete! 🎉"
