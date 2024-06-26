# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import functools
import logging
import sys
import secrets


def create_db_context(f):
    """
    Decorator for creating an app context and pushing into to the Flask context stack.

    :param f: function to test for basic auth.
    :return: function

    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from database.connector import init_db
        from webserver.settings import MONGO_DATABASES
        init_db(MONGO_DATABASES["default"])
        return f(*args, **kwargs)
    return decorated


@create_db_context
def create_app_context():
    """
    Creates a new db app context via decorator.
    """
    return None


def setup_logging(log_level=logging.INFO):
    """
    Setup logging for the application.
    """
    logger = logging.getLogger()
    if not logger.handlers:
        unique_string = secrets.token_hex(5)
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(f'%(asctime)s - %(name)s - {unique_string} - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def create_log_context(f):
    """
    Decorator for creating a log context and pushing into.

    :param f: function to test for basic auth.
    :return: function

    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        setup_logging()
        return f(*args, **kwargs)
    return decorated