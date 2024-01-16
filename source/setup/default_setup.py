import logging
import os
import redis_lock
from model import WebclientSetting
from model.StoreSetting import StoreSetting
from webserver.settings import MAIN_FOLDER, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT, DJANGO_SUPERUSER_PASSWORD, \
    DJANGO_SUPERUSER_USERNAME, DJANGO_SUPERUSER_EMAIL
import uuid
from redis import StrictRedis


logging.debug((REDIS_HOST, REDIS_PORT))
redis_con = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
redis_con.ping()
DEFAULT_STORAGE_FOLDER = "00_file_storage"


def create_file_store_setting(storage_folder):
    """
    Creates a class:'StoreSetting' instance and saves it to the database. Sets the default options for the file store.

    :return: class:'StoreSetting'

    """
    store_options_dict = {}
    uuid_str = str(uuid.uuid4())
    file_storage_folder = MAIN_FOLDER + storage_folder + "/" + uuid_str + "/"
    store_options_dict[uuid_str] = {}
    store_options_dict[uuid_str]["paths"] = {}
    store_options_dict[uuid_str]["paths"]["FILE_STORAGE_FOLDER"] = file_storage_folder
    store_options_dict[uuid_str]["paths"]["FIRMWARE_FOLDER_IMPORT"] = file_storage_folder \
                                                                      + "firmware_import/"
    store_options_dict[uuid_str]["paths"]["FIRMWARE_FOLDER_IMPORT_FAILED"] = file_storage_folder \
                                                                             + "firmware_import_failed/"
    store_options_dict[uuid_str]["paths"]["FIRMWARE_FOLDER_STORE"] = file_storage_folder \
                                                                     + "firmware_store/"
    store_options_dict[uuid_str]["paths"]["FIRMWARE_FOLDER_APP_EXTRACT"] = file_storage_folder \
                                                                           + "android_app_store/"
    store_options_dict[uuid_str]["paths"]["FIRMWARE_FOLDER_FILE_EXTRACT"] = file_storage_folder \
                                                                            + "firmware_file_store/"
    store_options_dict[uuid_str]["paths"]["FIRMWARE_FOLDER_CACHE"] = file_storage_folder + "cache/"
    store_options_dict[uuid_str]["paths"]["LIBS_FOLDER"] = file_storage_folder + "libs/"
    setup_storage_folders(store_options_dict[uuid_str]["paths"])

    return StoreSetting(store_options_dict=store_options_dict, uuid=uuid_str).save()


def setup_storage_folders(paths_dict):
    """
    Creates the folder structure for the file storage.

    """
    for path in paths_dict.values():
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError as exception:
            message = f"Could not create folder: {path} - Exception: {exception}"
            logging.warning(message)


def setup_file_store_setting():
    """
    Setup the default file store at startup of the application. Several stores can exist but only one is setup by
    default.

    :return: class:'StoreSetting'

    """
    with redis_lock.Lock(redis_con, "fmd_app_setup"):
        store_setting = None
        store_setting_list = StoreSetting.objects.all().order_by('create_date')
        setup_store_folders(store_setting_list)

        if len(store_setting_list) == 0:
            store_setting = create_file_store_setting(DEFAULT_STORAGE_FOLDER)
            setup_store_folders([store_setting])

        if store_setting is None:
            store_setting = store_setting_list[0]

    return store_setting


def setup_store_folders(store_setting_list):
    """
    Creates the folder structure for a list of store settings.

    :param store_setting_list: list(class:`StoreSetting`)

    """
    for store_setting in store_setting_list:
        for key in store_setting.store_options_dict.keys():
            store_dict = store_setting.store_options_dict[key]
            setup_storage_folders(store_dict["paths"])


def setup_application_setting():
    """
    Save the default settings for webclients to the database.

    :return: class:'WebclientSetting'

    """
    with redis_lock.Lock(redis_con, "fmd_app_setup"):
        application_setting = WebclientSetting.objects.first()
        #create_default_django_superuser()
        if not application_setting:
            logging.info("First application start detected.")
            application_setting = create_application_setting()
    return application_setting


def get_active_file_store_paths():
    """
    Gets a dict containing the paths of the current active file storage.

    :return: dict() - From class:'StoreSetting' paths object.

    """
    store_setting = StoreSetting.objects(is_active=True).first()
    return store_setting.store_options_dict[store_setting.uuid]["paths"]


def create_application_setting():
    """
    Creates a class:'WebclientSetting' instance and saves it to the database.

    :return: class:'WebclientSetting'

    """
    return WebclientSetting(is_signup_active=True,
                            is_firmware_upload_active=True).save()


def create_default_django_superuser():
    """
    Create the default superuser for the django webserver.

    """
    from setup.models import User
    if not User.objects.filter(username=DJANGO_SUPERUSER_USERNAME).exists():
        user = User.objects.create_superuser(username=DJANGO_SUPERUSER_USERNAME,
                                             email=DJANGO_SUPERUSER_EMAIL,
                                             password=DJANGO_SUPERUSER_PASSWORD)
        user.save()
