#!/bin/bash
# =============================================================================
# Setup ElastiCache Redis
# =============================================================================
# Creates:
# - Redis subnet group in private subnets
# - Redis cluster with TLS and AUTH enabled
# - Updates Secrets Manager with endpoint
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/vpc-info.env"
source "${SCRIPT_DIR}/sg-info.env"
source "${SCRIPT_DIR}/secrets-info.env"

print_info "=========================================="
print_info "Setting up ElastiCache Redis"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Get Redis AUTH Token from Secrets Manager
# -----------------------------------------------------------------------------
print_info "Retrieving Redis AUTH token from Secrets Manager..."

REDIS_AUTH_TOKEN=$(aws secretsmanager get-secret-value \
    --secret-id "$SECRET_REDIS_AUTH" \
    --query 'SecretString' \
    --output text)

# -----------------------------------------------------------------------------
# Create Redis Subnet Group
# -----------------------------------------------------------------------------
print_info "Creating Redis subnet group..."

aws elasticache create-cache-subnet-group \
    --cache-subnet-group-name "${PROJECT_NAME}-redis-subnet-group-${ENVIRONMENT}" \
    --cache-subnet-group-description "Subnet group for ${PROJECT_NAME} Redis ${ENVIRONMENT}" \
    --subnet-ids "$PRIVATE_SUBNET_1_ID" "$PRIVATE_SUBNET_2_ID" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || print_warning "Redis subnet group already exists"

print_success "Redis subnet group created/exists"

# -----------------------------------------------------------------------------
# Create Redis Cluster
# -----------------------------------------------------------------------------
print_info "Creating Redis cluster..."
print_info "This may take 5-10 minutes..."

aws elasticache create-cache-cluster \
    --cache-cluster-id "$REDIS_CLUSTER_ID" \
    --cache-node-type "$REDIS_NODE_TYPE" \
    --engine redis \
    --engine-version "$REDIS_ENGINE_VERSION" \
    --num-cache-nodes "$REDIS_NUM_CACHE_NODES" \
    --cache-subnet-group-name "${PROJECT_NAME}-redis-subnet-group-${ENVIRONMENT}" \
    --security-group-ids "$REDIS_SG_ID" \
    --auth-token "$REDIS_AUTH_TOKEN" \
    --transit-encryption-enabled \
    --snapshot-retention-limit 5 \
    --preferred-maintenance-window "sun:05:00-sun:06:00" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || print_warning "Redis cluster already exists or creation in progress"

print_info "Waiting for Redis cluster to become available..."
aws elasticache wait cache-cluster-available --cache-cluster-id "$REDIS_CLUSTER_ID"

print_success "Redis cluster is now available!"

# -----------------------------------------------------------------------------
# Get Redis Endpoint
# -----------------------------------------------------------------------------
print_info "Retrieving Redis endpoint..."

REDIS_ENDPOINT=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id "$REDIS_CLUSTER_ID" \
    --show-cache-node-info \
    --query 'CacheClusters[0].CacheNodes[0].Endpoint.Address' \
    --output text)

REDIS_PORT=$(aws elasticache describe-cache-clusters \
    --cache-cluster-id "$REDIS_CLUSTER_ID" \
    --show-cache-node-info \
    --query 'CacheClusters[0].CacheNodes[0].Endpoint.Port' \
    --output text)

print_success "Redis Endpoint: $REDIS_ENDPOINT:$REDIS_PORT"

# -----------------------------------------------------------------------------
# Save Redis Information
# -----------------------------------------------------------------------------
REDIS_INFO_FILE="${SCRIPT_DIR}/redis-info.env"
cat > "$REDIS_INFO_FILE" <<EOF
# ElastiCache Redis Information
export REDIS_CLUSTER_ID="$REDIS_CLUSTER_ID"
export REDIS_ENDPOINT="$REDIS_ENDPOINT"
export REDIS_PORT="$REDIS_PORT"
export REDIS_URL="rediss://:****@${REDIS_ENDPOINT}:${REDIS_PORT}/0"
EOF

print_success "Redis information saved to: $REDIS_INFO_FILE"

print_success "=========================================="
print_success "Redis setup completed successfully!"
print_success "=========================================="
print_info "Connection: rediss://:****@${REDIS_ENDPOINT}:${REDIS_PORT}/0"
print_warning "Remember: TLS is enabled, use 'rediss://' scheme"
