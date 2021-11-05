# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import mongoengine
from flask_mongoengine import MongoEngine
from mongoengine import connection


def init_db(app):
    register_default_connection(app)
    mongo_db = MongoEngine(app)
    return mongo_db


def open_db_con(alias):
    """
    Opens a new mongoEngine db connection with the given alias.

    :param alias: a unique connection string not default.
    :return: (str) the connection alias

    """
    from app import app
    db_name, host, port, username, password = get_connection_options(app)
    mongoengine.connect(db=db_name, alias=alias, host=host, port=port, username=username, password=password)


def close_db_con(alias):
    """
    Closes mongoEngine connection by alias.

    :param alias: (str) the connection alias

    """
    mongoengine.disconnect(alias=alias)


def multiprocess_disconnect_all(app):
    """
    Disconnects all mongoEngine connections and then registers default connection.
    Workaround for using mongoEngine in a multiprocess environment:
    See link: https://stackoverflow.com/questions/49390825/using-mongoengine-with-multiprocessing-how-do-you-close-mongoengine-connection

    """
    if not app:
        from app import app
    mongoengine.disconnect_all()
    connection._connections = {}
    connection._connection_settings = {}
    connection._dbs = {}
    register_default_connection(app)


def register_default_connection(app):
    db_name, host, port, username, password = get_connection_options(app)
    mongoengine.register_connection(alias='default', db=db_name, host=host, port=port, username=username,
                                    password=password)


def reconnect(alias):
    """
    Reconnect if the alias is not connected.

    :param alias: str- connection alias
    :return: db connection or None

    """
    db_connection = None
    try:
        db_connection = mongoengine.get_connection(alias, True)
    except Exception as err:
        logging.error(str(err))
    return db_connection


def get_connection_options(app):
    """
    Gets the db connection configuration for mongodb.

    :param app: the current flask app instance.
    :return: db_name, host, port, username, password

    """
    db_name = app.config["MONGODB_SETTINGS"].get("db")
    host = app.config["MONGODB_SETTINGS"].get("host")
    port = app.config["MONGODB_SETTINGS"].get("port")
    username = app.config["MONGODB_SETTINGS"].get("username")
    password = app.config["MONGODB_SETTINGS"].get("password")
    return db_name, host, port, username, password


