# AWS Infrastructure Setup for CBaaS Frontend

This directory contains scripts and policy files for setting up AWS infrastructure to deploy the CBaaS React frontend to S3 + CloudFront.

## 📁 Directory Structure

```
infra/aws/
├── README.md                          # This file
├── setup-aws-infrastructure.sh        # Automated setup script
├── deploy_frontend.sh                 # Deployment script (used by CI/CD)
└── policies/
    ├── github-trust-policy.json       # OIDC trust policy for GitHub Actions
    ├── deploy-permissions.json        # IAM permissions for deployment
    ├── s3-public-policy.json          # S3 bucket public read policy
    └── cloudfront-distribution.json   # CloudFront distribution config
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

### `github-trust-policy.json`
Allows GitHub Actions from your repository to assume the IAM role using OIDC authentication.

**What to replace:**
- `YOUR_AWS_ACCOUNT_ID`: Your AWS account ID
- Repository is hardcoded to `ayyadurai-k/CBaaS` - change if needed

### `deploy-permissions.json`
Grants the IAM role permissions to deploy to S3 and invalidate CloudFront.

**What to replace:**
- `your-app-bucket-name`: Your S3 bucket name
- `YOUR_AWS_ACCOUNT_ID`: Your AWS account ID

### `s3-public-policy.json`
Makes S3 bucket objects publicly readable (required for website hosting).

**What to replace:**
- `your-app-bucket-name`: Your S3 bucket name

### `cloudfront-distribution.json`
Configuration for CloudFront distribution with SPA routing support.

**What to replace:**
- `your-app-bucket-name.s3-website.ap-south-1.amazonaws.com`: Your S3 website endpoint

## 🔧 Manual Commands

If you want to run individual steps:

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
# Update policies/github-trust-policy.json first
aws iam create-role \
  --role-name GitHubActionsDeployRole \
  --assume-role-policy-document file://policies/github-trust-policy.json
```

### Attach Permissions
```bash
# Update policies/deploy-permissions.json first
aws iam put-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-name DeployFrontendPolicy \
  --policy-document file://policies/deploy-permissions.json
```

### Create CloudFront Distribution
```bash
# Update policies/cloudfront-distribution.json first
aws cloudfront create-distribution \
  --distribution-config file://policies/cloudfront-distribution.json
```

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
