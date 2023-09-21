# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import functools
import logging
import sys


def create_db_context(f):
    """
    Decorator for creating an app context and pushing into to the Flask context stack.

    :param f: function to test for basic auth.
    :return: function

    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        #sys.path.insert(0, '/var/www/source/')
        from database.connector import init_db
        from webserver.settings import MONGODB_DATABASES
        init_db(MONGODB_DATABASES["default"])

        #from app import create_app
        #app = create_app()
        #app.logger.setLevel(logging.INFO)
        #logging.getLogger().setLevel(logging.INFO)
        #app.app_context().push()
        #logging.info(*args, **kwargs)
        return f(*args, **kwargs)
    return decorated


@create_db_context
def create_app_context():
    """
    Creates a new db app context via decorator.
    """
    return None


