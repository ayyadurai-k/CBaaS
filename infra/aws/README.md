# AWS Infrastructure Setup for CBaaS Frontend

This directory contains scripts and policy files for setting up AWS infrastructure to deploy the CBaaS React frontend to S3 + CloudFront.

## 📁 Directory Structure

```
infra/aws/
├── README.md                          # This file
├── setup-aws-infrastructure.sh        # Automated setup script (all policies embedded)
├── deploy_frontend.sh                 # Deployment script (used by CI/CD)
└── quick-deploy.sh                    # One-command manual deployment
```

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

Run the setup script to create all AWS resources at once:

```bash
# Make script executable
chmod +x setup-aws-infrastructure.sh

# Run setup (replace with your values)
./setup-aws-infrastructure.sh cbaas-frontend-prod 123456789012
```

**Parameters:**
- `cbaas-frontend-prod`: Your desired S3 bucket name (must be globally unique)
- `123456789012`: Your AWS account ID (find it with `aws sts get-caller-identity`)

**What it creates:**
- ✅ S3 bucket with static website hosting enabled
- ✅ S3 bucket policy for public read access
- ✅ GitHub OIDC provider in IAM
- ✅ IAM role for GitHub Actions with deployment permissions
- ✅ CloudFront distribution pointing to S3

**Output:** The script will display all the values you need for GitHub Secrets.

### Option 2: Manual Setup

If you prefer manual setup or need to customize, follow the detailed instructions in [docs/README_DEPLOY_FRONTEND.md](../../docs/README_DEPLOY_FRONTEND.md).

## 📝 Policy Files Explained

All IAM policies and CloudFront configurations are now **embedded directly in `setup-aws-infrastructure.sh`** for easier portability and learning.

### Embedded Policies in Script

The script contains these policies as heredocs:

**1. S3 Bucket Policy** (Public Read Access)
- Allows anyone on the internet to read files
- Applied after bucket creation
- Required for public website hosting

**2. GitHub Trust Policy** (OIDC Authentication)  
- Allows GitHub Actions to assume IAM role
- Scoped to `ayyadurai-k/CBaaS:release` branch only
- Uses temporary credentials (expire in 1 hour)

**3. IAM Permissions Policy** (Deployment Permissions)
- S3 permissions: Upload, delete, list files
- CloudFront permissions: Create/check invalidations
- Least-privilege principle (only what's needed)

**4. CloudFront Distribution Config**
- Origin: S3 website endpoint
- HTTPS redirect enabled
- SPA routing support (404 → index.html)
- Cache settings optimized for React apps

To view these policies, open `setup-aws-infrastructure.sh` and search for the relevant sections.

## 🔧 Manual Commands

If you want to run individual steps (not recommended - use `setup-aws-infrastructure.sh` instead):

### Create S3 Bucket
```bash
aws s3 mb s3://your-bucket-name --region ap-south-1
```

### Enable Website Hosting
```bash
aws s3 website s3://your-bucket-name \
  --index-document index.html \
  --error-document index.html
```

### Create OIDC Provider
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### Create IAM Role
```bash
# Policy is embedded in setup-aws-infrastructure.sh
# See script for complete trust policy with OIDC configuration
aws iam create-role \
  --role-name GitHubActionsDeployRole \
  --assume-role-policy-document '{ "Version": "2012-10-17", ... }'
```

### Attach Permissions
```bash
# Policy is embedded in setup-aws-infrastructure.sh
# See script for complete permissions policy
aws iam put-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-name DeployFrontendPolicy \
  --policy-document '{ "Version": "2012-10-17", ... }'
```

### Create CloudFront Distribution
```bash
# Configuration is embedded in setup-aws-infrastructure.sh
# See script for complete distribution config with SPA routing
aws cloudfront create-distribution \
  --distribution-config '{ "CallerReference": "...", ... }'
```

**Note:** These manual commands are complex. The automated script handles all edge cases and proper variable substitution. Use `setup-aws-infrastructure.sh` instead!

## 🧹 Cleanup

To delete all created resources:

```bash
# Delete S3 bucket (must be empty first)
aws s3 rm s3://your-bucket-name --recursive
aws s3 rb s3://your-bucket-name

# Delete CloudFront distribution (must be disabled first)
aws cloudfront delete-distribution --id YOUR_DIST_ID --if-match ETAG

# Delete IAM role
aws iam delete-role-policy --role-name GitHubActionsDeployRole --policy-name DeployFrontendPolicy
aws iam delete-role --role-name GitHubActionsDeployRole

# Delete OIDC provider (only if not used by other apps)
aws iam delete-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com
```

## ⚠️ Important Notes

1. **Bucket Name:** Must be globally unique across all AWS accounts
2. **Region:** Scripts use `ap-south-1` (Mumbai) - change if needed
3. **OIDC Provider:** Only needs to be created once per AWS account
4. **CloudFront:** Takes 15-30 minutes to deploy initially
5. **Costs:** See cost estimates in main deployment README

## 🔍 Verification

After setup, verify everything works:

```bash
# Test S3 bucket
aws s3 ls s3://your-bucket-name

# Test IAM role
aws iam get-role --role-name GitHubActionsDeployRole

# Test CloudFront distribution
aws cloudfront get-distribution --id YOUR_DIST_ID

# Test OIDC provider
aws iam list-open-id-connect-providers
```

## 📚 Related Documentation

- [Main Deployment Guide](../../docs/README_DEPLOY_FRONTEND.md)
- [GitHub Actions Workflow](../../.github/workflows/cd-frontend.yml)
- [AWS S3 Static Website Hosting](https://docs.aws.amazon.com/AmazonS3/latest/userguide/WebsiteHosting.html)
- [CloudFront Documentation](https://docs.aws.amazon.com/cloudfront/)
- [GitHub OIDC with AWS](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services)

## 🆘 Troubleshooting

### "Bucket already exists"
S3 bucket names must be globally unique. Try a different name.

### "Access Denied" errors
Check your AWS CLI credentials: `aws sts get-caller-identity`

### OIDC provider errors
Verify the thumbprint is correct: `6938fd4d98bab03faadb97b34396831e3780aea1`

### CloudFront creation fails
Check if you've hit the CloudFront distribution limit (default: 200 per account)

---

**Last Updated**: October 4, 2025  
**Maintained By**: CBaaS Team
