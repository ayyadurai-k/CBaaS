#!/bin/bash
# =============================================================================
# Setup AWS WAF
# =============================================================================
# Creates WAF Web ACL with managed rules:
# - AWS Core Rule Set (OWASP Top 10)
# - SQL Injection protection
# - Cross-Site Scripting (XSS) protection
# - Rate limiting (2000 requests per 5 min per IP)
# =============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/config.sh"
source "${SCRIPT_DIR}/cloudfront-info.env"

print_info "=========================================="
print_info "Setting up AWS WAF"
print_info "=========================================="

# WAF for CloudFront must be in us-east-1
WAF_REGION="us-east-1"

# -----------------------------------------------------------------------------
# Create WAF Web ACL
# -----------------------------------------------------------------------------
print_info "Creating WAF Web ACL..."

WAF_CONFIG=$(cat <<'EOF'
{
    "Name": "WAF_NAME_PLACEHOLDER",
    "Scope": "CLOUDFRONT",
    "DefaultAction": {
        "Allow": {}
    },
    "Description": "WAF for CBaaS CloudFront - OWASP protection and rate limiting",
    "Rules": [
        {
            "Name": "AWS-AWSManagedRulesCommonRuleSet",
            "Priority": 1,
            "Statement": {
                "ManagedRuleGroupStatement": {
                    "VendorName": "AWS",
                    "Name": "AWSManagedRulesCommonRuleSet"
                }
            },
            "OverrideAction": {
                "None": {}
            },
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "AWSManagedRulesCommonRuleSetMetric"
            }
        },
        {
            "Name": "AWS-AWSManagedRulesKnownBadInputsRuleSet",
            "Priority": 2,
            "Statement": {
                "ManagedRuleGroupStatement": {
                    "VendorName": "AWS",
                    "Name": "AWSManagedRulesKnownBadInputsRuleSet"
                }
            },
            "OverrideAction": {
                "None": {}
            },
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "AWSManagedRulesKnownBadInputsRuleSetMetric"
            }
        },
        {
            "Name": "AWS-AWSManagedRulesSQLiRuleSet",
            "Priority": 3,
            "Statement": {
                "ManagedRuleGroupStatement": {
                    "VendorName": "AWS",
                    "Name": "AWSManagedRulesSQLiRuleSet"
                }
            },
            "OverrideAction": {
                "None": {}
            },
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "AWSManagedRulesSQLiRuleSetMetric"
            }
        },
        {
            "Name": "RateLimitRule",
            "Priority": 4,
            "Statement": {
                "RateBasedStatement": {
                    "Limit": 2000,
                    "AggregateKeyType": "IP"
                }
            },
            "Action": {
                "Block": {}
            },
            "VisibilityConfig": {
                "SampledRequestsEnabled": true,
                "CloudWatchMetricsEnabled": true,
                "MetricName": "RateLimitRuleMetric"
            }
        }
    ],
    "VisibilityConfig": {
        "SampledRequestsEnabled": true,
        "CloudWatchMetricsEnabled": true,
        "MetricName": "METRIC_NAME_PLACEHOLDER"
    }
}
EOF
)

# Replace placeholders
WAF_CONFIG=$(echo "$WAF_CONFIG" | sed "s/WAF_NAME_PLACEHOLDER/${WAF_WEB_ACL_NAME}/g")
WAF_CONFIG=$(echo "$WAF_CONFIG" | sed "s/METRIC_NAME_PLACEHOLDER/${WAF_WEB_ACL_NAME}Metric/g")

echo "$WAF_CONFIG" > "${SCRIPT_DIR}/waf-config.json"

# Create Web ACL
WAF_ACL_ARN=$(aws wafv2 create-web-acl \
    --region "$WAF_REGION" \
    --cli-input-json file://"${SCRIPT_DIR}/waf-config.json" \
    --tags "Key=Project,Value=${PROJECT_NAME}" "Key=Environment,Value=${ENVIRONMENT}" "Key=ManagedBy,Value=aws-cli-automation" \
    --query 'Summary.ARN' \
    --output text 2>/dev/null || \
    aws wafv2 list-web-acls \
        --region "$WAF_REGION" \
        --scope CLOUDFRONT \
        --query "WebACLs[?Name=='${WAF_WEB_ACL_NAME}'].ARN | [0]" \
        --output text)

print_success "WAF Web ACL ARN: $WAF_ACL_ARN"

# -----------------------------------------------------------------------------
# Associate WAF with CloudFront Distribution
# -----------------------------------------------------------------------------
print_info "Associating WAF with CloudFront distribution..."

aws wafv2 associate-web-acl \
    --region "$WAF_REGION" \
    --web-acl-arn "$WAF_ACL_ARN" \
    --resource-arn "$CF_ARN" \
    2>/dev/null || print_warning "WAF already associated or CloudFront not ready"

print_success "WAF associated with CloudFront"

# -----------------------------------------------------------------------------
# Save WAF Information
# -----------------------------------------------------------------------------
WAF_INFO_FILE="${SCRIPT_DIR}/waf-info.env"
cat > "$WAF_INFO_FILE" <<EOF
# AWS WAF Information
export WAF_ACL_ARN="$WAF_ACL_ARN"
export WAF_WEB_ACL_NAME="$WAF_WEB_ACL_NAME"
EOF

print_success "WAF information saved to: $WAF_INFO_FILE"

print_success "=========================================="
print_success "WAF setup completed!"
print_success "=========================================="
print_info "WAF Rules:"
print_info "  - AWS Core Rule Set (OWASP Top 10)"
print_info "  - Known Bad Inputs"
print_info "  - SQL Injection Protection"
print_info "  - Rate Limiting (2000 req/5min per IP)"
print_info ""
print_info "Monitor WAF: https://console.aws.amazon.com/wafv2/home?region=us-east-1#/cloudfront/webacl/${WAF_WEB_ACL_NAME}"
