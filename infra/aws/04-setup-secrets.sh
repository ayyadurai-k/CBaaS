#!/bin/bash
# =============================================================================
# Setup Secrets Manager
# =============================================================================
# Creates secrets for:
# - Django SECRET_KEY
# - RDS database credentials
# - Redis AUTH token
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"

print_info "=========================================="
print_info "Setting up AWS Secrets Manager"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create Django Secret Key
# -----------------------------------------------------------------------------
print_info "Creating Django secret key..."

DJANGO_SECRET_VALUE=$(generate_password)

aws secretsmanager create-secret \
    --name "$SECRET_DJANGO_SECRET" \
    --description "Django SECRET_KEY for ${PROJECT_NAME} ${ENVIRONMENT}" \
    --secret-string "$DJANGO_SECRET_VALUE" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "$SECRET_DJANGO_SECRET" \
        --secret-string "$DJANGO_SECRET_VALUE"

print_success "Django secret key created/updated: $SECRET_DJANGO_SECRET"

# -----------------------------------------------------------------------------
# Create RDS Database Credentials
# -----------------------------------------------------------------------------
print_info "Creating RDS database credentials..."

DB_PASSWORD=$(generate_password)

DB_CREDENTIALS=$(cat <<EOF
{
    "username": "$RDS_MASTER_USERNAME",
    "password": "$DB_PASSWORD",
    "engine": "$RDS_ENGINE",
    "host": "PENDING",
    "port": 5432,
    "dbname": "$RDS_DB_NAME"
}
EOF
)

aws secretsmanager create-secret \
    --name "$SECRET_DB_CREDENTIALS" \
    --description "RDS database credentials for ${PROJECT_NAME} ${ENVIRONMENT}" \
    --secret-string "$DB_CREDENTIALS" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "$SECRET_DB_CREDENTIALS" \
        --secret-string "$DB_CREDENTIALS"

print_success "Database credentials created/updated: $SECRET_DB_CREDENTIALS"

# -----------------------------------------------------------------------------
# Create Redis AUTH Token
# -----------------------------------------------------------------------------
print_info "Creating Redis AUTH token..."

REDIS_AUTH_TOKEN=$(generate_password)

aws secretsmanager create-secret \
    --name "$SECRET_REDIS_AUTH" \
    --description "Redis AUTH token for ${PROJECT_NAME} ${ENVIRONMENT}" \
    --secret-string "$REDIS_AUTH_TOKEN" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || \
    aws secretsmanager update-secret \
        --secret-id "$SECRET_REDIS_AUTH" \
        --secret-string "$REDIS_AUTH_TOKEN"

print_success "Redis AUTH token created/updated: $SECRET_REDIS_AUTH"

# -----------------------------------------------------------------------------
# Save Secrets Information
# -----------------------------------------------------------------------------
SECRETS_INFO_FILE="${SCRIPT_DIR}/secrets-info.env"
cat > "$SECRETS_INFO_FILE" <<EOF
# AWS Secrets Manager Secret Names
export SECRET_DJANGO_SECRET="$SECRET_DJANGO_SECRET"
export SECRET_DB_CREDENTIALS="$SECRET_DB_CREDENTIALS"
export SECRET_REDIS_AUTH="$SECRET_REDIS_AUTH"
export RDS_MASTER_USERNAME="$RDS_MASTER_USERNAME"
EOF

print_success "Secrets information saved to: $SECRETS_INFO_FILE"

print_success "=========================================="
print_success "Secrets Manager setup completed!"
print_success "=========================================="
print_warning "IMPORTANT: Database host will be updated after RDS creation"
