import functools

import flask
from secrets import compare_digest
from flask import request, Response


def check_auth(username, password):
    """This function is called to check if a username password combination is valid."""
    app = flask.current_app
    return compare_digest(username, app.config["BASIC_AUTH_USERNAME"]) and compare_digest(
        password, app.config["BASIC_AUTH_PASSWORD"])


def authenticate():
    """Sends a 401 response that enables basic auth."""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def basic_auth():
    """Ensure basic authorization."""
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return authenticate()


def requires_basic_authorization(f):
    """
    Decorator for basic authentication.
    :param f: function to test for basic auth.
    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated
