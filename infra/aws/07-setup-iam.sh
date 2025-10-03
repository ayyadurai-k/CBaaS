#!/bin/bash
# =============================================================================
# Setup IAM Roles and Policies
# =============================================================================
# Creates IAM roles for:
# - ECS Task Execution (pull images, get secrets, write logs)
# - ECS Task (S3 access for static/media files)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/s3-info.env"
source "${SCRIPT_DIR}/secrets-info.env"

print_info "=========================================="
print_info "Setting up IAM Roles and Policies"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create ECS Task Execution Role
# -----------------------------------------------------------------------------
print_info "Creating ECS Task Execution Role..."

TRUST_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {
            "Service": "ecs-tasks.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
    }]
}
EOF
)

ECS_EXECUTION_ROLE_NAME="${PROJECT_NAME}-ecs-execution-role-${ENVIRONMENT}"

aws iam create-role \
    --role-name "$ECS_EXECUTION_ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || print_warning "ECS execution role already exists"

# Attach AWS managed policy for ECS task execution
aws iam attach-role-policy \
    --role-name "$ECS_EXECUTION_ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" \
    2>/dev/null || true

# Create custom policy for Secrets Manager and CloudWatch Logs
EXECUTION_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${SECRET_DJANGO_SECRET}*",
                "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${SECRET_DB_CREDENTIALS}*",
                "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${SECRET_REDIS_AUTH}*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
EOF
)

EXECUTION_POLICY_NAME="${PROJECT_NAME}-ecs-execution-policy-${ENVIRONMENT}"

aws iam create-policy \
    --policy-name "$EXECUTION_POLICY_NAME" \
    --policy-document "$EXECUTION_POLICY" \
    2>/dev/null || print_warning "ECS execution policy already exists"

EXECUTION_POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${EXECUTION_POLICY_NAME}"

aws iam attach-role-policy \
    --role-name "$ECS_EXECUTION_ROLE_NAME" \
    --policy-arn "$EXECUTION_POLICY_ARN" \
    2>/dev/null || true

ECS_EXECUTION_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ECS_EXECUTION_ROLE_NAME}"
print_success "ECS Execution Role ARN: $ECS_EXECUTION_ROLE_ARN"

# -----------------------------------------------------------------------------
# Create ECS Task Role
# -----------------------------------------------------------------------------
print_info "Creating ECS Task Role..."

ECS_TASK_ROLE_NAME="${PROJECT_NAME}-ecs-task-role-${ENVIRONMENT}"

aws iam create-role \
    --role-name "$ECS_TASK_ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    2>/dev/null || print_warning "ECS task role already exists"

# Create policy for S3 access (static and media buckets)
TASK_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::${S3_STATIC_BUCKET}",
                "arn:aws:s3:::${S3_STATIC_BUCKET}/*",
                "arn:aws:s3:::${S3_MEDIA_BUCKET}",
                "arn:aws:s3:::${S3_MEDIA_BUCKET}/*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${SECRET_DJANGO_SECRET}*",
                "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${SECRET_DB_CREDENTIALS}*",
                "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${SECRET_REDIS_AUTH}*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "ses:SendEmail",
                "ses:SendRawEmail"
            ],
            "Resource": "*"
        }
    ]
}
EOF
)

TASK_POLICY_NAME="${PROJECT_NAME}-ecs-task-policy-${ENVIRONMENT}"

aws iam create-policy \
    --policy-name "$TASK_POLICY_NAME" \
    --policy-document "$TASK_POLICY" \
    2>/dev/null || print_warning "ECS task policy already exists"

TASK_POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${TASK_POLICY_NAME}"

aws iam attach-role-policy \
    --role-name "$ECS_TASK_ROLE_NAME" \
    --policy-arn "$TASK_POLICY_ARN" \
    2>/dev/null || true

ECS_TASK_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ECS_TASK_ROLE_NAME}"
print_success "ECS Task Role ARN: $ECS_TASK_ROLE_ARN"

# -----------------------------------------------------------------------------
# Save IAM Information
# -----------------------------------------------------------------------------
IAM_INFO_FILE="${SCRIPT_DIR}/iam-info.env"
cat > "$IAM_INFO_FILE" <<EOF
# IAM Role ARNs
export ECS_EXECUTION_ROLE_ARN="$ECS_EXECUTION_ROLE_ARN"
export ECS_TASK_ROLE_ARN="$ECS_TASK_ROLE_ARN"
export ECS_EXECUTION_ROLE_NAME="$ECS_EXECUTION_ROLE_NAME"
export ECS_TASK_ROLE_NAME="$ECS_TASK_ROLE_NAME"
EOF

print_success "IAM information saved to: $IAM_INFO_FILE"

print_success "=========================================="
print_success "IAM roles setup completed!"
print_success "=========================================="
