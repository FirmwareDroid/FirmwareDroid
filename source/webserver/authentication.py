import logging
from typing import Optional, Tuple
from django.contrib.auth.models import AnonymousUser
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from graphql_jwt.utils import get_payload, get_user_by_payload
from graphql_jwt.settings import jwt_settings
#
# class GraphQLJWTAuthentication(BaseAuthentication):
#     def authenticate(self, request):
#         auth_header = request.headers.get('Authorization')
#         if not auth_header or not auth_header.startswith('Bearer ') or not auth_header.startswith('Token '):
#             return None
#
#         token = auth_header.split(' ')[1]
#         try:
#             payload = get_payload(token, jwt_settings.JWT_SECRET_KEY)
#             user = get_user_by_payload(payload)
#             if user is None or not user.is_active:
#                 raise exceptions.AuthenticationFailed('User inactive or deleted')
#             return (user, None)
#         except Exception as e:
#             logging.error(e)
#             raise exceptions.AuthenticationFailed(f'Invalid JWT Token')

class JWTCookieAuthentication(BaseAuthentication):
    """
    DRF authentication that:
    1. Tries Authorization header (Bearer|Token)
    2. Falls back to JWT cookie
    3. Returns (user, token) or None
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
        name = settings.GRAPHQL_JWT.get("JWT_COOKIE_NAME") or jwt_settings.JWT_COOKIE_NAME
        val = request.COOKIES.get(name)
        return val.strip() if val else None

    def _validate(self, token: str):
        try:
            payload = get_payload(token, jwt_settings.JWT_SECRET_KEY)
            user = get_user_by_payload(payload)
            if user is None:
                raise exceptions.AuthenticationFailed("User not found")
            return payload, user
        except Exception as e:
            logging.debug(f"JWT decode failed: {e}")
            raise exceptions.AuthenticationFailed("Invalid JWT token")