import os


class Config:
    """General Config"""
    MAIN_FOLDER = os.environ['APP_DATA_FOLDER']
    FILE_FOLDER = MAIN_FOLDER + "00_file_storage/"
    FIRMWARE_FOLDER_IMPORT = FILE_FOLDER + "import/"
    FIRMWARE_FOLDER_IMPORT_FAILED = FILE_FOLDER + "import_failed/"
    FIRMWARE_FOLDER_STORE = FILE_FOLDER + "store/"
    FIRMWARE_FOLDER_APP_EXTRACT = FILE_FOLDER + "app_extract/"
    FIRMWARE_FOLDER_FILE_EXTRACT = FILE_FOLDER + "file_extract/"
    FIRMWARE_FOLDER_CACHE = FILE_FOLDER + "cache/"
    LIBS_FOLDER = FILE_FOLDER + "libs/"
    ALL_FOLDERS = [FILE_FOLDER,
                   FIRMWARE_FOLDER_IMPORT,
                   FIRMWARE_FOLDER_IMPORT_FAILED,
                   FIRMWARE_FOLDER_STORE,
                   FIRMWARE_FOLDER_APP_EXTRACT,
                   FIRMWARE_FOLDER_FILE_EXTRACT,
                   FIRMWARE_FOLDER_CACHE]
    MASS_IMPORT_NUMBER_OF_THREADS = os.environ['MASS_IMPORT_NUMBER_OF_THREADS']


class ApplicationConfig(Config):
    """Config for productive builds"""
    DEBUG = False
    development = ""
    if os.environ['APP_ENV'] == "development":
        development = "DEV_"

    if os.environ['APP_ENV'] == "production":
        RQ_DASHBOARD_PASSWORD = os.environ['RQ_DASHBOARD_PASSWORD']
        REDIS_HOST_PORT = os.environ['REDIS_HOST_PORT']
        RQ_DASHBOARD_USERNAME = os.environ['RQ_DASHBOARD_USERNAME']
        RQ_DASHBOARD_REDIS_URL = os.environ['RQ_DASHBOARD_REDIS_URL']
        RQ_DASHBOARD_REDIS_AUTH_URL = f"redis://{RQ_DASHBOARD_USERNAME}:{RQ_DASHBOARD_PASSWORD}@{REDIS_HOST_PORT}"
        BASIC_AUTH_USERNAME = os.environ[development+'BASIC_AUTH_USERNAME']
        BASIC_AUTH_PASSWORD = os.environ[development+'BASIC_AUTH_PASSWORD']
        BASIC_AUTH_FORCE = os.environ['BASIC_AUTH_FORCE']
        JWT_SECRET_KEY = os.environ[development+'JWT_SECRET_KEY']
        FLASK_ADMIN_MAIL = os.environ[development+'FLASK_ADMIN_MAIL']
        FLASK_ADMIN_PW = os.environ[development+'FLASK_ADMIN_PW']
        DB_HOST = os.environ[development+'MONGODB_HOSTNAME']
        DB_HOST_PORT = int(os.environ[development+'MONGODB_PORT'])
        DB_NAME = os.environ[development+'MONGODB_DATABASE']
        DB_URI = 'mongodb://' + os.environ[development+'MONGODB_USERNAME'] \
                 + ':' + os.environ[development+'MONGODB_PASSWORD'] \
                 + '@' + os.environ[development+'MONGODB_HOSTNAME'] \
                 + ':' + str(DB_HOST_PORT) \
                 + '/' + os.environ[development+'MONGODB_DATABASE']
        MONGODB_SETTINGS = {
            "db": DB_NAME,
            'username': os.environ[development+'MONGODB_USERNAME'],
            'password': os.environ[development+'MONGODB_PASSWORD'],
            "host": DB_HOST,
            "port": DB_HOST_PORT,
        }
        API_TITLE = os.environ[development+'API_TITLE']
        API_VERSION = os.environ[development+'API_VERSION']
        API_DESCRIPTION = os.environ[development+'API_DESCRIPTION']
        API_PREFIX = os.environ[development+'API_PREFIX']
        API_DOC_FOLDER = os.environ[development+'API_DOC_FOLDER']
