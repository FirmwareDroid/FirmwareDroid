# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
Utility for loading and decrypting .env files whose secret values are
Fernet-encrypted on disk.

Secret values are stored with the prefix ``ENC:`` followed by the
URL-safe-base64-encoded Fernet token, e.g.::

    DJANGO_SECRET_KEY=ENC:gAAAAABl...

The matching encryption key is read from a separate ``.env.key`` file that
should be stored with mode 0600 and ideally on separate storage from the
``.env`` file itself.

Public API
----------
generate_key()          – generate a new Fernet key (bytes)
save_key(key, path)     – write key to path, chmod 0600
load_key(path)          – read key from path
encrypt_value(plain, f) – return ``ENC:<token>`` string
decrypt_value(value, f) – decrypt ``ENC:<token>`` or return value unchanged
load_decrypted_env(env, key) – decrypt env file, populate os.environ, return dict

CLI
---
Run as a script to write ``export KEY='value'`` lines to stdout::

    python env_utils.py <env_file> <key_file>

Source the output to export decrypted values into a shell session::

    . <(python3 env_utils.py .env .env.key)
"""

import os
import sys

from cryptography.fernet import Fernet, InvalidToken

# Prefix that marks an encrypted field value in the .env file.
SECRET_PREFIX = "ENC:"


def generate_key() -> bytes:
    """Return a new random Fernet key as bytes."""
    return Fernet.generate_key()


def save_key(key: bytes, key_file_path: str) -> None:
    """Write *key* to *key_file_path* with mode 0600."""
    with open(key_file_path, "wb") as f:
        f.write(key)
    os.chmod(key_file_path, 0o600)


def load_key(key_file_path: str) -> bytes:
    """Read and return the raw key bytes from *key_file_path*.

    Trailing whitespace (newlines) is stripped; Fernet keys are URL-safe
    base64 and contain no significant whitespace.
    """
    with open(key_file_path, "rb") as f:
        return f.read().strip()


def encrypt_value(plaintext: str, fernet: Fernet) -> str:
    """Encrypt *plaintext* and return an ``ENC:<token>`` string."""
    token = fernet.encrypt(plaintext.encode()).decode()
    return SECRET_PREFIX + token


def decrypt_value(value: str, fernet: Fernet) -> str:
    """
    Decrypt *value* if it starts with ``ENC:``.

    Returns the original *value* unchanged for non-encrypted fields.

    :raises InvalidToken: if the token is malformed or the key is wrong.
    """
    if value.startswith(SECRET_PREFIX):
        token = value[len(SECRET_PREFIX):]
        try:
            return fernet.decrypt(token.encode()).decode()
        except InvalidToken:
            raise InvalidToken(
                f"Failed to decrypt value – wrong key or corrupted token. "
                f"Verify that .env.key matches the key used during setup."
            )
    return value


def decrypt_env_to_dict(env_file_path: str, key_file_path: str) -> dict:
    """
    Read *env_file_path*, decrypt all ``ENC:`` prefixed values using the key
    in *key_file_path*, and return a plain ``{name: value}`` dictionary.

    Comment lines (starting with ``#``) and blank lines are skipped.
    Inline comments are stripped from unquoted, non-ENC: values only.
    """
    key = load_key(key_file_path)
    fernet = Fernet(key)
    result = {}

    with open(env_file_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "=" not in stripped:
                continue

            name, _, value = stripped.partition("=")
            name = name.strip()
            value = value.strip()

            # Strip inline comments only for unquoted, unencrypted values.
            # Encrypted tokens (ENC:...) are never treated as having inline
            # comments – their content is opaque base64.
            if (value
                    and not value.startswith(('"', "'"))
                    and not value.startswith(SECRET_PREFIX)):
                comment_pos = value.find(" #")
                if comment_pos != -1:
                    value = value[:comment_pos].strip()

            result[name] = decrypt_value(value, fernet)

    return result


def load_decrypted_env(env_file_path: str, key_file_path: str) -> dict:
    """
    Decrypt *env_file_path* using the key in *key_file_path*, populate
    ``os.environ`` with the plaintext values, and return the resulting dict.

    This is the main entry point used by ``settings.py``.
    """
    decrypted = decrypt_env_to_dict(env_file_path, key_file_path)
    for name, value in decrypted.items():
        os.environ[name] = value
    return decrypted


# ---------------------------------------------------------------------------
# CLI entry point – output ``export KEY='value'`` lines for shell sourcing.
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <env_file> <key_file>", file=sys.stderr)
        sys.exit(1)

    env_file_arg = sys.argv[1]
    key_file_arg = sys.argv[2]

    try:
        decrypted = decrypt_env_to_dict(env_file_arg, key_file_arg)
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except InvalidToken as exc:
        print(f"Decryption error: {exc}", file=sys.stderr)
        sys.exit(1)

    for k, v in decrypted.items():
        # Escape single quotes in the value for POSIX shell single-quoted strings.
        # The pattern "'\\''": end current single-quote string ('), output a
        # literal backslash-escaped single quote (\\'), then restart the
        # single-quote string (').  This is the portable POSIX approach.
        v_escaped = v.replace("'", "'\\''")
        print(f"export {k}='{v_escaped}'")
