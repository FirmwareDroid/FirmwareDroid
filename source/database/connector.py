# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import functools
import logging
import uuid
import mongoengine
from mongoengine import connection


def test_connection():
    """

    :return:
    """
    from model import WebclientSetting
    application_setting = WebclientSetting.objects.first()


def multiprocess_disconnect_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        multiprocess_disconnect_all()
        return func(*args, **kwargs)
    return wrapper


def multiprocess_disconnect_all():
    """
    Disconnects all mongoEngine connections and then registers default connection.
    Workaround for using mongoEngine in a multiprocess environment:
    See link: https://stackoverflow.com/questions/49390825/using-mongoengine-with-multiprocessing-how-do-you-close-mongoengine-connection

    """
    from webserver.settings import MONGO_DATABASES
    #mongoengine.disconnect_all()
    mongoengine.disconnect()
    connection._connections = {}
    connection._connection_settings = {}
    connection._dbs = {}


@multiprocess_disconnect_db_connection
def init_db(db_settings):
    """
    Register a new mongoengine default connection

    :param db_settings: dict - with mongodb configuration.

    :return: mongoengine database connection object.

    """
    alias = uuid.uuid4()
    register_connection(db_settings, alias='default', connect=True, maxPoolSize=100)
    db_con = open_db_connection(db_settings, str(alias))
    register_connection(db_settings, str(alias))
    test_connection()
    return db_con


def open_db_connection(db_settings, alias):
    """
    Opens a new mongoEngine db connection with the given alias.

    :param db_settings: dict - with mongodb configuration.
    :param alias: a unique connection string not default.

    :return: (str) the connection alias

    """
    db_name, host, port, username, password, authentication_source, auth_mechanism = get_connection_options(db_settings)
    return mongoengine.connect(db=db_name,
                               alias=alias,
                               host=host,
                               port=port,
                               username=username,
                               password=password,
                               authentication_source=authentication_source,
                               authentication_mechanism=auth_mechanism)


def close_db_con(alias):
    """
    Closes mongoEngine connection by alias.

    :param alias: (str) the connection alias

    """
    mongoengine.disconnect(alias=alias)


def register_connection(db_settings, alias='default', connect=True, maxPoolSize=10):
    db_name, host, port, username, password, authentication_source, auth_mechanism = get_connection_options(db_settings)
    mongoengine.register_connection(alias=alias,
                                    db=db_name,
                                    host=host,
                                    port=port,
                                    username=username,
                                    password=password,
                                    authentication_mechanism=auth_mechanism,
                                    authentication_source=authentication_source,
                                    maxPoolSize=maxPoolSize,
                                    connect=connect)


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


def get_connection_options(db_settings):
    """
    Gets the db connection configuration for mongodb.

    :param db_settings: dict - with mongodb configuration.

    :return: db_name, host, port, username, password

    """
    db_name = db_settings.get("db")
    host = db_settings.get("host")
    port = db_settings.get("port")
    username = db_settings.get("username")
    password = db_settings.get("password")
    authentication_source = db_settings.get("authSource")
    auth_mechanism = db_settings.get("authMechanism")
    return db_name, host, port, username, password, authentication_source, auth_mechanism
