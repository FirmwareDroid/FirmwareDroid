# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
from model import StoreSetting, ApplicationSetting
from model.StoreSetting import FILE_STORE_NAME_LIST
from multiprocessing import Lock
lock = Lock()

def get_application_setting():
    """
    Gets the application default settings.

    :return: class:'ApplicationSetting'

    """
    with lock:
        application_setting = ApplicationSetting.objects.first()
        if not application_setting:
            application_setting = create_application_setting()
    return application_setting


def get_store_setting(app_instance):
    """
    Gets the settings for the file store.

    :return: class:'StoreSetting'

    """
    with lock:
        store_setting = StoreSetting.objects.first()
        if not store_setting:
            store_setting = create_file_store_setting(app_instance)
    return store_setting


def get_active_store_path_dict(app_instance):
    """
    Gets a dict of the current active file storage.

    :return: dict() - From class:'StoreSetting' paths object.

    """
    store_setting = get_store_setting(app_instance)
    active_store = store_setting.active_store_name
    return store_setting.store_options_dict[active_store]["paths"]


def create_application_setting():
    """
    Creates a class:'ApplicationSetting' instance and saves it to the database.

    :return: class:'ApplicationSetting'

    """
    return ApplicationSetting(is_signup_active=True,
                              is_firmware_upload_active=True).save()


def create_file_store_setting(app_instance):
    """
    Creates a class:'StoreSetting' instance and saves it to the database. Sets the default options for the file store.

    :return: class:'StoreSetting'

    """

    store_options_dict = {}
    main_folder = app_instance.config["MAIN_FOLDER"]
    for file_store_name in FILE_STORE_NAME_LIST:
        store_options_dict[file_store_name] = {}
        file_storage_folder = main_folder + file_store_name + "/"
        store_options_dict[file_store_name]["paths"] = {}
        store_options_dict[file_store_name]["paths"]["FILE_STORAGE_FOLDER"] = file_storage_folder
        store_options_dict[file_store_name]["paths"]["FIRMWARE_FOLDER_IMPORT"] = file_storage_folder \
                                                                         + "firmware_import/"
        store_options_dict[file_store_name]["paths"]["FIRMWARE_FOLDER_IMPORT_FAILED"] = file_storage_folder \
                                                                                + "firmware_import_failed/"
        store_options_dict[file_store_name]["paths"]["FIRMWARE_FOLDER_STORE"] = file_storage_folder \
                                                                        + "firmware_store/"
        store_options_dict[file_store_name]["paths"]["FIRMWARE_FOLDER_APP_EXTRACT"] = file_storage_folder \
                                                                              + "android_app_store/"
        store_options_dict[file_store_name]["paths"]["FIRMWARE_FOLDER_FILE_EXTRACT"] = file_storage_folder \
                                                                               + "firmware_file_store/"
        store_options_dict[file_store_name]["paths"]["FIRMWARE_FOLDER_CACHE"] = file_storage_folder + "cache/"
        store_options_dict[file_store_name]["paths"]["LIBS_FOLDER"] = file_storage_folder + "libs/"
        setup_storage_folders(store_options_dict[file_store_name]["paths"])
    return StoreSetting(store_options_dict=store_options_dict).save()


def set_active_storage_folders(app_instance):
    """
    Sets the current active file storage to the app configuration and ensure that the folders exist.

    """
    store_setting = get_store_setting(app_instance)
    active_store = store_setting.active_store_name
    file_store_path_dict = store_setting.store_options_dict[active_store]["paths"]
    app_instance.config.update(
        FIRMWARE_FOLDER_IMPORT=file_store_path_dict["FIRMWARE_FOLDER_IMPORT"],
        FIRMWARE_FOLDER_IMPORT_FAILED=file_store_path_dict["FIRMWARE_FOLDER_IMPORT_FAILED"],
        FIRMWARE_FOLDER_STORE=file_store_path_dict["FIRMWARE_FOLDER_STORE"],
        FIRMWARE_FOLDER_APP_EXTRACT=file_store_path_dict["FIRMWARE_FOLDER_APP_EXTRACT"],
        FIRMWARE_FOLDER_FILE_EXTRACT=file_store_path_dict["FIRMWARE_FOLDER_FILE_EXTRACT"],
        FIRMWARE_FOLDER_CACHE=file_store_path_dict["FIRMWARE_FOLDER_CACHE"],
        LIBS_FOLDER=file_store_path_dict["LIBS_FOLDER"],
    )


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
