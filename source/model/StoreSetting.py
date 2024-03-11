# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import datetime
import logging
import os
from mongoengine import DateTimeField, DictField, BooleanField, StringField, Document


class StoreSetting(Document):
    create_date = DateTimeField(default=datetime.datetime.now)
    store_options_dict = DictField(required=True)
    is_active = BooleanField(required=True, default=False)
    uuid = StringField(required=True, unique=True)
    storage_root = StringField(required=True, unique=True)


def setup_storage_folders(paths_dict):
    """
    Creates the folder structure for the file storage.

    """
    for path in paths_dict.values():
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError as exception:
            logging.debug(f"Could not create folder: {path} - Exception: {exception}")


def create_file_store_setting(docker_root_folder, storage_folder, is_active):
    """
    Creates a class:'StoreSetting' instance and saves it to the database. Sets the default options for the file store.

    :param is_active: bool - If the store is active.
    :param storage_folder: str - The folder name for the storage.
    :param docker_root_folder: str - The root folder within the container.

    :return: class:'StoreSetting' - A store document that holds the storage options.
    """
    import uuid
    store_options_dict = {}
    uuid_str = str(uuid.uuid4())
    file_storage_folder = docker_root_folder + storage_folder + "/" + uuid_str + "/"
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
    store_options_dict[uuid_str]["paths"]["ANDROID_APP_IMPORT"] = file_storage_folder \
                                                                  + "android_app_import/"
    store_options_dict[uuid_str]["paths"]["ANDROID_APP_IMPORT_FAILED"] = file_storage_folder \
                                                                         + "android_app_import_failed/"
    store_options_dict[uuid_str]["paths"]["FIRMWARE_FOLDER_FILE_EXTRACT"] = file_storage_folder \
                                                                            + "firmware_file_store/"
    store_options_dict[uuid_str]["paths"]["FIRMWARE_FOLDER_CACHE"] = file_storage_folder + "cache/"
    store_options_dict[uuid_str]["paths"]["LIBS_FOLDER"] = file_storage_folder + "libs/"
    setup_storage_folders(store_options_dict[uuid_str]["paths"])

    return StoreSetting(store_options_dict=store_options_dict,
                        uuid=uuid_str,
                        is_active=is_active,
                        storage_root=storage_folder).save()


def get_active_store_by_uuid(uuid):
    """
    Returns the store setting by the uuid.

    :raises: ValueError: If no active store setting found for the index.

    :return: class:'StoreSetting' - A store document that holds the storage options.
    """
    store_setting = StoreSetting.objects(is_active=True, uuid=uuid).first()
    if store_setting is None:
        raise ValueError(f"No active store setting found for index {uuid}")

    return store_setting


def get_active_store_paths_by_uuid(uuid):
    store_setting = get_active_store_by_uuid(uuid)
    return store_setting.store_options_dict[store_setting.uuid]["paths"]


def get_active_store_paths_by_index(storage_index):
    store_setting = get_active_store_by_index(storage_index)
    return store_setting.store_options_dict[store_setting.uuid]["paths"]


def get_active_store_by_index(storage_index):
    """
    Returns the store setting by the index.

    :raises: ValueError: If no active store setting found for the index.

    :return: class:'StoreSetting' - A store document that holds the storage options.
    """
    store_setting = StoreSetting.objects(is_active=True, storage_root=f"0{storage_index}_file_storage").first()
    if store_setting is None:
        raise ValueError(f"No active store setting found for index {storage_index}")

    return store_setting




