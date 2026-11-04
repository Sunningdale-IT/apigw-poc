#!/bin/bash
set -e

ADMIN_USER="${CERTOSAUR_ADMIN_USER:-admin}"
ADMIN_PASSWORD="${CERTOSAUR_ADMIN_PASSWORD:-admin123}"
ADMIN_EMAIL="${CERTOSAUR_ADMIN_EMAIL:-admin@certosaur.local}"
SEED_CAS="${CERTOSAUR_SEED_CAS:-true}"
CLEAN_START="${CERTOSAUR_CLEAN_START:-false}"
DATA_DIR=/app/data
CERTS_DIR=/app/certificates_storage
CLEAN_MARKER="$DATA_DIR/.clean-start-done"
PORT="${PORT:-8000}"
WORKERS="${GUNICORN_WORKERS:-2}"

# Clean start: wipe the database and stored certificates, then re-seed below.
# One-shot: the marker file stops a container restart (e.g. after a reboot) with
# the flag still set from wiping again. Starting once without the flag clears the
# marker, so the next CERTOSAUR_CLEAN_START=true wipes again.
if [ "${CLEAN_START,,}" = "true" ]; then
    if [ -f "$CLEAN_MARKER" ]; then
        echo "☄️  CERTOSAUR_CLEAN_START is set but this container already did a clean start; keeping data."
    else
        echo "☄️  CLEAN START: wiping $DATA_DIR and $CERTS_DIR ..."
        find "$DATA_DIR" "$CERTS_DIR" -mindepth 1 -delete
        touch "$CLEAN_MARKER"
    fi
else
    rm -f "$CLEAN_MARKER"
fi

# Run database migrations
echo "🦖 Running database migrations..."
python manage.py migrate --noinput

# Create superuser if it doesn't exist
echo "🦕 Checking for admin dino..."
ADMIN_USER="$ADMIN_USER" ADMIN_PASSWORD="$ADMIN_PASSWORD" ADMIN_EMAIL="$ADMIN_EMAIL" \
python manage.py shell <<'PYEOF'
import os
from django.contrib.auth import get_user_model
User = get_user_model()
username = os.environ['ADMIN_USER']
if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, os.environ['ADMIN_EMAIL'], os.environ['ADMIN_PASSWORD'])
    print(f'🥚 Hatched admin user (username: {username})')
else:
    print('🦴 Admin dino already exists')
PYEOF

# Seed the default CA hierarchy (alpha root, commercial + government intermediates).
# The command is a no-op when any CA already exists, so this is safe on every start.
if [ "${SEED_CAS,,}" = "true" ]; then
    echo "🌱 Seeding initial certificate authorities..."
    python manage.py populate_initial_cas
fi

# Collect static files
echo "🌿 Gathering static files..."
python manage.py collectstatic --noinput

# Start the server
echo "🌋 RAWR! Starting Certosaur on port ${PORT}..."
exec gunicorn --bind "0.0.0.0:${PORT}" --workers "${WORKERS}" certosaur_project.wsgi:application
