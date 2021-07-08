# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
from itsdangerous import URLSafeTimedSerializer
from itsdangerous import TimestampSigner


def generate_confirmation_token(data, secret_key, salt):
    """
    Generate a URL safe token with a timestamp. This token is invalidated only by time.
    :param salt: str - salt used for generating the token.
    :param secret_key: str - key used for generating the token.
    :param data: str - data to include into the token.
    :return: str - a token containing the encoded data.
    """
    serializer = URLSafeTimedSerializer(secret_key)
    return serializer.dumps(data, salt=salt)


def validate_token(token, secret_key, salt, expiration=300):
    """
    Validates that a URL safe token is not expired. Returns the encoded data if the token is valid.
    :param salt: str - salt used for generating the token.
    :param secret_key: str - key used for generating the token.
    :param token: str - token to validate.
    :param expiration: int - seconds until the token is invalid.
    :return: str - data extracted from the token.
    """
    serializer = URLSafeTimedSerializer(secret_key)
    data = None
    try:
        ts = TimestampSigner(secret_key, salt=salt)
        isValid = ts.validate(token, max_age=expiration)
        if isValid:
            data = serializer.loads(
                token,
                salt=salt,
                max_age=expiration
            )
    except Exception as err:
        logging.warning(f"Token validation error: {err}")
        raise RuntimeError(err)
    return data
