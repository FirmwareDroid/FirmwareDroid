import os


class Config:
    """General Config"""
    DEBUG = False
    if os.environ['APP_ENV'] == "development":
        ENV = "DEV_"
    elif os.environ['APP_ENV'] == "production":
        ENV = ""
    elif os.environ['APP_ENV'] == "testing":
        os.environ['TESTING'] = "True"
        ENV = "TST_"
    else:
        ENV = "DEV_"


class ApplicationConfig(Config):
    """Config for productive builds"""

    ####################
    # Folder Config
    ####################
    MAIN_FOLDER = os.environ[Config.ENV+'APP_DATA_FOLDER']
    FILE_FOLDER = MAIN_FOLDER + "00_file_storage/"
    FIRMWARE_FOLDER_IMPORT = FILE_FOLDER + "firmware_import/"
    FIRMWARE_FOLDER_IMPORT_FAILED = FILE_FOLDER + "firmware_import_failed/"
    FIRMWARE_FOLDER_STORE = FILE_FOLDER + "firmware_store/"
    FIRMWARE_FOLDER_APP_EXTRACT = FILE_FOLDER + "android_app_store/"
    FIRMWARE_FOLDER_FILE_EXTRACT = FILE_FOLDER + "firmware_file_store/"
    FIRMWARE_FOLDER_CACHE = FILE_FOLDER + "cache/"
    LIBS_FOLDER = FILE_FOLDER + "libs/"
    ALL_FOLDERS = [FILE_FOLDER,
                   FIRMWARE_FOLDER_IMPORT,
                   FIRMWARE_FOLDER_IMPORT_FAILED,
                   FIRMWARE_FOLDER_STORE,
                   FIRMWARE_FOLDER_APP_EXTRACT,
                   FIRMWARE_FOLDER_FILE_EXTRACT,
                   FIRMWARE_FOLDER_CACHE]
    ####################
    # Redis Config
    ####################
    REDIS_HOST_PORT = os.environ[Config.ENV+'REDIS_HOST_PORT']
    ####################
    # RQ Config
    ####################
    RQ_DASHBOARD_PASSWORD = os.environ[Config.ENV+'RQ_DASHBOARD_PASSWORD']
    RQ_DASHBOARD_USERNAME = os.environ[Config.ENV+'RQ_DASHBOARD_USERNAME']
    RQ_DASHBOARD_REDIS_URL = os.environ[Config.ENV+'RQ_DASHBOARD_REDIS_URL']
    RQ_DASHBOARD_REDIS_AUTH_URL = f"redis://{RQ_DASHBOARD_USERNAME}:{RQ_DASHBOARD_PASSWORD}@{REDIS_HOST_PORT}"
    ####################
    # Basic Auth Config
    ####################
    BASIC_AUTH_USERNAME = os.environ[Config.ENV + 'BASIC_AUTH_USERNAME']
    BASIC_AUTH_PASSWORD = os.environ[Config.ENV + 'BASIC_AUTH_PASSWORD']
    BASIC_AUTH_FORCE = os.environ[Config.ENV + 'BASIC_AUTH_FORCE']
    ####################
    # JWT Auth Config
    ####################
    JWT_SECRET_KEY = os.environ[Config.ENV + 'JWT_SECRET_KEY']
    JWT_TOKEN_LOCATION = ["cookies"]
    JWT_COOKIE_SECURE = True
    if os.environ['APP_ENV'] == "development" or os.environ['APP_ENV'] == "testing" \
            or os.environ['JWT_CSRF_ACTIVE'] == "false":
        JWT_COOKIE_CSRF_PROTECT = False
        JWT_CSRF_CHECK_FORM = False
    else:
        JWT_CSRF_CHECK_FORM = True
        JWT_COOKIE_CSRF_PROTECT = True


    JWT_CSRF_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE"]
    JWT_COOKIE_SAMESITE = 'Strict'

    ####################
    # Flask Config
    ####################
    FLASK_ADMIN_MAIL = os.environ[Config.ENV + 'FLASK_ADMIN_MAIL']
    FLASK_ADMIN_PW = os.environ[Config.ENV + 'FLASK_ADMIN_PW']
    FLASK_ADMIN_USERNAME = os.environ[Config.ENV + 'FLASK_ADMIN_USERNAME']
    DOMAIN_NAME = os.environ[Config.ENV + 'DOMAIN_NAME']
    SERVER_NAME = DOMAIN_NAME
    MAX_CONTENT_LENGTH = 7 * 1024 * 1024 * 1024     # MAX File upload size
    ####################
    # DB Config
    ####################
    DB_REPLICA_SET = os.environ[Config.ENV + 'MONGODB_REPLICA_SET']
    DB_HOST = os.environ[Config.ENV + 'MONGODB_HOSTNAME']
    DB_HOST_PORT = int(os.environ[Config.ENV + 'MONGODB_PORT'])
    DB_NAME = os.environ[Config.ENV + 'MONGODB_DATABASE']
    DB_AUTH_SRC = os.environ[Config.ENV + 'MONGODB_AUTH_SRC']
    DB_URI = 'mongodb://' + os.environ[Config.ENV + 'MONGODB_USERNAME'] \
             + ':' + os.environ[Config.ENV + 'MONGODB_PASSWORD'] \
             + '@' + os.environ[Config.ENV + 'MONGODB_HOSTNAME'] \
             + ':' + str(DB_HOST_PORT) \
             + '/' + os.environ[Config.ENV + 'MONGODB_DATABASE']
    MONGODB_SETTINGS = {
        "db": DB_NAME,
        'username': os.environ[Config.ENV + 'MONGODB_USERNAME'],
        'password': os.environ[Config.ENV + 'MONGODB_PASSWORD'],
        "host": DB_HOST,
        "port": DB_HOST_PORT,
        "auth_src": DB_AUTH_SRC
    }
    ####################
    # REST API Config
    ####################
    API_TITLE = os.environ[Config.ENV + 'API_TITLE']
    API_VERSION = os.environ[Config.ENV + 'API_VERSION']
    API_DESCRIPTION = os.environ[Config.ENV + 'API_DESCRIPTION']
    API_PREFIX = os.environ[Config.ENV + 'API_PREFIX']
    API_DOC_FOLDER = os.environ[Config.ENV + 'API_DOC_FOLDER']
    ####################
    # Firmware Mass Import Config
    ####################
    MASS_IMPORT_NUMBER_OF_THREADS = os.environ[Config.ENV+'MASS_IMPORT_NUMBER_OF_THREADS']
    ####################
    # Mail Config
    ####################
    MAIL_SERVER = os.environ[Config.ENV + 'MAIL_SERVER']
    MAIL_PORT = os.environ[Config.ENV + 'MAIL_PORT']
    MAIL_USERNAME = os.environ[Config.ENV + 'MAIL_USERNAME']
    MAIL_PASSWORD = os.environ[Config.ENV + 'MAIL_PASSWORD']
    MAIL_DEFAULT_SENDER = os.environ[Config.ENV + 'MAIL_DEFAULT_SENDER']
    MAIL_SECRET_KEY = os.environ[Config.ENV + 'MAIL_SECRET_KEY']
    MAIL_SALT = os.environ[Config.ENV + 'MAIL_SALT']
