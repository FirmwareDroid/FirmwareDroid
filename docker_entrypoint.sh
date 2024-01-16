#!/bin/bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

set -e

mkdir -p /var/www/blob_storage/django_database/
#chown "$(whoami):$(whoami)" /var/www/blob_storage/django_database/db.sqlite3

# Collect static files
echo "Collect static files"
python3 ./source/manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python3 ./source/manage.py makemigrations
python3 ./source/manage.py migrate --noinput


DJANGO_SUPERUSER_PASSWORD=73805a28-0111-406c-8e2c-9b3447a03605
DJANGO_SUPERUSER_USERNAME=fmd-admin
DJANGO_SUPERUSER_EMAIL=fmd-admin@fmd.localhost
# Create default superuser
echo "Create default user"
cat <<EOF | python3 ./source/manage.py shell
from django.contrib.auth import get_user_model

User = get_user_model()

User.objects.filter(username="${DJANGO_SUPERUSER_USERNAME}").exists() or \
    User.objects.create_superuser("${DJANGO_SUPERUSER_USERNAME}", "${DJANGO_SUPERUSER_EMAIL}", "${DJANGO_SUPERUSER_PASSWORD}")
EOF
#python3 ./source/manage.py createsuperuser --noinput


# Start server
/home/www/.local/bin/gunicorn -w 17 --bind 0.0.0.0:5000 --worker-tmp-dir /dev/shm --chdir /var/www/source/ --timeout 300 --worker-class gevent --threads 12 --log-level debug webserver.wsgi:app
