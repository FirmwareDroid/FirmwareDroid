#!/bin/bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

set -e

# ---------------------------------------------------------------------------
# Decrypt environment variables from the .env file when the key is available.
# This ensures that ENC:-prefixed secret values (DJANGO_SUPERUSER_PASSWORD,
# etc.) are available as plaintext shell variables for the commands below.
# ---------------------------------------------------------------------------
FMD_ENV_FILE="${FMD_ENV_FILE:-/var/www/.env}"
FMD_KEY_FILE="${FMD_KEY_FILE:-/var/www/.env.key}"
FMD_DECRYPTED_ENV="/dev/shm/fmd_env_$$.sh"

if [ -f "${FMD_KEY_FILE}" ]; then
    if python3 /var/www/source/utils/env_utils.py "${FMD_ENV_FILE}" "${FMD_KEY_FILE}" > "${FMD_DECRYPTED_ENV}" 2>/dev/null; then
        # shellcheck disable=SC1090
        . "${FMD_DECRYPTED_ENV}"
    fi
    rm -f "${FMD_DECRYPTED_ENV}"
fi

# Ensure a mounted /file_store exists and is writable by the www user.
# We must perform ownership changes as root at container start; do NOT grant
# the runtime `www` user additional sudo rights. If the container is started
# as non-root (www), we will warn but continue.
if [ "$(id -u)" -eq 0 ]; then
    mkdir -p ./file_store || true
    chown -R www:www ./file_store || true
    chmod -R u+rwX,g+rwX,o-rwx ./file_store || true
else
    echo "Warning: container not started as root; cannot change ownership of /file_store. Ensure host permissions or use a named volume."
fi
mkdir -p /var/www/blob_storage/django_database/
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
# If started as root: drop privileges to 'www' for the main server process.
GUNICORN_CMD=("/home/www/.local/bin/gunicorn" -w 17 --bind 0.0.0.0:5000 --worker-tmp-dir /dev/shm --chdir /var/www/source/ --timeout 300 --worker-class gevent --threads 12 --log-level debug webserver.wsgi:app)

if [ "$(id -u)" -eq 0 ]; then
    echo "Attempting to drop privileges to user 'www' and start gunicorn as www"
    # Preferred: su (available in most Debian images)
    if command -v su >/dev/null 2>&1; then
        exec su -s /bin/sh www -c "${GUNICORN_CMD[*]}"
    fi
    echo "Warning: unable to drop privileges (su/runuser/gosu/python3 not available). Starting gunicorn as root." >&2
    exec "${GUNICORN_CMD[@]}"
else
    exec "${GUNICORN_CMD[@]}"
fi
