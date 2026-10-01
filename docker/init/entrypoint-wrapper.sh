#!/bin/sh
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
#
# Thin wrapper used by images (Mongo, Neo4j, Backend) whose secret-bearing env vars (e.g.
# MONGO_INITDB_ROOT_PASSWORD, NEO4J_AUTH, DJANGO_SUPERUSER_*) must come from the generated
# `runtime.env` in the `fmd-config` named volume instead of a host-side `.env`/env_file.
# This lets images keep their normal entrypoint/CMD behavior while sourcing secrets at container start.
set -e

RUNTIME_ENV="${FMD_RUNTIME_ENV:-/config/runtime.env}"
if [ ! -f "$RUNTIME_ENV" ] && [ -f "/var/www/config/runtime.env" ]; then
    RUNTIME_ENV="/var/www/config/runtime.env"
fi

if [ -f "$RUNTIME_ENV" ]; then
    set -a
    # shellcheck disable=SC1090
    . "$RUNTIME_ENV"
    set +a
else
    echo "fmd-entrypoint-wrapper: warning: $RUNTIME_ENV not found; continuing without generated secrets." >&2
fi

exec "$@"
