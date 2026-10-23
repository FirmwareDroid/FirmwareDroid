# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import hashlib
import logging
import time
import uuid
from datetime import datetime
from functools import wraps

import graphene
import jwt
import redis
from django.conf import settings
from django.http import HttpResponse
from django.utils.translation import gettext as _
from graphql_jwt import exceptions
from graphql_jwt.backends import JSONWebTokenBackend
from graphql_jwt.settings import jwt_settings
from graphql_jwt.shortcuts import get_user_by_token
from graphql_jwt.utils import (
    get_credentials,
    get_http_authorization,
    jwt_decode as original_jwt_decode,
    jwt_payload as original_jwt_payload,
    set_cookie,
)

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis_client():
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.Redis(
                host=getattr(settings, "REDIS_HOST", "redis"),
                port=getattr(settings, "REDIS_PORT", 6379),
                password=getattr(settings, "REDIS_PASSWORD", None) or None,
                db=1,
                socket_timeout=2.0,
                decode_responses=False,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Redis client for JWT revocation: {e}")
            return None
    return _redis_client


def get_token_hash(token: str) -> str:
    """Returns SHA-256 hash of a JWT token string."""
    return hashlib.sha256(token.strip().encode("utf-8")).hexdigest()


def revoke_token(token: str) -> bool:
    """
    Revokes a JWT token by storing its hash and jti in Redis until expiration.
    """
    if not token:
        return False
    try:
        unverified_payload = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False},
        )
    except Exception as e:
        logger.warning(f"Could not parse token payload for revocation: {e}")
        unverified_payload = {}

    exp = unverified_payload.get("exp")
    now = time.time()
    if exp:
        ttl = max(int(exp - now), 1)
    else:
        delta = getattr(jwt_settings, "JWT_EXPIRATION_DELTA", None)
        ttl = int(delta.total_seconds()) if delta else 86400

    token_hash = get_token_hash(token)
    r = get_redis_client()
    if r:
        try:
            r.setex(f"jwt:revoked:{token_hash}", ttl, b"1")
            jti = unverified_payload.get("jti")
            if jti:
                r.setex(f"jwt:revoked:{jti}", ttl, b"1")
            logger.info(f"JWT token {token_hash[:8]}... successfully revoked with TTL={ttl}s")
            return True
        except Exception as e:
            logger.error(f"Redis error while revoking token: {e}")
            return False
    return False


def is_token_revoked(token: str, payload: dict = None) -> bool:
    """
    Checks if a JWT token or its jti is recorded in the revocation blocklist.
    """
    if not token:
        return False
    r = get_redis_client()
    if not r:
        return False
    try:
        token_hash = get_token_hash(token)
        if r.exists(f"jwt:revoked:{token_hash}"):
            return True
        if payload and "jti" in payload:
            if r.exists(f"jwt:revoked:{payload['jti']}"):
                return True
        elif not payload:
            try:
                unverified = jwt.decode(
                    token,
                    options={"verify_signature": False, "verify_exp": False},
                )
                jti = unverified.get("jti")
                if jti and r.exists(f"jwt:revoked:{jti}"):
                    return True
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Redis error while checking token revocation: {e}")
    return False


def fmd_jwt_payload(user, context=None):
    """
    Extends standard graphql_jwt payload with a unique JWT ID (jti).
    """
    payload = original_jwt_payload(user, context)
    payload["jti"] = uuid.uuid4().hex
    return payload


def fmd_jwt_decode(token, context=None):
    """
    Decodes JWT token and validates it against the revocation blocklist.
    """
    payload = original_jwt_decode(token, context)
    if is_token_revoked(token, payload):
        raise jwt.InvalidTokenError(_("Token has been revoked"))
    return payload


def fmd_delete_cookie(response: HttpResponse, key: str):
    """
    Deletes a cookie matching the exact security parameters used when set,
    guaranteeing compliance with RFC 6265bis and all modern browsers.
    """
    response.delete_cookie(
        key,
        path=jwt_settings.JWT_COOKIE_PATH,
        domain=jwt_settings.JWT_COOKIE_DOMAIN,
        samesite=jwt_settings.JWT_COOKIE_SAMESITE or "Strict",
    )
    if key in response.cookies:
        response.cookies[key]["secure"] = jwt_settings.JWT_COOKIE_SECURE
        response.cookies[key]["httponly"] = True


def fmd_jwt_cookie(view_func):
    """
    Enhanced jwt_cookie decorator for GraphQL view that:
    1. Sets JWT cookie with secure/samesite flags on login/refresh.
    2. Securely deletes JWT, refresh, and session cookies on logout with
       RFC 6265bis-compliant Set-Cookie attributes (Secure; HttpOnly; SameSite=Strict).
    """
    @wraps(view_func)
    def wrapped_view(request, *args, **kwargs):
        request.jwt_cookie = True
        response = view_func(request, *args, **kwargs)

        if hasattr(request, "jwt_token"):
            expires = datetime.utcnow() + jwt_settings.JWT_EXPIRATION_DELTA
            set_cookie(
                response,
                jwt_settings.JWT_COOKIE_NAME,
                request.jwt_token,
                expires=expires,
            )
            if hasattr(request, "jwt_refresh_token"):
                refresh_token = request.jwt_refresh_token
                ref_expires = refresh_token.created + jwt_settings.JWT_REFRESH_EXPIRATION_DELTA
                set_cookie(
                    response,
                    jwt_settings.JWT_REFRESH_TOKEN_COOKIE_NAME,
                    refresh_token.token,
                    expires=ref_expires,
                )

        if getattr(request, "delete_jwt_cookie", False):
            fmd_delete_cookie(response, jwt_settings.JWT_COOKIE_NAME)
            fmd_delete_cookie(response, jwt_settings.JWT_REFRESH_TOKEN_COOKIE_NAME)
            if hasattr(settings, "SESSION_COOKIE_NAME"):
                fmd_delete_cookie(response, settings.SESSION_COOKIE_NAME)

        return response

    return wrapped_view


class FMDDeleteJSONWebTokenCookie(graphene.Mutation):
    """
    GraphQL mutation that revokes the caller's JWT token and signals cookie deletion.
    """
    class Arguments:
        pass

    deleted = graphene.Boolean(required=True)

    @classmethod
    def mutate(cls, root, info, **kwargs):
        request = info.context
        token = (
            get_http_authorization(request)
            or (request.COOKIES.get(jwt_settings.JWT_COOKIE_NAME) if hasattr(request, "COOKIES") else None)
        )
        if token:
            revoke_token(token)

        request.delete_jwt_cookie = True
        return cls(deleted=True)


class FMDJSONWebTokenBackend(JSONWebTokenBackend):
    """
    Authentication backend that rejects revoked tokens and handles decoding errors cleanly.
    """
    def authenticate(self, request=None, **kwargs):
        if request is None or getattr(request, "_jwt_token_auth", False):
            return None

        token = get_credentials(request, **kwargs)
        if token is not None:
            if is_token_revoked(token):
                return None
            try:
                return get_user_by_token(token, request)
            except exceptions.JSONWebTokenError:
                return None

        return None
