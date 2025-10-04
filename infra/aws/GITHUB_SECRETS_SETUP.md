# GitHub Secrets Setup for CBaaS

## 📝 Instructions

### 1. Go to GitHub Repository Settings
Visit: https://github.com/ayyadurai-k/CBaaS/settings/secrets/actions

Or navigate manually:
1. Go to your repository: https://github.com/ayyadurai-k/CBaaS
2. Click **Settings** (top right)
3. In the left sidebar, click **Secrets and variables** → **Actions**

### 2. Add Repository Secrets

Click **"New repository secret"** and add each of these **THREE** secrets:

---

#### Secret 1: AWS_ROLE_ARN
**Name:** `AWS_ROLE_ARN`

**Value:**
```
arn:aws:iam::577897067437:role/GitHubActionsDeployRole
```

**Description:** IAM role ARN that GitHub Actions will assume using OIDC

---

#### Secret 2: S3_BUCKET
**Name:** `S3_BUCKET`

**Value:**
```
cbaas-vite-app
```

**Description:** S3 bucket name where frontend files will be uploaded

---

#### Secret 3: CF_DIST_ID
**Name:** `CF_DIST_ID`

**Value:**
```
E3ACPM7RLVZA5I
```

**Description:** CloudFront distribution ID for cache invalidation

---

## ✅ Verification

After adding all three secrets, you should see them listed like this:

```
AWS_ROLE_ARN     Updated X seconds/minutes ago
S3_BUCKET        Updated X seconds/minutes ago
CF_DIST_ID       Updated X seconds/minutes ago
```

**Note:** You won't be able to view the secret values after saving them (they're encrypted).

---

## 🚀 Next Steps

Once secrets are configured:

1. **Test the workflow:**
   ```bash
   git add .
   git commit -m "feat: Add S3 + CloudFront deployment"
   git push origin main
   
   # Switch to release branch (triggers deployment)
   git checkout -b release
   git push origin release
   ```

2. **Monitor deployment:**
   - Go to https://github.com/ayyadurai-k/CBaaS/actions
   - You should see "CD - Frontend to S3 + CloudFront" workflow running

3. **Access your deployed app:**
   - Get your CloudFront URL with: `aws cloudfront get-distribution --id E3ACPM7RLVZA5I --query 'Distribution.DomainName' --output text`
   - Or check AWS Console → CloudFront → Distributions

---

## 🐛 Troubleshooting

### Workflow fails with "AssumeRoleWithWebIdentity" error
- Verify `AWS_ROLE_ARN` is correct
- Check IAM role trust policy allows your repository
- Ensure OIDC provider is configured in AWS

### Workflow fails with "Access Denied" on S3
- Verify `S3_BUCKET` name is correct
- Check IAM role has S3 permissions for this bucket

### CloudFront invalidation fails
- Verify `CF_DIST_ID` is correct
- Check IAM role has CloudFront invalidation permissions

### Workflow doesn't trigger
- Ensure you pushed to `release` branch
- Check workflow file exists in `.github/workflows/cd-frontend.yml`
- Verify workflow is enabled in repository settings

---

**Created:** October 4, 2025  
**Last Updated:** October 4, 2025
