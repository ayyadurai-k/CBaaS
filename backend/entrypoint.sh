#!/bin/bash
set -e

echo "=== Django Startup Script ==="

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Create superuser (hardcoded)
echo "Creating superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@cbaas.com', 'Admin@CBaaS2025!');
    print('✅ Superuser created: admin');
else:
    print('ℹ️  Superuser already exists: admin');
"

echo "=== Startup Complete ==="

# Start the application
exec "$@"
