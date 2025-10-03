#!/bin/bash
# =============================================================================
# Setup RDS PostgreSQL Database
# =============================================================================
# Creates:
# - DB subnet group in private subnets
# - RDS PostgreSQL instance (Multi-AZ)
# - Automated backups enabled
# - Updates Secrets Manager with endpoint
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/vpc-info.env"
source "${SCRIPT_DIR}/sg-info.env"
source "${SCRIPT_DIR}/secrets-info.env"

print_info "=========================================="
print_info "Setting up RDS PostgreSQL Database"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create DB Subnet Group
# -----------------------------------------------------------------------------
print_info "Creating DB subnet group..."

aws rds create-db-subnet-group \
    --db-subnet-group-name "${PROJECT_NAME}-db-subnet-group-${ENVIRONMENT}" \
    --db-subnet-group-description "Subnet group for ${PROJECT_NAME} RDS ${ENVIRONMENT}" \
    --subnet-ids "$PRIVATE_SUBNET_1_ID" "$PRIVATE_SUBNET_2_ID" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || print_warning "DB subnet group already exists"

print_success "DB subnet group created/exists"

# -----------------------------------------------------------------------------
# Get Database Password from Secrets Manager
# -----------------------------------------------------------------------------
print_info "Retrieving database password from Secrets Manager..."

DB_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_DB_CREDENTIALS" \
    --query 'SecretString' \
    --output text | jq -r '.password')

# -----------------------------------------------------------------------------
# Create RDS Instance
# -----------------------------------------------------------------------------
print_info "Creating RDS PostgreSQL instance..."
print_info "This may take 10-15 minutes..."

aws rds create-db-instance \
    --db-instance-identifier "$RDS_INSTANCE_ID" \
    --db-instance-class "$RDS_INSTANCE_CLASS" \
    --engine "$RDS_ENGINE" \
    --engine-version "$RDS_ENGINE_VERSION" \
    --master-username "$RDS_MASTER_USERNAME" \
    --master-user-password "$DB_PASSWORD" \
    --allocated-storage "$RDS_ALLOCATED_STORAGE" \
    --storage-type gp3 \
    --storage-encrypted \
    --db-name "$RDS_DB_NAME" \
    --vpc-security-group-ids "$RDS_SG_ID" \
    --db-subnet-group-name "${PROJECT_NAME}-db-subnet-group-${ENVIRONMENT}" \
    --multi-az \
    --backup-retention-period 7 \
    --preferred-backup-window "03:00-04:00" \
    --preferred-maintenance-window "mon:04:00-mon:05:00" \
    --enable-cloudwatch-logs-exports '["postgresql"]' \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    --no-publicly-accessible \
    --deletion-protection \
    2>/dev/null || print_warning "RDS instance already exists or creation in progress"

print_info "Waiting for RDS instance to become available..."
aws rds wait db-instance-available --db-instance-identifier "$RDS_INSTANCE_ID"

print_success "RDS instance is now available!"

# -----------------------------------------------------------------------------
# Get RDS Endpoint
# -----------------------------------------------------------------------------
print_info "Retrieving RDS endpoint..."

RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$RDS_INSTANCE_ID" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text)

print_success "RDS Endpoint: $RDS_ENDPOINT"

# -----------------------------------------------------------------------------
# Update Secrets Manager with RDS Endpoint
# -----------------------------------------------------------------------------
print_info "Updating Secrets Manager with RDS endpoint..."

DB_CREDENTIALS=$(cat <<EOF
{
    "username": "$RDS_MASTER_USERNAME",
    "password": "$DB_PASSWORD",
    "engine": "$RDS_ENGINE",
    "host": "$RDS_ENDPOINT",
    "port": 5432,
    "dbname": "$RDS_DB_NAME"
}
EOF
)

aws secretsmanager update-secret \
    --secret-id "$SECRET_DB_CREDENTIALS" \
    --secret-string "$DB_CREDENTIALS"

print_success "Secrets Manager updated with RDS endpoint"

# -----------------------------------------------------------------------------
# Save RDS Information
# -----------------------------------------------------------------------------
RDS_INFO_FILE="${SCRIPT_DIR}/rds-info.env"
cat > "$RDS_INFO_FILE" <<EOF
# RDS PostgreSQL Information
export RDS_INSTANCE_ID="$RDS_INSTANCE_ID"
export RDS_ENDPOINT="$RDS_ENDPOINT"
export RDS_DB_NAME="$RDS_DB_NAME"
export RDS_MASTER_USERNAME="$RDS_MASTER_USERNAME"
export RDS_PORT="5432"
EOF

print_success "RDS information saved to: $RDS_INFO_FILE"

print_success "=========================================="
print_success "RDS setup completed successfully!"
print_success "=========================================="
print_info "Connection string: postgresql://${RDS_MASTER_USERNAME}:****@${RDS_ENDPOINT}:5432/${RDS_DB_NAME}"
