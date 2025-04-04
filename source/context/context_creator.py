# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import functools
import logging
import sys


def create_db_context(f):
    """
    Decorator for creating an app context and pushing into to the context stack.

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


def create_db_context_subprocess(f):
    """
    Decorator for creating an app context and pushing into to the context stack.

    :param f: function to test for basic auth.
    :return: function

    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        from database.connector import reconnect
        from database.connector import multiprocess_disconnect_all
        alias = "default"
        multiprocess_disconnect_all()
        reconnect(alias)
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
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(f'%(asctime)s - %(processName)s/%(process)d - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def setup_thread_logging(log_level=logging.INFO):
    """
    Sets up logging for a thread, directing output to stdout with a thread-specific identifier.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(f'%(asctime)s - %(name)s - %(threadName)s/%(threadID)d - %(levelname)s '
                                      f'- %(message)s')
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)


def create_multithread_log_context(f):
    """
    Decorator for creating a log context for multiple threads.

    :param f: function to test for basic auth.
    :return: function

    """
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        setup_thread_logging()
        return f(*args, **kwargs)
    return decorated


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