# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import json
import logging
from functools import wraps
from flask_jwt_extended import get_jwt, get_jwt_identity
from flask_jwt_extended import verify_jwt_in_request


def admin_jwt_required(fn):
    """Define a custom decorator for the role of an admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        """ Verifies the JWT is present in the request,
         as well as ensuring that this user has a role of `admin` in the access token
        """
        verify_jwt_in_request()
        claims = get_jwt_identity()
        claims = json.loads(claims)
        role_list = claims["role_list"]
        if role_list and 'admin' in role_list:
            return fn(*args, **kwargs)
        else:
            return "Unauthorized", 401

    return wrapper


def user_jwt_required(fn):
    """Define a custom decorator for the role of a user."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        """
        Verifies the JWT is present in the request,
        as well as ensuring that this user has a role of `user` in the access token
        """
        verify_jwt_in_request()
        claims = get_jwt_identity()
        claims = json.loads(claims)
        role_list = claims["role_list"]
        if role_list and ('user' or 'admin' in role_list):
            return fn(*args, **kwargs)
        else:
            return "Unauthorized", 401

    return wrapper


def jwt_required(fn):
    """Decorator for jwt of any role."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        """
        Verifies the JWT is present in the request.
        """
        verify_jwt_in_request()
        return fn(*args, **kwargs)

    return wrapper
