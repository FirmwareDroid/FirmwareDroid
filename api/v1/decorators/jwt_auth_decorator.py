from functools import wraps
from flask_jwt_extended import (verify_jwt_in_request, get_jwt_claims)


def admin_required(fn):
    """Define a custom decorator for the role of an admin."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        """ Verifies the JWT is present in the request,
         as well as ensuring that this user has a role of `admin` in the access token
        """
        verify_jwt_in_request()
        claims = get_jwt_claims()
        if claims['roles'] != 'admin':
            return "Unauthorized", 401
        else:
            return fn(*args, **kwargs)
    return wrapper
