import json
import tempfile
import time
from sys import path

import rq
import os
import logging
import rq_dashboard
from bson import ObjectId
from flask import Flask
from flask_basicauth import BasicAuth
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from marshmallow import fields
from mongoengine import DoesNotExist, NotUniqueError
from pymongo.errors import OperationFailure
from redis import Redis
from api.v1.converter.BoolConverter import BoolConverter
from scripts.auth.jwt_auth import check_if_token_is_revoked
from model.UserAccount import RegistrationStatus
from scripts.config.app_settings import get_application_setting
from scripts.auth.basic_auth import basic_auth
from config import ApplicationConfig
from model import UserAccount
from scripts.database.database import init_db
from api.v1.decorators.jwt_claims import add_role_list_claims
from api.v1.routes.firmware import ns as firmware_namespace
from api.v1.routes.androguard import ns as androguard_namespace
from api.v1.routes.virustotal import ns as virustotal_namespace
from api.v1.routes.statistics import ns as statistics_namespace
from api.v1.routes.androwarn import ns as androwarn_namespace
from api.v1.routes.comparer import ns as comparer_namespace
from api.v1.routes.apkid import ns as apkid_namespace
from api.v1.routes.jobs import ns as jobs_namespace
from api.v1.routes.auth import ns as auth_namespace
from api.v1.routes.qark import ns as qark_namespace
from api.v1.routes.android_app import ns as android_app_namespace
from api.v1.routes.firmware_file import ns as firmware_file_namespace
from api.v1.routes.fuzzy_hashing import ns as fuzzy_hashing_namespace
from api.v1.routes.cleanup import ns as cleanup_namespace
from api.v1.routes.adb import ns as adb_namespace
from api.v1.routes.frida import ns as frida_namespace
from api.v1.routes.exodus import ns as exodus_namespace
from api.v1.routes.settings import ns as settings_namespace
from api.v1.routes.quark_engine import ns as quark_engine_namespace
from api.v1.routes.super_android_analyzer import ns as super_android_analyzer_namespace
from api.v1.routes.apkleaks import ns as apkleaks_namespace
from flask_restx import Api
from gevent.pywsgi import WSGIServer
from scripts.utils.file_utils.file_util import delete_files_in_folder
from flasgger import Swagger


def create_app():
    """Creates and configures an app instance with all extensions."""
    app_instance = Flask(__name__, instance_relative_config=True, static_url_path='/static')
    set_logging_config(app_instance)
    app_config = ApplicationConfig()
    app_instance.config.from_object(app_config)
    api = Api(title=app_instance.config["API_TITLE"],
              version=app_instance.config["API_VERSION"],
              description=app_instance.config["API_DESCRIPTION"],
              prefix=app_instance.config["API_PREFIX"],
              authorizations={
                  "basicAuth": {
                      "type": "basic"
                  }
              },
              security="basicAuth",
              doc=False,  # doc=app_instance.config["API_DOC_FOLDER"])
              add_specs=True)
    api.namespaces.clear()
    setup_jwt_auth(app_instance)
    setup_api_converter(app_instance)
    register_api_namespaces(api)
    setup_rq_dashboard(app_instance)
    setup_marshmallow(app_instance)
    app_instance.mongo_db = init_db(app_instance)
    setup_application_settings()
    setup_default_users(app_instance)
    setup_cors(app_instance)
    setup_folders(app_instance)
    setup_redis_and_rq(app_instance)
    api.init_app(app=app_instance)
    clear_cache(app_instance)
    setup_swagger_ui(app_instance, api)

    return app_instance


def set_logging_config(app_instance):
    """
    Setup the logging config.
    """
    app_instance.logger.setLevel(logging.INFO)
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging.INFO,
        datefmt='%Y-%m-%d %H:%M:%S')


def setup_redis_and_rq(app_instance):
    """
    Setup redis database for background tasks.
    :param app_instance: the app to configure.
    """
    app_instance.redis = Redis.from_url(app_instance.config["RQ_DASHBOARD_REDIS_URL"])
    app_instance.rq_task_queue_default = rq.Queue('default', connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_high = rq.Queue('high', connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_java = rq.Queue('java', connection=app_instance.redis, default_timeout=60 * 60)

    app_instance.rq_task_queue_androwarn = rq.Queue('androwarn', connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_androguard = rq.Queue('androguard', connection=app_instance.redis,
                                                     default_timeout=60 * 60)
    app_instance.rq_task_queue_apkid = rq.Queue('apkid', connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_virustotal = rq.Queue('virustotal', connection=app_instance.redis,
                                                     default_timeout=60 * 60)
    app_instance.rq_task_queue_exodus = rq.Queue('exodus', connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_frida = rq.Queue('frida', connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_fuzzyhash = rq.Queue('fuzzyhash', connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_quark_engine = rq.Queue('quark_engine', connection=app_instance.redis,
                                                       default_timeout=60 * 60)
    app_instance.rq_task_queue_qark = rq.Queue('qark', connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_super_android_analyzer = rq.Queue('super_android_analyzer',
                                                                 connection=app_instance.redis, default_timeout=60 * 60)
    app_instance.rq_task_queue_apkleaks = rq.Queue('apkleaks', connection=app_instance.redis, default_timeout=60 * 60)


def setup_rq_dashboard(app_instance):
    """
    Setup RQ-Dashboard route.
    :param app_instance: the app to configure.
    """
    rq_dashboard.blueprint.before_request(basic_auth)
    app_instance.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq-dashboard")


def setup_basic_auth(app_instance):
    """
    Add basic auth to the app instance.
    :param app_instance:
    :return:
    """
    app_instance.basic_auth = BasicAuth(app_instance)


def setup_cors(app_instance):
    """
    Default configuration for Cross-Origin Resource Sharing.
    :param app_instance: the app to configure.
    """
    # TODO - Disallow origins. Make Secure
    app_instance.cors = CORS(app_instance)


def setup_marshmallow(app_instance):
    """
    Setup the marshmallow lib for de-/serialization of objects.
    :param app_instance: the app to configure.
    """
    ma = Marshmallow(app_instance)
    ma.Schema.TYPE_MAPPING[ObjectId] = fields.Str()


def setup_jwt_auth(app_instance):
    """
    Add jwt authentication and decorators for api endpoints.
    :param app_instance: the flask app.
    """
    app_instance.bcrypt = Bcrypt(app_instance)
    app_instance.jwt = JWTManager(app_instance)
    app_instance.jwt.additional_claims_loader(add_role_list_claims)
    app_instance.jwt.token_in_blocklist_loader(check_if_token_is_revoked)


def setup_default_users(app_instance):
    """
    Creates the default admin user in the database if not already existing.
    :return:
    """
    username = app_instance.config["FLASK_ADMIN_USERNAME"]
    mail = app_instance.config["FLASK_ADMIN_MAIL"]
    password = app_instance.config["FLASK_ADMIN_PW"]
    try:
        UserAccount.objects.get(email=mail)
    except DoesNotExist:
        try:
            user = UserAccount(email=mail,
                               password=password,
                               active=True,
                               registration_status=RegistrationStatus.VERIFIED,
                               role_list=['admin', 'user'],
                               username=username)
            user.hash_password()
            user.save()
            logging.warning("Created default admin user in db! CHANGE YOUR PASSWORD ASAP!")
        except NotUniqueError:
            logging.info("Admin account already exists")


def register_api_namespaces(api):
    """
    Registers all namespaces and endpoints.
    :param api: REST api object.
    """
    api.add_namespace(androguard_namespace, path='/v1/androguard')
    api.add_namespace(androwarn_namespace, path='/v1/androwarn')
    api.add_namespace(auth_namespace, path='/v1/auth')
    api.add_namespace(comparer_namespace, path='/v1/comparer')
    api.add_namespace(firmware_namespace, path='/v1/firmware')
    api.add_namespace(jobs_namespace, path='/v1/jobs')
    api.add_namespace(qark_namespace, path='/v1/qark')
    api.add_namespace(statistics_namespace, path='/v1/statistics')
    api.add_namespace(virustotal_namespace, path='/v1/virustotal')
    api.add_namespace(apkid_namespace, path='/v1/apkid')
    api.add_namespace(android_app_namespace, path='/v1/android_app')
    api.add_namespace(firmware_file_namespace, path='/v1/firmware_file')
    api.add_namespace(fuzzy_hashing_namespace, path='/v1/fuzzy_hashing')
    api.add_namespace(cleanup_namespace, path='/v1/cleanup')
    api.add_namespace(adb_namespace, path='/v1/adb')
    api.add_namespace(frida_namespace, path='/v1/frida')
    api.add_namespace(exodus_namespace, path='/v1/exodus')
    api.add_namespace(settings_namespace, path='/v1/settings')
    api.add_namespace(quark_engine_namespace, path='/v1/quark_engine')
    api.add_namespace(super_android_analyzer_namespace, path='/v1/super_android_analyzer')
    api.add_namespace(apkleaks_namespace, path="/v1/apkleaks")


def setup_api_converter(app_instance):
    """
    Register route view converters.
    """
    app_instance.url_map.converters['bool'] = BoolConverter


def setup_folders(app_instance):
    """Creates basic folder structure of the app instance"""
    for path in app_instance.config["ALL_FOLDERS"]:
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            message = "Could not create folder: " + path
            logging.error(message)


def setup_application_settings():
    """
    Initializes the application settings.
    """
    connection_attempts = 0
    has_connected = False
    while not has_connected:
        if connection_attempts > 6:
            raise ConnectionError("Cannot connect to mongo-db! "
                                  "Maybe the DB was not initialized correctly or is temporarily unavailable.")
        try:
            get_application_setting()
            has_connected = True
        except OperationFailure:
            logging.warning(f"Attempt Mongo-DB connect failed. Reattempt {connection_attempts}")
            time.sleep(45)
            connection_attempts += 1


def clear_cache(app_instance):
    """
    Deletes all cache files.
    :param app_instance: flask app instance
    """
    cache_path = app_instance.config["FIRMWARE_FOLDER_CACHE"]
    delete_files_in_folder(cache_path)


def setup_swagger_ui(app_instance, api):
    """
    Configure swagger-ui and load api specification generated by flask restx.
    :param app_instance: flask app instance
    :param api: flask restx REST api
    """
    app_instance.c = {
        'title': app_instance.config["API_TITLE"],
        'uiversion': 3,
        'openapi': '3.0.2',
    }
    swagger_config = {
        "headers": [
        ],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/api/apispec_1.json',
                "rule_filter": lambda rule: True,  # all in
                "model_filter": lambda tag: True,  # all in
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    with app_instance.app_context():
        tmp_file = tempfile.NamedTemporaryFile(suffix=".json")
        tmp_file.write(bytes(json.dumps(api.__schema__), 'utf-8'))
        tmp_file.seek(0)
        swagger = Swagger(app_instance, config=swagger_config)
        swagger.load_swagger_file(tmp_file.name)
        tmp_file.close()


################################################################################
# APPLICATION MAIN ENTRY
################################################################################
app = create_app()

if __name__ == "__main__":
    http_server = WSGIServer(('0.0.0.0', int(os.environ['APP_PORT'])), app)
    http_server.serve_forever()
