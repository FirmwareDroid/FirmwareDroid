import logging
import os
from multiprocessing import Lock
lock = Lock()
from model import ApplicationSetting
from model.StoreSetting import StoreSetting
from webserver.settings import MAIN_FOLDER
import uuid

STORAGE_FOLDERS = ["00_file_storage", "01_file_storage"]


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
    Setup the file store if no store exists.

    :return: class:'StoreSetting'

    """
    with lock:
        store_setting_list = StoreSetting.objects.all()
        if len(store_setting_list) == 0:
            for storage_folder in STORAGE_FOLDERS:
                store_setting = create_file_store_setting(storage_folder)
        for store_setting in store_setting_list:
            for key in store_setting.store_options_dict.keys():
                store_dict = store_setting.store_options_dict[key]
                setup_storage_folders(store_dict["paths"])
    return store_setting


def setup_application_setting():
    """
    Gets the application default settings.

    :return: class:'ApplicationSetting'

    """
    with lock:
        application_setting = ApplicationSetting.objects.first()
        if not application_setting:
            application_setting = create_application_setting()
    return application_setting


def get_active_store_path_dict():
    """
    Gets a dict of the current active file storage.

    :return: dict() - From class:'StoreSetting' paths object.

    """
    store_setting = setup_file_store_setting()
    return store_setting.store_options_dict[store_setting.uuid]["paths"]


def create_application_setting():
    """
    Creates a class:'ApplicationSetting' instance and saves it to the database.

    :return: class:'ApplicationSetting'

    """
    return ApplicationSetting(is_signup_active=True,
                              is_firmware_upload_active=True).save()