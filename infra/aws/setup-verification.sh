#!/bin/bash

##############################################################################
# CBaaS Backend Quick Setup Script
# Run this after the infrastructure setup to verify everything works
##############################################################################

set -e

echo "🚀 CBaaS Backend Setup Verification"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "backend/manage.py" ]; then
    echo "❌ Please run from project root (where backend/manage.py exists)"
    exit 1
fi

# Check required files
echo "📋 Checking required files..."
REQUIRED_FILES=(
    "backend/Dockerfile.backend"
    "infra/aws/setup-aws-backend.sh"
    "infra/aws/deploy_backend.sh"
    ".github/workflows/cd-backend.yml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file - MISSING"
        exit 1
    fi
done

# Check backend health endpoint
echo ""
echo "🔍 Checking Django health endpoint..."
cd backend

# Check if health endpoint exists
if grep -r "health" apps/ config/ 2>/dev/null | grep -q "url\|path"; then
    echo "  ✅ Health endpoint configured"
else
    echo "  ⚠️  No health endpoint found. Consider adding one:"
    echo "     # In config/urls.py"
    echo "     path('health/', lambda request: HttpResponse('OK'), name='health')"
fi

# Check if gunicorn is in requirements
if grep -q "gunicorn" requirements/prod.txt 2>/dev/null; then
    echo "  ✅ Gunicorn in requirements"
else
    echo "  ⚠️  Add 'gunicorn' to requirements/prod.txt"
fi

# Check if psycopg2 is in requirements
if grep -q "psycopg2" requirements/prod.txt 2>/dev/null; then
    echo "  ✅ PostgreSQL driver in requirements"
else
    echo "  ⚠️  Add 'psycopg2-binary' to requirements/prod.txt"
fi

cd ..

echo ""
echo "🔧 Next Steps:"
echo "1. Run infrastructure setup:"
echo "   ./infra/aws/setup-aws-backend.sh cbaas 577897067437"
echo ""
echo "2. Add GitHub secrets (values from setup output):"
echo "   - AWS_ROLE_ARN"
echo "   - ECR_REPOSITORY" 
echo "   - ECS_CLUSTER"
echo "   - ECS_SERVICE"
echo "   - TARGET_GROUP_ARN"
echo ""
echo "3. Test deployment:"
echo "   git checkout release && git push origin release"
echo ""
echo "📚 Full documentation: infra/aws/README_DEPLOY_BACKEND.md"