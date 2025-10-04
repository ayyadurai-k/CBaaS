# Frontend Deployment to AWS S3 + CloudFront

This document explains how to deploy the CBaaS React frontend to AWS S3 with CloudFront CDN distribution using GitHub Actions.

## 🏗️ Architecture

```
GitHub Actions (on push to release)
    ↓
Build React app in Docker (Dockerfile.s3)
    ↓
Extract build artifacts (dist/)
    ↓
Upload to S3 bucket
    ↓
Invalidate CloudFront cache
    ↓
✅ Live deployment
```

## 📋 Prerequisites

### 1. AWS Infrastructure Setup

You need to manually create the following AWS resources (one-time setup):

#### S3 Bucket
```bash
# Create bucket
aws s3 mb s3://your-app-bucket-name --region ap-south-1

# Enable static website hosting
aws s3 website s3://your-app-bucket-name \
  --index-document index.html \
  --error-document index.html

# Disable block public access (required for public website)
aws s3api put-public-access-block \
  --bucket your-app-bucket-name \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
```

#### CloudFront Distribution
```bash
# Create a CloudFront distribution pointing to your S3 bucket
# You can do this via AWS Console or CLI
# Note: This is complex via CLI, recommend using Console for first-time setup

# Via Console:
# 1. Go to CloudFront → Create Distribution
# 2. Origin Domain: your-app-bucket-name.s3-website.ap-south-1.amazonaws.com
# 3. Viewer Protocol Policy: Redirect HTTP to HTTPS
# 4. Default Root Object: index.html
# 5. Error Pages: Add custom error response for 404 → /index.html (for SPA routing)
```

#### IAM Role for GitHub Actions (OIDC)

Create an IAM role that GitHub Actions can assume:

```bash
# 1. Create trust policy (save as github-trust-policy.json)
cat > github-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
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

# 2. Create the role
aws iam create-role \
  --role-name GitHubActionsDeployRole \
  --assume-role-policy-document file://github-trust-policy.json

# 3. Create permissions policy (save as deploy-permissions.json)
cat > deploy-permissions.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket",
        "s3:PutBucketPolicy"
      ],
      "Resource": [
        "arn:aws:s3:::your-app-bucket-name",
        "arn:aws:s3:::your-app-bucket-name/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudfront:CreateInvalidation",
        "cloudfront:GetInvalidation"
      ],
      "Resource": "arn:aws:cloudfront::YOUR_AWS_ACCOUNT_ID:distribution/*"
    }
  ]
}
EOF

# 4. Attach policy to role
aws iam put-role-policy \
  --role-name GitHubActionsDeployRole \
  --policy-name DeployFrontendPolicy \
  --policy-document file://deploy-permissions.json
```

**Note:** You need to set up the OIDC provider first if you haven't:
```bash
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
```

### 2. GitHub Secrets Configuration

Add the following secrets in your GitHub repository:  
**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Description | Example Value |
|-------------|-------------|---------------|
| `AWS_ROLE_ARN` | ARN of the IAM role created above | `arn:aws:iam::123456789012:role/GitHubActionsDeployRole` |
| `S3_BUCKET` | Name of your S3 bucket | `cbaas-frontend-prod` |
| `CF_DIST_ID` | CloudFront distribution ID | `E1234ABCDEFGH` |

## 🚀 How It Works

### Automatic Deployment (GitHub Actions)

When you push to the `release` branch:

1. **Trigger**: Workflow runs on changes to `frontend/**` or workflow file
2. **Build**: React app is built inside Docker using `Dockerfile.s3`
3. **Extract**: Build artifacts are copied from Docker container to runner
4. **Deploy**: `deploy_frontend.sh` uploads files to S3 with proper cache headers
5. **Invalidate**: CloudFront cache is invalidated to show new changes immediately

### Manual Deployment

You can also deploy manually from your local machine:

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Build the React app
npm run build

# 3. Configure AWS credentials (if not already done)
aws configure

# 4. Run the deploy script
chmod +x ../infra/aws/deploy_frontend.sh
../infra/aws/deploy_frontend.sh your-bucket-name YOUR_CF_DIST_ID
```

## 📦 File Structure

```
CBaaS/
├── frontend/
│   ├── Dockerfile.s3              # Docker build for React app
│   ├── dist/                      # Build output (generated)
│   └── src/                       # React source code
├── infra/aws/
│   └── deploy_frontend.sh         # Deployment script
├── .github/workflows/
│   └── cd-frontend.yml            # GitHub Actions workflow
└── docs/
    └── README_DEPLOY_FRONTEND.md  # This file
```

## 🔧 Cache Strategy

The deployment script sets different cache headers for different file types:

| File Type | Cache-Control | Reason |
|-----------|---------------|--------|
| `index.html` | `max-age=300, must-revalidate` | Short cache (5 min) - contains references to hashed files |
| `*.js`, `*.css` | `max-age=31536000, immutable` | Long cache (1 year) - filenames include hash, safe to cache |
| Other assets | `max-age=86400` | Medium cache (24 hours) - images, fonts, etc. |

## 🐛 Troubleshooting

### Build fails in Docker
- Check `frontend/package.json` scripts are correct
- Ensure `.env.production` exists and has valid values
- Verify `vite.config.ts` is properly configured

### AWS credentials error
- Verify the IAM role ARN is correct in GitHub secrets
- Check the trust policy allows your repository
- Ensure OIDC provider is configured in AWS

### S3 upload fails
- Verify bucket name is correct
- Check IAM role has `s3:PutObject` permission
- Ensure bucket exists in the correct region

### CloudFront invalidation fails
- Verify distribution ID is correct
- Check IAM role has `cloudfront:CreateInvalidation` permission
- Ensure distribution is in "Deployed" state

### Changes not visible after deployment
- CloudFront invalidation can take 5-15 minutes
- Check browser cache (hard refresh with Ctrl+Shift+R)
- Verify invalidation completed: `aws cloudfront get-invalidation --distribution-id XXX --id YYY`

## 🔒 Security Notes

1. **S3 Bucket**: Only contains public static files, no sensitive data
2. **IAM Role**: Scoped to specific S3 bucket and CloudFront operations only
3. **OIDC**: GitHub Actions uses temporary credentials, no long-lived keys
4. **Secrets**: Never commit AWS credentials to git

## 📊 Monitoring

- **CloudFront Logs**: Enable logging to track access patterns
- **S3 Access Logs**: Monitor bucket access (optional)
- **GitHub Actions**: Check workflow runs for deployment status

## 🔄 Workflow Customization

To deploy on different branches, edit `.github/workflows/cd-frontend.yml`:

```yaml
on:
  push:
    branches:
      - release      # Current
      - staging      # Add staging environment
      - main         # Deploy on every main branch push
```

## 📝 Cost Estimates

For a typical small application:
- **S3 Storage**: ~$0.023/GB/month
- **S3 Requests**: ~$0.0004/1000 requests
- **CloudFront**: Free tier covers 1TB transfer, then ~$0.085/GB
- **CloudFront Requests**: ~$0.0075/10,000 requests

**Estimated monthly cost for low-traffic app**: $1-5/month

## 🆘 Support

For issues:
1. Check GitHub Actions workflow logs
2. Review CloudWatch logs (if enabled)
3. Consult AWS documentation
4. Check project issues on GitHub

---

**Last Updated**: October 4, 2025  
**Maintained By**: CBaaS Team
