#!/bin/bash

##############################################################################
# AWS Backend Infrastructure Setup Script for CBaaS Django Deployment
# 
# This script sets up:
# 1. ECR repository for Docker images
# 2. VPC, Subnets, Security Groups (if not existing)
# 3. RDS PostgreSQL instance
# 4. ECS Cluster (Fargate)
# 5. Application Load Balancer with    # Attach AWS managed policy for ECS task execution
    aws iam attach-role-policy \
        --role-name "$TASK_EXEC_ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    
    # Custom policy for Secrets Manager and CloudWatch Logs access
    cat > temp-secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${PROJECT_NAME}/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "logs:CreateLogGroup"
      ],
      "Resource": "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:log-group:/ecs/${PROJECT_NAME}-*"
    }
  ]
}
EOFes and OIDC provider for GitHub Actions
# 7. AWS Secrets Manager for environment variables
#
# Usage: ./setup-aws-backend.sh <project-name> <aws-account-id> [domain]
# Example: ./setup-aws-backend.sh cbaas 577897067437 api.cbaas.com
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
if [ $# -lt 2 ] || [ $# -gt 3 ]; then
    log_error "Usage: $0 <project-name> <aws-account-id> [domain]"
    log_error "Example: $0 cbaas 577897067437 api.cbaas.com"
    exit 1
fi

PROJECT_NAME=$1
AWS_ACCOUNT_ID=$2
DOMAIN=${3:-""}
AWS_REGION="ap-south-1"
CLUSTER_NAME="${PROJECT_NAME}-cluster"
SERVICE_NAME="${PROJECT_NAME}-backend-service"
ECR_REPO="${PROJECT_NAME}-backend"
ROLE_NAME="GitHubActionsBackendDeployRole"

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

log_info "Starting AWS backend infrastructure setup..."
log_info "Project: $PROJECT_NAME"
log_info "Region: $AWS_REGION"
log_info "Account ID: $AWS_ACCOUNT_ID"
log_info "Domain: ${DOMAIN:-"None (will use ALB DNS)"}"

# Step 1: Create ECR repository
log_step "Creating ECR repository..."
if aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$AWS_REGION" &>/dev/null; then
    log_warn "ECR repository $ECR_REPO already exists"
else
    aws ecr create-repository \
        --repository-name "$ECR_REPO" \
        --region "$AWS_REGION" \
        --image-scanning-configuration scanOnPush=true
    log_info "ECR repository created: $ECR_REPO"
fi

ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"

# Step 2: Create VPC and networking (if not exists)
log_step "Setting up VPC and networking..."

# Check if default VPC exists
DEFAULT_VPC=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text 2>/dev/null || echo "None")

if [ "$DEFAULT_VPC" != "None" ] && [ "$DEFAULT_VPC" != "null" ]; then
    VPC_ID="$DEFAULT_VPC"
    log_info "Using existing default VPC: $VPC_ID"
    
    # Get default subnets
    SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[*].SubnetId' --output text)
    SUBNET_ID_1=$(echo $SUBNET_IDS | cut -d' ' -f1)
    SUBNET_ID_2=$(echo $SUBNET_IDS | cut -d' ' -f2)
    
    if [ -z "$SUBNET_ID_2" ]; then
        SUBNET_ID_2="$SUBNET_ID_1"
        log_warn "Only one subnet available, using same for both AZ requirements"
    fi
else
    log_error "No default VPC found. Please create VPC manually or use existing VPC."
    log_error "This script currently requires a default VPC for simplicity."
    exit 1
fi

# Step 3: Create Security Groups
log_step "Creating security groups..."

# ALB Security Group
ALB_SG_NAME="${PROJECT_NAME}-alb-sg"
ALB_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$ALB_SG_NAME" "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "None")

if [ "$ALB_SG_ID" = "None" ] || [ "$ALB_SG_ID" = "null" ]; then
    ALB_SG_ID=$(aws ec2 create-security-group \
        --group-name "$ALB_SG_NAME" \
        --description "Security group for $PROJECT_NAME ALB" \
        --vpc-id "$VPC_ID" \
        --query 'GroupId' \
        --output text)
    
    # Allow HTTP and HTTPS
    aws ec2 authorize-security-group-ingress \
        --group-id "$ALB_SG_ID" \
        --protocol tcp \
        --port 80 \
        --cidr 0.0.0.0/0
    
    aws ec2 authorize-security-group-ingress \
        --group-id "$ALB_SG_ID" \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0
    
    log_info "ALB security group created: $ALB_SG_ID"
else
    log_warn "ALB security group already exists: $ALB_SG_ID"
fi

# ECS Security Group
ECS_SG_NAME="${PROJECT_NAME}-ecs-sg"
ECS_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$ECS_SG_NAME" "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "None")

if [ "$ECS_SG_ID" = "None" ] || [ "$ECS_SG_ID" = "null" ]; then
    ECS_SG_ID=$(aws ec2 create-security-group \
        --group-name "$ECS_SG_NAME" \
        --description "Security group for $PROJECT_NAME ECS tasks" \
        --vpc-id "$VPC_ID" \
        --query 'GroupId' \
        --output text)
    
    # Allow traffic from ALB
    aws ec2 authorize-security-group-ingress \
        --group-id "$ECS_SG_ID" \
        --protocol tcp \
        --port 8000 \
        --source-group "$ALB_SG_ID"
    
    # Allow outbound HTTPS for ECR/Secrets Manager
    aws ec2 authorize-security-group-egress \
        --group-id "$ECS_SG_ID" \
        --protocol tcp \
        --port 443 \
        --cidr 0.0.0.0/0
    
    log_info "ECS security group created: $ECS_SG_ID"
else
    log_warn "ECS security group already exists: $ECS_SG_ID"
fi

# RDS Security Group
RDS_SG_NAME="${PROJECT_NAME}-rds-sg"
RDS_SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$RDS_SG_NAME" "Name=vpc-id,Values=$VPC_ID" --query 'SecurityGroups[0].GroupId' --output text 2>/dev/null || echo "None")

if [ "$RDS_SG_ID" = "None" ] || [ "$RDS_SG_ID" = "null" ]; then
    RDS_SG_ID=$(aws ec2 create-security-group \
        --group-name "$RDS_SG_NAME" \
        --description "Security group for $PROJECT_NAME RDS" \
        --vpc-id "$VPC_ID" \
        --query 'GroupId' \
        --output text)
    
    # Allow PostgreSQL from ECS
    aws ec2 authorize-security-group-ingress \
        --group-id "$RDS_SG_ID" \
        --protocol tcp \
        --port 5432 \
        --source-group "$ECS_SG_ID"
    
    log_info "RDS security group created: $RDS_SG_ID"
else
    log_warn "RDS security group already exists: $RDS_SG_ID"
fi

# Step 4: Create RDS subnet group
log_step "Creating RDS subnet group..."
DB_SUBNET_GROUP="${PROJECT_NAME}-db-subnet-group"

if aws rds describe-db-subnet-groups --db-subnet-group-name "$DB_SUBNET_GROUP" &>/dev/null; then
    log_warn "RDS subnet group already exists: $DB_SUBNET_GROUP"
else
    aws rds create-db-subnet-group \
        --db-subnet-group-name "$DB_SUBNET_GROUP" \
        --db-subnet-group-description "Subnet group for $PROJECT_NAME RDS" \
        --subnet-ids "$SUBNET_ID_1" "$SUBNET_ID_2"
    log_info "RDS subnet group created: $DB_SUBNET_GROUP"
fi

# Step 5: Create RDS instance
log_step "Creating RDS PostgreSQL instance..."
DB_INSTANCE_ID="${PROJECT_NAME}-postgres"
DB_NAME="${PROJECT_NAME}db"
DB_USERNAME="postgres"
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25) # Generate random password

if aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" &>/dev/null; then
    log_warn "RDS instance already exists: $DB_INSTANCE_ID"
    RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" --query 'DBInstances[0].Endpoint.Address' --output text)
else
    aws rds create-db-instance \
        --db-instance-identifier "$DB_INSTANCE_ID" \
        --db-instance-class db.t4g.micro \
        --engine postgres \
        --engine-version 16.10 \
        --master-username "$DB_USERNAME" \
        --master-user-password "$DB_PASSWORD" \
        --allocated-storage 20 \
        --storage-type gp2 \
        --db-name "$DB_NAME" \
        --vpc-security-group-ids "$RDS_SG_ID" \
        --db-subnet-group-name "$DB_SUBNET_GROUP" \
        --backup-retention-period 7 \
        --no-multi-az \
        --no-publicly-accessible \
        --storage-encrypted
    
    log_info "RDS instance creation initiated: $DB_INSTANCE_ID"
    log_warn "RDS instance will take 5-10 minutes to become available"
    
    # Wait for RDS to be available
    log_info "Waiting for RDS instance to become available..."
    aws rds wait db-instance-available --db-instance-identifier "$DB_INSTANCE_ID"
    
    RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier "$DB_INSTANCE_ID" --query 'DBInstances[0].Endpoint.Address' --output text)
    log_info "RDS instance ready: $RDS_ENDPOINT"
fi

# Step 6: Create Application Load Balancer
log_step "Creating Application Load Balancer..."
ALB_NAME="${PROJECT_NAME}-alb"

ALB_ARN=$(aws elbv2 describe-load-balancers --names "$ALB_NAME" --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null || echo "None")

if [ "$ALB_ARN" != "None" ] && [ "$ALB_ARN" != "null" ]; then
    log_warn "ALB already exists: $ALB_NAME"
else
    ALB_ARN=$(aws elbv2 create-load-balancer \
        --name "$ALB_NAME" \
        --subnets "$SUBNET_ID_1" "$SUBNET_ID_2" \
        --security-groups "$ALB_SG_ID" \
        --scheme internet-facing \
        --type application \
        --query 'LoadBalancers[0].LoadBalancerArn' \
        --output text)
    
    log_info "ALB created: $ALB_NAME"
fi

ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns "$ALB_ARN" --query 'LoadBalancers[0].DNSName' --output text)

# Create target group
TG_NAME="${PROJECT_NAME}-tg"
TG_ARN=$(aws elbv2 describe-target-groups --names "$TG_NAME" --query 'TargetGroups[0].TargetGroupArn' --output text 2>/dev/null || echo "None")

if [ "$TG_ARN" != "None" ] && [ "$TG_ARN" != "null" ]; then
    log_warn "Target group already exists: $TG_NAME"
else
    TG_ARN=$(aws elbv2 create-target-group \
        --name "$TG_NAME" \
        --protocol HTTP \
        --port 8000 \
        --vpc-id "$VPC_ID" \
        --target-type ip \
        --health-check-path "//api//healthz" \
        --health-check-interval-seconds 30 \
        --health-check-timeout-seconds 5 \
        --healthy-threshold-count 2 \
        --unhealthy-threshold-count 3 \
        --query 'TargetGroups[0].TargetGroupArn' \
        --output text)
    
    log_info "Target group created: $TG_NAME"
fi

# Create ALB listener
LISTENER_ARN=$(aws elbv2 describe-listeners --load-balancer-arn "$ALB_ARN" --query 'Listeners[0].ListenerArn' --output text 2>/dev/null || echo "None")

if [ "$LISTENER_ARN" != "None" ] && [ "$LISTENER_ARN" != "null" ]; then
    log_warn "ALB listener already exists"
else
    aws elbv2 create-listener \
        --load-balancer-arn "$ALB_ARN" \
        --protocol HTTP \
        --port 80 \
        --default-actions Type=forward,TargetGroupArn="$TG_ARN"
    
    log_info "ALB listener created (HTTP:80)"
fi

# Step 7: Create ECS Cluster
log_step "Creating ECS cluster..."

if aws ecs describe-clusters --clusters "$CLUSTER_NAME" --query 'clusters[0].clusterName' --output text 2>/dev/null | grep -q "$CLUSTER_NAME"; then
    log_warn "ECS cluster already exists: $CLUSTER_NAME"
else
    aws ecs create-cluster \
        --cluster-name "$CLUSTER_NAME" \
        --capacity-providers FARGATE \
        --default-capacity-provider-strategy capacityProvider=FARGATE,weight=1
    
    log_info "ECS cluster created: $CLUSTER_NAME"
fi

# Step 7.1: Create CloudWatch Log Group
log_step "Creating CloudWatch log group..."
LOG_GROUP_NAME="/ecs/${PROJECT_NAME}-backend"

if aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP_NAME" --query "logGroups[?logGroupName=='$LOG_GROUP_NAME'].logGroupName" --output text | grep -q "$LOG_GROUP_NAME"; then
    log_warn "CloudWatch log group already exists: $LOG_GROUP_NAME"
else
    aws logs create-log-group \
        --log-group-name "$LOG_GROUP_NAME" \
        --retention-in-days 7
    
    log_info "CloudWatch log group created: $LOG_GROUP_NAME"
fi

# Step 8: Create GitHub OIDC provider (if not exists)
log_step "Setting up GitHub OIDC provider..."

if aws iam get-open-id-connect-provider --open-id-connect-provider-arn "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com" &>/dev/null; then
    log_warn "GitHub OIDC provider already exists"
else
    log_info "Creating GitHub OIDC provider..."
    aws iam create-open-id-connect-provider \
        --url "https://token.actions.githubusercontent.com" \
        --thumbprint-list "6938fd4d98bab03faadb97b34396831e3780aea1" \
        --client-id-list "sts.amazonaws.com"
    log_info "GitHub OIDC provider created"
fi

# Step 9: Create IAM roles
log_step "Creating IAM roles..."

# ECS Task Execution Role
TASK_EXEC_ROLE_NAME="${PROJECT_NAME}-task-execution-role"
TASK_EXEC_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${TASK_EXEC_ROLE_NAME}"

if aws iam get-role --role-name "$TASK_EXEC_ROLE_NAME" &>/dev/null; then
    log_warn "Task execution role already exists: $TASK_EXEC_ROLE_NAME"
else
    # Trust policy for ECS tasks
    cat > temp-task-exec-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ecs-tasks.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

    aws iam create-role \
        --role-name "$TASK_EXEC_ROLE_NAME" \
        --assume-role-policy-document file://temp-task-exec-trust.json
    
    # Attach AWS managed policy for ECS task execution
    aws iam attach-role-policy \
        --role-name "$TASK_EXEC_ROLE_NAME" \
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
    
    # Custom policy for Secrets Manager access
    cat > temp-secrets-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:${AWS_REGION}:${AWS_ACCOUNT_ID}:secret:${PROJECT_NAME}/*"
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$TASK_EXEC_ROLE_NAME" \
        --policy-name SecretsManagerAndLogsAccess \
        --policy-document file://temp-secrets-policy.json
    
    rm -f temp-task-exec-trust.json temp-secrets-policy.json
    log_info "Task execution role created: $TASK_EXEC_ROLE_NAME"
fi

# GitHub Actions OIDC Role
if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    log_warn "GitHub Actions role already exists: $ROLE_NAME"
else
    # Trust policy for GitHub OIDC
    cat > temp-github-trust.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::${AWS_ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:ayyadurai-k/CBaaS:ref:refs/heads/release"
        }
      }
    }
  ]
}
EOF

    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document file://temp-github-trust.json
    
    # Permissions for GitHub Actions
    cat > temp-github-permissions.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload",
        "ecr:PutImage"
      ],
      "Resource": [
        "arn:aws:ecr:${AWS_REGION}:${AWS_ACCOUNT_ID}:repository/${ECR_REPO}",
        "*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:DescribeTasks",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "iam:PassRole"
      ],
      "Resource": "${TASK_EXEC_ROLE_ARN}"
    }
  ]
}
EOF

    aws iam put-role-policy \
        --role-name "$ROLE_NAME" \
        --policy-name BackendDeploymentPolicy \
        --policy-document file://temp-github-permissions.json
    
    rm -f temp-github-trust.json temp-github-permissions.json
    log_info "GitHub Actions role created: $ROLE_NAME"
fi

GITHUB_ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"

# Step 10: Create AWS Secrets Manager secret
log_step "Creating AWS Secrets Manager secret..."
SECRET_NAME="${PROJECT_NAME}/backend/env"

if aws secretsmanager describe-secret --secret-id "$SECRET_NAME" &>/dev/null; then
    log_warn "Secret already exists: $SECRET_NAME"
else
    # Generate Django secret key
    DJANGO_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(50))" 2>/dev/null || openssl rand -base64 50)
    
    # Database URL
    DATABASE_URL="postgres://${DB_USERNAME}:${DB_PASSWORD}@${RDS_ENDPOINT}:5432/${DB_NAME}"
    
    # Create secret
    cat > temp-secrets.json <<EOF
{
  "DJANGO_SECRET_KEY": "${DJANGO_SECRET_KEY}",
  "DEBUG": "False",
  "ALLOWED_HOSTS": "${ALB_DNS}${DOMAIN:+,$DOMAIN}",
  "DATABASE_URL": "${DATABASE_URL}",
  "CORS_ALLOWED_ORIGINS": "https://${DOMAIN:-$ALB_DNS}",
  "CORS_ALLOW_CREDENTIALS": "True"
}
EOF

    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --description "Environment variables for $PROJECT_NAME backend" \
        --secret-string file://temp-secrets.json
    
    rm -f temp-secrets.json
    log_info "Secrets Manager secret created: $SECRET_NAME"
fi

# Step 11: Output summary
echo ""
echo "======================================================================"
log_info "✅ AWS Backend Infrastructure Setup Complete!"
echo "======================================================================"
echo ""
echo "📋 Infrastructure Summary:"
echo "  ECR Repository: ${ECR_URI}"
echo "  ECS Cluster: ${CLUSTER_NAME}"
echo "  ECS Service: ${SERVICE_NAME} (to be created)"
echo "  RDS Endpoint: ${RDS_ENDPOINT}"
echo "  ALB DNS: http://${ALB_DNS}"
echo "  Target Group ARN: ${TG_ARN}"
echo "  VPC ID: ${VPC_ID}"
echo "  Subnets: ${SUBNET_ID_1}, ${SUBNET_ID_2}"
echo "  Security Groups: ALB=${ALB_SG_ID}, ECS=${ECS_SG_ID}, RDS=${RDS_SG_ID}"
echo ""
echo "🔑 GitHub Secrets to Configure (Backend):"
echo "  AWS_BACKEND_ROLE_ARN: ${GITHUB_ROLE_ARN}"
echo "  ECR_REPOSITORY: ${ECR_URI}"
echo "  ECS_CLUSTER: ${CLUSTER_NAME}"
echo "  ECS_SERVICE: ${SERVICE_NAME}"
echo "  TARGET_GROUP_ARN: ${TG_ARN}"
echo "  TASK_EXECUTION_ROLE_ARN: ${TASK_EXEC_ROLE_ARN}"
echo "  SECRET_NAME: ${SECRET_NAME}"
echo "  AWS_REGION: ${AWS_REGION}"
echo ""
echo "🔧 Next Steps:"
echo "  1. Add the GitHub secrets above to your repository"
echo "  2. Update backend/Dockerfile.backend if needed"
echo "  3. Push to 'release' branch to trigger deployment"
echo "  4. Monitor deployment: aws ecs describe-services --cluster ${CLUSTER_NAME} --services ${SERVICE_NAME}"
echo ""
echo "📊 Monitor Logs:"
echo "  CloudWatch Log Group: /ecs/${PROJECT_NAME}-backend"
echo "  AWS Console: https://ap-south-1.console.aws.amazon.com/cloudwatch/home?region=ap-south-1#logsV2:log-groups/log-group/%2Fecs%2F${PROJECT_NAME}-backend"
echo "  CLI Command: aws logs tail /ecs/${PROJECT_NAME}-backend --follow"
echo ""
echo "🌐 Your backend will be accessible at: http://${ALB_DNS}"
echo "======================================================================"

exit 0