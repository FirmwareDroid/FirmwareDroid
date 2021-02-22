import logging
import os
import shutil
import flask
import mongoengine
from flask_mongoengine import MongoEngine
from mongoengine import connection
from model import AndroidFirmware
from scripts.rq_tasks.task_util import create_app_context


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
    :return:
    """
    mongoengine.disconnect(alias=alias)


def multiprocess_disconnect_all(app):
    """
    Disconnects all mongoEngine connections and then registers default connection.
    Workaround for using mongoEngine in a multiprocess environment:
    See link: https://stackoverflow.com/questions/49390825/using-mongoengine-with-multiprocessing-how-do-you-close-mongoengine-connection
    :return:
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


def clear_firmware_database():
    """
    Deletes all firmware and related objects from the database.
    Moves the store firmware-files to the import folder and deletes all extracted app on the disk.
    """
    create_app_context()
    app = flask.current_app
    import_dir_path = app.config["FIRMWARE_FOLDER_IMPORT"]
    app_store_path = app.config["FIRMWARE_FOLDER_APP_EXTRACT"]
    if not os.path.exists(import_dir_path):
        raise OSError("Import folder does not exist!")
    firmware_list = AndroidFirmware.objects()
    for firmware in firmware_list:
        destination_path = os.path.join(import_dir_path, firmware.original_filename)
        app_store_firmware_path = os.path.join(app_store_path, firmware.md5)
        try:
            shutil.move(firmware.absolute_store_path, destination_path)
            shutil.rmtree(app_store_firmware_path)
            firmware.delete()
        except OSError as err:
            logging.error(str(err))
