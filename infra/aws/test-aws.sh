#!/bin/bash
# Quick test script to verify AWS CLI and resource creation

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

print_info "Testing AWS CLI..."

# Test 1: Check credentials
print_info "Test 1: Verifying AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    ACCOUNT=$(aws sts get-caller-identity --query 'Account' --output text)
    print_success "AWS Account: $ACCOUNT"
else
    print_error "AWS credentials not configured"
    exit 1
fi

# Test 2: Check for existing VPC
print_info "Test 2: Checking for existing VPC..."
VPC_CHECK=$(aws ec2 describe-vpcs \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-vpc-${ENVIRONMENT}" \
    --query 'Vpcs[0].VpcId' \
    --output text 2>/dev/null || echo "")

if [ "$VPC_CHECK" == "None" ] || [ -z "$VPC_CHECK" ]; then
    print_info "No existing VPC found - will create new one"
else
    print_warning "VPC already exists: $VPC_CHECK"
fi

# Test 3: Try to create a VPC (will not fail if exists)
print_info "Test 3: Creating test VPC..."

VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-vpc-${ENVIRONMENT}" \
    --query 'Vpcs[0].VpcId' \
    --output text 2>/dev/null || echo "")

if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
    print_info "Creating new VPC..."
    VPC_ID=$(aws ec2 create-vpc \
        --cidr-block "$VPC_CIDR" \
        --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT_NAME}-vpc-${ENVIRONMENT}}]" \
        --query 'Vpc.VpcId' \
        --output text)
    
    if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
        print_error "Failed to create VPC"
        exit 1
    fi
    
    print_success "VPC created: $VPC_ID"
    
    # Enable DNS
    aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-hostnames
    aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-support
    print_success "DNS enabled for VPC"
else
    print_success "Using existing VPC: $VPC_ID"
fi

# Test 4: Save to env file
print_info "Test 4: Saving VPC info..."
cat > "${SCRIPT_DIR}/vpc-test-info.env" << EOF
VPC_ID="$VPC_ID"
EOF

print_success "VPC info saved to vpc-test-info.env"

print_success ""
print_success "All tests passed! AWS CLI is working correctly."
print_info "VPC ID: $VPC_ID"
print_info ""
print_info "You can now run: bash infra-setup.sh"
