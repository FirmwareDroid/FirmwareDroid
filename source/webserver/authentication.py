import logging

from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from graphql_jwt.utils import get_payload, get_user_by_payload
from graphql_jwt.settings import jwt_settings

class GraphQLJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None

        token = auth_header.split(' ')[1]
        try:
            payload = get_payload(token, jwt_settings.JWT_SECRET_KEY)
            user = get_user_by_payload(payload)
            if user is None or not user.is_active:
                raise exceptions.AuthenticationFailed('User inactive or deleted')
            return (user, None)
        except Exception as e:
            logging.error(e)
            raise exceptions.AuthenticationFailed(f'Invalid JWT Token')