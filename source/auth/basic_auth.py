# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.

import functools
# import flask
from secrets import compare_digest
# from flask import request, Response


def check_auth(username, password):
    """
    This function is called to check if a username password combination is valid.

    :return: bool - true if valid combination.

    """
    app = flask.current_app
    return compare_digest(username, app.config["BASIC_AUTH_USERNAME"]) and compare_digest(
        password, app.config["BASIC_AUTH_PASSWORD"])


def get_authentication_request():
    """
    Sends a 401 response that enables basic auth.

    :return: Flask-Response object

    """
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'}
    )


def basic_auth():
    """
    Ensure basic authorization.

    :return: Flask-Response object
    """
    auth = request.authorization
    if not auth or not check_auth(auth.username, auth.password):
        return get_authentication_request()


def requires_basic_authorization(f):
    """
    Decorator for basic authentication.

    :param f: function to test for basic auth.
    :return: function

    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return get_authentication_request()
        return f(*args, **kwargs)
    return decorated
