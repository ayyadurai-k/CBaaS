# PowerShell Script to update AWS Secrets Manager with S3 configuration
# Usage: .\update-secrets.ps1

$ErrorActionPreference = "Stop"

$REGION = "ap-south-1"
$SECRET_NAME = "cbaas/backend/env"
$BUCKET_NAME = "cbaas-static-files"

Write-Host "🔐 Updating AWS Secrets Manager for CBaaS Backend" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Host "✅ AWS CLI found" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: AWS CLI is not installed" -ForegroundColor Red
    Write-Host "   Install: https://aws.amazon.com/cli/" -ForegroundColor Yellow
    exit 1
}

# Check AWS credentials
Write-Host "✅ Checking AWS credentials..." -ForegroundColor Yellow
try {
    aws sts get-caller-identity | Out-Null
    Write-Host "✅ AWS credentials verified" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: AWS credentials not configured" -ForegroundColor Red
    Write-Host "   Run: aws configure" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Prompt for S3 bucket name
$inputBucket = Read-Host "Enter S3 bucket name [default: cbaas-static-files]"
if ([string]::IsNullOrWhiteSpace($inputBucket)) {
    $inputBucket = $BUCKET_NAME
}
$BUCKET_NAME = $inputBucket

Write-Host ""
Write-Host "📦 S3 Bucket: $BUCKET_NAME" -ForegroundColor Cyan
Write-Host ""

# Check if bucket exists
try {
    aws s3api head-bucket --bucket $BUCKET_NAME 2>$null
    Write-Host "✅ S3 bucket '$BUCKET_NAME' exists" -ForegroundColor Green
} catch {
    Write-Host "⚠️  S3 bucket '$BUCKET_NAME' not found" -ForegroundColor Yellow
    $createBucket = Read-Host "Do you want to create it? (y/n)"
    if ($createBucket -eq "y") {
        Write-Host "Creating bucket..." -ForegroundColor Yellow
        aws s3api create-bucket `
            --bucket $BUCKET_NAME `
            --region $REGION `
            --create-bucket-configuration LocationConstraint=$REGION
        Write-Host "✅ Bucket created" -ForegroundColor Green
    } else {
        Write-Host "❌ Bucket required. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host ""

# Prompt for AWS credentials
Write-Host "🔑 Enter AWS IAM User Credentials for S3 Access" -ForegroundColor Cyan
Write-Host "(You can create these with: aws iam create-access-key --user-name cbaas-s3-user)" -ForegroundColor Gray
Write-Host ""

$aws_access_key_id = Read-Host "AWS_ACCESS_KEY_ID"
$aws_secret_access_key = Read-Host "AWS_SECRET_ACCESS_KEY" -AsSecureString
$aws_secret_access_key_plain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($aws_secret_access_key)
)

Write-Host ""

# Validate inputs
if ([string]::IsNullOrWhiteSpace($aws_access_key_id) -or [string]::IsNullOrWhiteSpace($aws_secret_access_key_plain)) {
    Write-Host "❌ Error: AWS credentials cannot be empty" -ForegroundColor Red
    exit 1
}

# Get current secret value
Write-Host "📥 Fetching current secret from Secrets Manager..." -ForegroundColor Yellow
try {
    $CURRENT_SECRET_JSON = aws secretsmanager get-secret-value `
        --secret-id $SECRET_NAME `
        --region $REGION `
        --query SecretString `
        --output text
    
    Write-Host "✅ Current secret retrieved" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Could not fetch secret '$SECRET_NAME'" -ForegroundColor Red
    exit 1
}

Write-Host ""

# Parse and update secret
Write-Host "🔄 Updating secret with S3 configuration..." -ForegroundColor Yellow

$secretObject = $CURRENT_SECRET_JSON | ConvertFrom-Json
$secretObject | Add-Member -NotePropertyName "AWS_ACCESS_KEY_ID" -NotePropertyValue $aws_access_key_id -Force
$secretObject | Add-Member -NotePropertyName "AWS_SECRET_ACCESS_KEY" -NotePropertyValue $aws_secret_access_key_plain -Force
$secretObject | Add-Member -NotePropertyName "AWS_STORAGE_BUCKET_NAME" -NotePropertyValue $BUCKET_NAME -Force

$UPDATED_SECRET = $secretObject | ConvertTo-Json -Compress

# Update the secret
try {
    aws secretsmanager update-secret `
        --secret-id $SECRET_NAME `
        --region $REGION `
        --secret-string $UPDATED_SECRET
    
    Write-Host "✅ Secret updated successfully!" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Failed to update secret" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📋 Summary of Updated Secret Keys:" -ForegroundColor Cyan
$secretObject.PSObject.Properties.Name | ForEach-Object { Write-Host "  - $_" -ForegroundColor Gray }

Write-Host ""
Write-Host "✅ Done! Next steps:" -ForegroundColor Green
Write-Host "   1. Register updated task definition:" -ForegroundColor Yellow
Write-Host "      aws ecs register-task-definition --cli-input-json file://infra/aws/task-definition.json" -ForegroundColor Gray
Write-Host ""
Write-Host "   2. Force new deployment:" -ForegroundColor Yellow
Write-Host "      aws ecs update-service --cluster cbaas-cluster --service cbaas-backend-service --force-new-deployment" -ForegroundColor Gray
Write-Host ""
Write-Host "   3. Verify at: https://your-api.com/api/debug/static" -ForegroundColor Yellow
