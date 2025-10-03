#!/bin/bash
# =============================================================================
# Setup VPC and Network Infrastructure
# =============================================================================
# Creates:
# - VPC with DNS support
# - 2 Public subnets (for ALB, NAT Gateways)
# - 2 Private subnets (for ECS, RDS, Redis)
# - Internet Gateway
# - 2 NAT Gateways (one per AZ for HA)
# - Route tables and associations
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

# Helper function to create or get existing resource
get_or_create_resource() {
    local resource_type=$1
    local describe_cmd=$2
    local create_cmd=$3
    local resource_name=$4
    
    # Try to find existing resource
    local resource_id=$(eval "$describe_cmd" 2>/dev/null || echo "")
    
    if [ "$resource_id" == "None" ] || [ -z "$resource_id" ]; then
        # Resource doesn't exist, create it
        resource_id=$(eval "$create_cmd")
        if [ "$resource_id" == "None" ] || [ -z "$resource_id" ]; then
            print_error "Failed to create $resource_type: $resource_name"
            exit 1
        fi
        print_success "$resource_type created: $resource_id"
    else
        print_warning "$resource_type already exists: $resource_id"
    fi
    
    echo "$resource_id"
}

print_info "=========================================="
print_info "Setting up VPC and Network Infrastructure"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create VPC
# -----------------------------------------------------------------------------
print_info "Creating VPC..."

# Check if VPC already exists
VPC_ID=$(aws ec2 describe-vpcs \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-vpc-${ENVIRONMENT}" \
    --query 'Vpcs[0].VpcId' \
    --output text 2>/dev/null)

if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
    # Create new VPC
    VPC_ID=$(aws ec2 create-vpc \
        --cidr-block "$VPC_CIDR" \
        --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=${PROJECT_NAME}-vpc-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
        --query 'Vpc.VpcId' \
        --output text)
    print_success "VPC created: $VPC_ID"
else
    print_warning "VPC already exists: $VPC_ID"
fi

# Verify VPC ID is valid
if [ "$VPC_ID" == "None" ] || [ -z "$VPC_ID" ]; then
    print_error "Failed to create or find VPC"
    exit 1
fi

print_success "VPC ID: $VPC_ID"

# Enable DNS hostnames and DNS support
aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-hostnames
aws ec2 modify-vpc-attribute --vpc-id "$VPC_ID" --enable-dns-support

# -----------------------------------------------------------------------------
# Create Internet Gateway
# -----------------------------------------------------------------------------
print_info "Creating Internet Gateway..."

# Check if IGW already exists
IGW_ID=$(aws ec2 describe-internet-gateways \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-igw-${ENVIRONMENT}" \
    --query 'InternetGateways[0].InternetGatewayId' \
    --output text 2>/dev/null)

if [ "$IGW_ID" == "None" ] || [ -z "$IGW_ID" ]; then
    # Create new IGW
    IGW_ID=$(aws ec2 create-internet-gateway \
        --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-igw-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
        --query 'InternetGateway.InternetGatewayId' \
        --output text)
    print_success "Internet Gateway created: $IGW_ID"
else
    print_warning "Internet Gateway already exists: $IGW_ID"
fi

print_success "Internet Gateway ID: $IGW_ID"

# Attach IGW to VPC (idempotent)
aws ec2 attach-internet-gateway --vpc-id "$VPC_ID" --internet-gateway-id "$IGW_ID" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Create Public Subnets
# -----------------------------------------------------------------------------
print_info "Creating public subnets..."

# Public Subnet 1
PUBLIC_SUBNET_1_ID=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-public-1-${ENVIRONMENT}" \
    --query 'Subnets[0].SubnetId' \
    --output text 2>/dev/null)

if [ "$PUBLIC_SUBNET_1_ID" == "None" ] || [ -z "$PUBLIC_SUBNET_1_ID" ]; then
    PUBLIC_SUBNET_1_ID=$(aws ec2 create-subnet \
        --vpc-id "$VPC_ID" \
        --cidr-block "$PUBLIC_SUBNET_1_CIDR" \
        --availability-zone "$AVAILABILITY_ZONE_1" \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-1-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}},{Key=Type,Value=public}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    print_success "Public subnet 1 created: $PUBLIC_SUBNET_1_ID"
else
    print_warning "Public subnet 1 already exists: $PUBLIC_SUBNET_1_ID"
fi

# Public Subnet 2
PUBLIC_SUBNET_2_ID=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-public-2-${ENVIRONMENT}" \
    --query 'Subnets[0].SubnetId' \
    --output text 2>/dev/null)

if [ "$PUBLIC_SUBNET_2_ID" == "None" ] || [ -z "$PUBLIC_SUBNET_2_ID" ]; then
    PUBLIC_SUBNET_2_ID=$(aws ec2 create-subnet \
        --vpc-id "$VPC_ID" \
        --cidr-block "$PUBLIC_SUBNET_2_CIDR" \
        --availability-zone "$AVAILABILITY_ZONE_2" \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-2-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}},{Key=Type,Value=public}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    print_success "Public subnet 2 created: $PUBLIC_SUBNET_2_ID"
else
    print_warning "Public subnet 2 already exists: $PUBLIC_SUBNET_2_ID"
fi

print_success "Public Subnet 1 ID: $PUBLIC_SUBNET_1_ID"
print_success "Public Subnet 2 ID: $PUBLIC_SUBNET_2_ID"

# Enable auto-assign public IP
aws ec2 modify-subnet-attribute --subnet-id "$PUBLIC_SUBNET_1_ID" --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id "$PUBLIC_SUBNET_2_ID" --map-public-ip-on-launch

# -----------------------------------------------------------------------------
# Create Private Subnets
# -----------------------------------------------------------------------------
print_info "Creating private subnets..."

# Private Subnet 1
PRIVATE_SUBNET_1_ID=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-private-1-${ENVIRONMENT}" \
    --query 'Subnets[0].SubnetId' \
    --output text 2>/dev/null)

if [ "$PRIVATE_SUBNET_1_ID" == "None" ] || [ -z "$PRIVATE_SUBNET_1_ID" ]; then
    PRIVATE_SUBNET_1_ID=$(aws ec2 create-subnet \
        --vpc-id "$VPC_ID" \
        --cidr-block "$PRIVATE_SUBNET_1_CIDR" \
        --availability-zone "$AVAILABILITY_ZONE_1" \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-1-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}},{Key=Type,Value=private}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    print_success "Private subnet 1 created: $PRIVATE_SUBNET_1_ID"
else
    print_warning "Private subnet 1 already exists: $PRIVATE_SUBNET_1_ID"
fi

# Private Subnet 2
PRIVATE_SUBNET_2_ID=$(aws ec2 describe-subnets \
    --filters "Name=tag:Name,Values=${PROJECT_NAME}-private-2-${ENVIRONMENT}" \
    --query 'Subnets[0].SubnetId' \
    --output text 2>/dev/null)

if [ "$PRIVATE_SUBNET_2_ID" == "None" ] || [ -z "$PRIVATE_SUBNET_2_ID" ]; then
    PRIVATE_SUBNET_2_ID=$(aws ec2 create-subnet \
        --vpc-id "$VPC_ID" \
        --cidr-block "$PRIVATE_SUBNET_2_CIDR" \
        --availability-zone "$AVAILABILITY_ZONE_2" \
        --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-2-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}},{Key=Type,Value=private}]" \
        --query 'Subnet.SubnetId' \
        --output text)
    print_success "Private subnet 2 created: $PRIVATE_SUBNET_2_ID"
else
    print_warning "Private subnet 2 already exists: $PRIVATE_SUBNET_2_ID"
fi

print_success "Private Subnet 1 ID: $PRIVATE_SUBNET_1_ID"
print_success "Private Subnet 2 ID: $PRIVATE_SUBNET_2_ID"

# -----------------------------------------------------------------------------
# Create NAT Gateways
# -----------------------------------------------------------------------------
print_info "Allocating Elastic IPs for NAT Gateways..."

EIP_1_ID=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-eip-1-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'AllocationId' \
    --output text 2>/dev/null || \
    aws ec2 describe-addresses \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-nat-eip-1-${ENVIRONMENT}" \
        --query 'Addresses[0].AllocationId' \
        --output text)

EIP_2_ID=$(aws ec2 allocate-address \
    --domain vpc \
    --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-eip-2-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'AllocationId' \
    --output text 2>/dev/null || \
    aws ec2 describe-addresses \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-nat-eip-2-${ENVIRONMENT}" \
        --query 'Addresses[0].AllocationId' \
        --output text)

print_success "EIP 1 ID: $EIP_1_ID"
print_success "EIP 2 ID: $EIP_2_ID"

print_info "Creating NAT Gateways..."

NAT_GW_1_ID=$(aws ec2 create-nat-gateway \
    --subnet-id "$PUBLIC_SUBNET_1_ID" \
    --allocation-id "$EIP_1_ID" \
    --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-1-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'NatGateway.NatGatewayId' \
    --output text 2>/dev/null || \
    aws ec2 describe-nat-gateways \
        --filter "Name=tag:Name,Values=${PROJECT_NAME}-nat-1-${ENVIRONMENT}" "Name=state,Values=available,pending" \
        --query 'NatGateways[0].NatGatewayId' \
        --output text)

NAT_GW_2_ID=$(aws ec2 create-nat-gateway \
    --subnet-id "$PUBLIC_SUBNET_2_ID" \
    --allocation-id "$EIP_2_ID" \
    --tag-specifications "ResourceType=natgateway,Tags=[{Key=Name,Value=${PROJECT_NAME}-nat-2-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'NatGateway.NatGatewayId' \
    --output text 2>/dev/null || \
    aws ec2 describe-nat-gateways \
        --filter "Name=tag:Name,Values=${PROJECT_NAME}-nat-2-${ENVIRONMENT}" "Name=state,Values=available,pending" \
        --query 'NatGateways[0].NatGatewayId' \
        --output text)

print_success "NAT Gateway 1 ID: $NAT_GW_1_ID"
print_success "NAT Gateway 2 ID: $NAT_GW_2_ID"

print_info "Waiting for NAT Gateways to become available..."
aws ec2 wait nat-gateway-available --nat-gateway-ids "$NAT_GW_1_ID" "$NAT_GW_2_ID"
print_success "NAT Gateways are now available"

# -----------------------------------------------------------------------------
# Create Route Tables
# -----------------------------------------------------------------------------
print_info "Creating route tables..."

# Public route table
PUBLIC_RT_ID=$(aws ec2 create-route-table \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-public-rt-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'RouteTable.RouteTableId' \
    --output text 2>/dev/null || \
    aws ec2 describe-route-tables \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-public-rt-${ENVIRONMENT}" \
        --query 'RouteTables[0].RouteTableId' \
        --output text)

# Private route tables (one per AZ)
PRIVATE_RT_1_ID=$(aws ec2 create-route-table \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-rt-1-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'RouteTable.RouteTableId' \
    --output text 2>/dev/null || \
    aws ec2 describe-route-tables \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-private-rt-1-${ENVIRONMENT}" \
        --query 'RouteTables[0].RouteTableId' \
        --output text)

PRIVATE_RT_2_ID=$(aws ec2 create-route-table \
    --vpc-id "$VPC_ID" \
    --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=${PROJECT_NAME}-private-rt-2-${ENVIRONMENT}},{Key=${TAG_PROJECT}},{Key=${TAG_ENVIRONMENT}},{Key=${TAG_MANAGED_BY}}]" \
    --query 'RouteTable.RouteTableId' \
    --output text 2>/dev/null || \
    aws ec2 describe-route-tables \
        --filters "Name=tag:Name,Values=${PROJECT_NAME}-private-rt-2-${ENVIRONMENT}" \
        --query 'RouteTables[0].RouteTableId' \
        --output text)

print_success "Public Route Table ID: $PUBLIC_RT_ID"
print_success "Private Route Table 1 ID: $PRIVATE_RT_1_ID"
print_success "Private Route Table 2 ID: $PRIVATE_RT_2_ID"

# -----------------------------------------------------------------------------
# Create Routes
# -----------------------------------------------------------------------------
print_info "Creating routes..."

# Public route to Internet Gateway
aws ec2 create-route \
    --route-table-id "$PUBLIC_RT_ID" \
    --destination-cidr-block "0.0.0.0/0" \
    --gateway-id "$IGW_ID" 2>/dev/null || true

# Private routes to NAT Gateways
aws ec2 create-route \
    --route-table-id "$PRIVATE_RT_1_ID" \
    --destination-cidr-block "0.0.0.0/0" \
    --nat-gateway-id "$NAT_GW_1_ID" 2>/dev/null || true

aws ec2 create-route \
    --route-table-id "$PRIVATE_RT_2_ID" \
    --destination-cidr-block "0.0.0.0/0" \
    --nat-gateway-id "$NAT_GW_2_ID" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Associate Route Tables with Subnets
# -----------------------------------------------------------------------------
print_info "Associating route tables with subnets..."

aws ec2 associate-route-table --subnet-id "$PUBLIC_SUBNET_1_ID" --route-table-id "$PUBLIC_RT_ID" 2>/dev/null || true
aws ec2 associate-route-table --subnet-id "$PUBLIC_SUBNET_2_ID" --route-table-id "$PUBLIC_RT_ID" 2>/dev/null || true
aws ec2 associate-route-table --subnet-id "$PRIVATE_SUBNET_1_ID" --route-table-id "$PRIVATE_RT_1_ID" 2>/dev/null || true
aws ec2 associate-route-table --subnet-id "$PRIVATE_SUBNET_2_ID" --route-table-id "$PRIVATE_RT_2_ID" 2>/dev/null || true

# -----------------------------------------------------------------------------
# Save VPC Information to File
# -----------------------------------------------------------------------------
VPC_INFO_FILE="${SCRIPT_DIR}/vpc-info.env"
cat > "$VPC_INFO_FILE" <<EOF
# VPC Infrastructure IDs
export VPC_ID="$VPC_ID"
export IGW_ID="$IGW_ID"
export PUBLIC_SUBNET_1_ID="$PUBLIC_SUBNET_1_ID"
export PUBLIC_SUBNET_2_ID="$PUBLIC_SUBNET_2_ID"
export PRIVATE_SUBNET_1_ID="$PRIVATE_SUBNET_1_ID"
export PRIVATE_SUBNET_2_ID="$PRIVATE_SUBNET_2_ID"
export NAT_GW_1_ID="$NAT_GW_1_ID"
export NAT_GW_2_ID="$NAT_GW_2_ID"
export PUBLIC_RT_ID="$PUBLIC_RT_ID"
export PRIVATE_RT_1_ID="$PRIVATE_RT_1_ID"
export PRIVATE_RT_2_ID="$PRIVATE_RT_2_ID"
EOF

print_success "VPC information saved to: $VPC_INFO_FILE"

print_success "=========================================="
print_success "VPC setup completed successfully!"
print_success "=========================================="
