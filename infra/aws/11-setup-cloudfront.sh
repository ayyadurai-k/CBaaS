#!/bin/bash
# =============================================================================
# Setup CloudFront Distribution
# =============================================================================
# Creates:
# - CloudFront distribution for frontend
# - Origin Access Control (OAC) for S3
# - Cache behaviors for optimal performance
# - Updates S3 bucket policy
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/s3-info.env"

print_info "=========================================="
print_info "Setting up CloudFront Distribution"
print_info "=========================================="

# -----------------------------------------------------------------------------
# Create CloudFront Distribution
# -----------------------------------------------------------------------------
print_info "Creating CloudFront distribution..."

# Build CloudFront configuration
CF_CONFIG=$(cat <<EOF
{
    "CallerReference": "${PROJECT_NAME}-frontend-$(date +%s)",
    "Comment": "${PROJECT_NAME} frontend distribution - ${ENVIRONMENT}",
    "Enabled": true,
    "DefaultRootObject": "index.html",
    "Origins": {
        "Quantity": 1,
        "Items": [{
            "Id": "S3-${S3_FRONTEND_BUCKET}",
            "DomainName": "${S3_FRONTEND_BUCKET}.s3.${AWS_REGION}.amazonaws.com",
            "OriginAccessControlId": "${OAC_ID}",
            "S3OriginConfig": {
                "OriginAccessIdentity": ""
            }
        }]
    },
    "DefaultCacheBehavior": {
        "TargetOriginId": "S3-${S3_FRONTEND_BUCKET}",
        "ViewerProtocolPolicy": "redirect-to-https",
        "AllowedMethods": {
            "Quantity": 2,
            "Items": ["GET", "HEAD"],
            "CachedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"]
            }
        },
        "Compress": true,
        "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
        "TrustedSigners": {
            "Enabled": false,
            "Quantity": 0
        }
    },
    "CacheBehaviors": {
        "Quantity": 1,
        "Items": [{
            "PathPattern": "/static/*",
            "TargetOriginId": "S3-${S3_FRONTEND_BUCKET}",
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {
                "Quantity": 2,
                "Items": ["GET", "HEAD"],
                "CachedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"]
                }
            },
            "Compress": true,
            "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
            "TrustedSigners": {
                "Enabled": false,
                "Quantity": 0
            }
        }]
    },
    "CustomErrorResponses": {
        "Quantity": 1,
        "Items": [{
            "ErrorCode": 404,
            "ResponsePagePath": "/index.html",
            "ResponseCode": "200",
            "ErrorCachingMinTTL": 300
        }]
    },
    "PriceClass": "${CLOUDFRONT_PRICE_CLASS}",
    "ViewerCertificate": {
        "CloudFrontDefaultCertificate": true,
        "MinimumProtocolVersion": "TLSv1.2_2021"
    }
}
EOF
)

# Add ACM certificate if provided
if [ -n "$CLOUDFRONT_CERT_ARN" ]; then
    CF_CONFIG=$(echo "$CF_CONFIG" | jq --arg cert "$CLOUDFRONT_CERT_ARN" --arg domain "$FRONTEND_DOMAIN" '
        .Aliases = {
            "Quantity": 1,
            "Items": [$domain]
        } |
        .ViewerCertificate = {
            "ACMCertificateArn": $cert,
            "SSLSupportMethod": "sni-only",
            "MinimumProtocolVersion": "TLSv1.2_2021",
            "Certificate": $cert,
            "CertificateSource": "acm"
        }
    ')
fi

echo "$CF_CONFIG" > "${SCRIPT_DIR}/cloudfront-config.json"

# Create distribution
CF_DISTRIBUTION_ID=$(aws cloudfront create-distribution \
    --distribution-config file://"${SCRIPT_DIR}/cloudfront-config.json" \
    --query 'Distribution.Id' \
    --output text 2>/dev/null)

if [ -z "$CF_DISTRIBUTION_ID" ]; then
    print_warning "CloudFront distribution might already exist or there was an error"
    print_info "Checking for existing distribution..."
    
    CF_DISTRIBUTION_ID=$(aws cloudfront list-distributions \
        --query "DistributionList.Items[?Origins.Items[?Id=='S3-${S3_FRONTEND_BUCKET}']].Id | [0]" \
        --output text)
fi

print_success "CloudFront Distribution ID: $CF_DISTRIBUTION_ID"

# Get CloudFront domain name
CF_DOMAIN=$(aws cloudfront get-distribution \
    --id "$CF_DISTRIBUTION_ID" \
    --query 'Distribution.DomainName' \
    --output text)

print_success "CloudFront Domain: $CF_DOMAIN"

# -----------------------------------------------------------------------------
# Update S3 Bucket Policy for OAC
# -----------------------------------------------------------------------------
print_info "Updating S3 bucket policy for CloudFront OAC..."

# Get CloudFront distribution ARN
CF_ARN="arn:aws:cloudfront::${AWS_ACCOUNT_ID}:distribution/${CF_DISTRIBUTION_ID}"

BUCKET_POLICY=$(cat <<EOF
{
    "Version": "2012-10-17",
    "Statement": [{
        "Sid": "AllowCloudFrontServicePrincipal",
        "Effect": "Allow",
        "Principal": {
            "Service": "cloudfront.amazonaws.com"
        },
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::${S3_FRONTEND_BUCKET}/*",
        "Condition": {
            "StringEquals": {
                "AWS:SourceArn": "${CF_ARN}"
            }
        }
    }]
}
EOF
)

aws s3api put-bucket-policy \
    --bucket "$S3_FRONTEND_BUCKET" \
    --policy "$BUCKET_POLICY"

print_success "S3 bucket policy updated"

print_info "Waiting for CloudFront distribution to deploy..."
print_info "This can take 15-30 minutes..."

# Note: We don't wait here to avoid blocking the script
# aws cloudfront wait distribution-deployed --id "$CF_DISTRIBUTION_ID"

# -----------------------------------------------------------------------------
# Save CloudFront Information
# -----------------------------------------------------------------------------
CF_INFO_FILE="${SCRIPT_DIR}/cloudfront-info.env"
cat > "$CF_INFO_FILE" <<EOF
# CloudFront Distribution Information
export CF_DISTRIBUTION_ID="$CF_DISTRIBUTION_ID"
export CF_DOMAIN="$CF_DOMAIN"
export CF_ARN="$CF_ARN"
EOF

print_success "CloudFront information saved to: $CF_INFO_FILE"

print_success "=========================================="
print_success "CloudFront setup completed!"
print_success "=========================================="
print_info "Frontend will be accessible at: https://${CF_DOMAIN}"
if [ -n "$CLOUDFRONT_CERT_ARN" ]; then
    print_info "Custom domain: https://${FRONTEND_DOMAIN}"
    print_info "Configure DNS CNAME: ${FRONTEND_DOMAIN} -> ${CF_DOMAIN}"
fi
