#!/bin/bash
set -e

# Run database migrations
echo "🦖 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "🦕 Checking for admin dino..."
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@certosaurus.local', 'admin123')
    print('🥚 Hatched admin user (username: admin, password: admin123)')
else:
    print('🦴 Admin dino already exists')
EOF

# Collect static files
echo "🌿 Gathering static files..."
python manage.py collectstatic --noinput

# Start the server
echo "🌋 RAWR! Starting Certosaurus..."
exec gunicorn --bind 0.0.0.0:8000 --workers 2 certosaurus_project.wsgi:application
