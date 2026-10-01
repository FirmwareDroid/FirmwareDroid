import logging
from typing import Optional, Tuple
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from graphql_jwt.utils import get_payload, get_user_by_payload
from graphql_jwt.settings import jwt_settings


class JWTCookieAuthentication(BaseAuthentication):
    """
    DRF authentication that:
    1. Tries Authorization header (Bearer|Token)
    2. Falls back to JWT cookie
    3. Checks token revocation list
    4. Returns (user, token) or None
    """

    header_prefixes = ("Bearer ", "Token ")

    def authenticate(self, request) -> Optional[Tuple[object, str]]:
        token = self._from_header(request) or self._from_cookie(request)
        if not token:
            return None
        payload, user = self._validate(token)
        if not user or isinstance(user, AnonymousUser):
            raise exceptions.AuthenticationFailed("Invalid user")
        if not user.is_active:
            raise exceptions.AuthenticationFailed("Inactive user")
        return (user, token)

    def _from_header(self, request) -> Optional[str]:
        auth = request.headers.get("Authorization")
        if not auth:
            return None
        for prefix in self.header_prefixes:
            if auth.startswith(prefix):
                parts = auth.split()
                if len(parts) != 2:
                    raise exceptions.AuthenticationFailed("Malformed Authorization header")
                return parts[1].strip()
        return None

    def _from_cookie(self, request) -> Optional[str]:
        graphql_jwt_settings = getattr(settings, "GRAPHQL_JWT", None) or getattr(settings, "GRAPHENE_FRAMEWORK_GRAPHQL_JWT", {})
        name = graphql_jwt_settings.get("JWT_COOKIE_NAME") or getattr(jwt_settings, "JWT_COOKIE_NAME", "JWT")
        val = request.COOKIES.get(name)
        return val.strip() if val else None

    def _validate(self, token: str):
        try:
            from webserver.jwt_auth import is_token_revoked
            if is_token_revoked(token):
                raise exceptions.AuthenticationFailed("Token has been revoked")
            payload = get_payload(token, jwt_settings.JWT_SECRET_KEY)
            user = get_user_by_payload(payload)
            if user is None:
                raise exceptions.AuthenticationFailed("User not found")
            return payload, user
        except exceptions.AuthenticationFailed:
            raise
        except Exception as e:
            logging.debug(f"JWT decode failed: {e}")
            raise exceptions.AuthenticationFailed("Invalid JWT token")
