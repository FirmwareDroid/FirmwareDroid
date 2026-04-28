#!/usr/bin/env bash
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
#
# start.sh – Decrypt the .env secrets into RAM and launch docker-compose.
#
# Usage:
#   ./start.sh [docker-compose options]   e.g. ./start.sh -d
#
# Why this script is needed
# --------------------------
# Secret values in .env are Fernet-encrypted on disk (prefixed with ENC:).
# Docker Compose reads .env directly for variable substitution (e.g.
# ${REDIS_PASSWORD} in command: lines) and passes env_file contents to
# containers verbatim.  Infrastructure containers such as Redis and MongoDB
# that do not run Python need plaintext values.
#
# This script:
#   1. Decrypts .env into a temporary file on /dev/shm (RAM – never touches
#      persistent storage) using the key from .env.key.
#   2. Exports FMD_ENV_FILE pointing at that temp file so Docker Compose
#      uses it for env_file directives.
#   3. Sources the decrypted values into the current shell so Docker Compose
#      variable substitution (${VAR}) also works.
#   4. Removes the decrypted temp file after docker-compose exits.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"
KEY_FILE="${SCRIPT_DIR}/.env.key"
RUNTIME_ENV="/dev/shm/fmd-runtime-$$.env"

# --- Pre-flight checks ------------------------------------------------------
if [ ! -f "${ENV_FILE}" ]; then
    echo "Error: ${ENV_FILE} not found. Run 'python3 setup.py' first." >&2
    exit 1
fi

if [ ! -f "${KEY_FILE}" ]; then
    echo "Error: ${KEY_FILE} not found. Run 'python3 setup.py' first." >&2
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: python3 is required but not found in PATH." >&2
    exit 1
fi

# --- Decrypt to RAM ---------------------------------------------------------
python3 "${SCRIPT_DIR}/source/utils/env_utils.py" "${ENV_FILE}" "${KEY_FILE}" \
    > "${RUNTIME_ENV}" || { echo "Error: Failed to decrypt .env secrets." >&2; exit 1; }
chmod 600 "${RUNTIME_ENV}"

# Ensure the temp file is always removed, even on error or SIGINT.
cleanup() {
    rm -f "${RUNTIME_ENV}"
}
trap cleanup EXIT INT TERM

# Source decrypted values so Docker Compose ${VAR} substitution works.
# shellcheck disable=SC1090
set -a
. "${RUNTIME_ENV}"
set +a

# Point docker-compose env_file directives at the decrypted file.
export FMD_ENV_FILE="${RUNTIME_ENV}"
export FMD_KEY_FILE="${KEY_FILE}"

# --- Launch docker-compose --------------------------------------------------
docker compose --env-file "${RUNTIME_ENV}" "$@"
