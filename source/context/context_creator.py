# File: `source/context/context_creator.py`
# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import functools
import logging
import sys
from log4mongo.handlers import MongoHandler


def create_db_context(f):
    """
    Decorator for creating an app context and pushing into to the context stack.
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
        logger.setLevel(log_level)
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        formatter = logging.Formatter(f'%(asctime)s - %(processName)s/%(process)d - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger


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
    """

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        setup_thread_logging()
        return f(*args, **kwargs)

    return decorated


class TaggedMongoHandler(MongoHandler):
    def __init__(self, tags, details, *args, **kwargs):
        if not tags or not isinstance(tags, list):
            raise ValueError("A non-empty 'tag' must be provided to TaggedMongoHandler.")
        super().__init__(*args, **kwargs)
        self.tags = tags
        self.details = details

    # Model: ApkScannerLog
    def emit(self, record):
        if not hasattr(record, 'tags'):
            record.tags = self.tags
        if not hasattr(record,  'details'):
            record.details = self.details
        super().emit(record)


def setup_apk_scanner_logger(tags=None, details=None):
    if tags is None:
        tags = []
    from webserver.settings import MONGO_DATABASES
    logger = logging.getLogger("apk_scanner_logger")
    logger.setLevel(logging.DEBUG)
    if not any(h.__class__.__name__ == "TaggedMongoHandler" for h in logger.handlers):
        mongo_handler = TaggedMongoHandler(
            tags=tags,
            details=details,
            host=MONGO_DATABASES["default"]["host"],
            port=MONGO_DATABASES["default"]["port"],
            database_name=MONGO_DATABASES["default"]["db"],
            username=MONGO_DATABASES["default"]["username"],
            password=MONGO_DATABASES["default"]["password"],
            collection="apk_scanner_log",
            capped=True
        )
        mongo_handler.setLevel(logging.DEBUG)
        logger.addHandler(mongo_handler)
    return logger


def create_log_context(f):
    """
    Decorator for creating a log context and pushing into.
    """

    @functools.wraps(f)
    def decorated(*args, **kwargs):
        try:
            setup_logging()
        except Exception as e:
            pass
        return f(*args, **kwargs)

    return decorated
