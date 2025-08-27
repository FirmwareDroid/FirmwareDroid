#!/bin/bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

set -e

# Run automatic setup if .env doesn't exist or if auto_setup.sh exists
if [ ! -f /var/www/.env ] || [ -f /var/www/auto_setup.sh ]; then
    echo "Running automatic FirmwareDroid setup..."
    if [ -f /var/www/auto_setup.sh ]; then
        BASE_DIR=/var/www /var/www/auto_setup.sh
    fi
fi

# Create Django database directory (backward compatibility)
mkdir -p /var/www/blob_storage/django_database/
# Create data directory structure (new default structure)
mkdir -p /var/www/data/django_database/
#chown "$(whoami):$(whoami)" /var/www/blob_storage/django_database/db.sqlite3

# Collect static files
echo "Collect static files"
python3 ./source/manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python3 ./source/manage.py makemigrations
python3 ./source/manage.py migrate --noinput

# Create default superuser
echo "Create default user"
cat <<EOF | python3 ./source/manage.py shell
from django.contrib.auth import get_user_model

User = get_user_model()

User.objects.filter(username="${DJANGO_SUPERUSER_USERNAME}").exists() or \
    User.objects.create_superuser("${DJANGO_SUPERUSER_USERNAME}", "${DJANGO_SUPERUSER_EMAIL}", "${DJANGO_SUPERUSER_PASSWORD}")
EOF

# Start server
/home/www/.local/bin/gunicorn -w 17 --bind 0.0.0.0:5000 --worker-tmp-dir /dev/shm --chdir /var/www/source/ --timeout 300 --worker-class gevent --threads 12 --log-level debug webserver.wsgi:app
