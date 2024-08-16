import glob
import logging
import os
import shutil
import redis_lock
from model import WebclientSetting, ServerSetting, FirmwareImporterSetting
from model.FirmwareImporterSetting import create_firmware_importer_setting
from model.ServerSetting import create_server_setting
from model.StoreSetting import StoreSetting, create_file_store_setting, setup_storage_folders
from model.WebclientSetting import create_webclient_setting
from webserver.settings import MAIN_FOLDER, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from redis import StrictRedis

logging.debug((REDIS_HOST, REDIS_PORT))
redis_con = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
redis_con.ping()


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
            for x in range(0, 10):
                if x == 0:
                    is_active = True
                else:
                    is_active = False
                store_setting = create_file_store_setting(MAIN_FOLDER, f"0{x}_file_storage", is_active)
                setup_store_folders([store_setting])

        if store_setting is None:
            store_setting = store_setting_list[0]

    return store_setting


def clear_cache(store_setting):
    """
    Clear the cache on disk of the server.
    """
    try:
        store_paths = store_setting.get_store_paths()
        cache_path = store_paths["FIRMWARE_FOLDER_CACHE"]
        file_list = glob.glob(os.path.join(cache_path, "*"))
        for file_path in file_list:
            if os.path.exists(file_path) and os.path.isdir(file_path):
                shutil.rmtree(file_path)
            elif os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
    except Exception as e:
        logging.debug(f"Error while deleting cache: {e}")


def setup_store_folders(store_setting_list):
    """
    Creates the folder structure for a list of store settings.

    :param store_setting_list: list(class:`StoreSetting`)

    """
    for store_setting in store_setting_list:
        for key in store_setting.store_options_dict.keys():
            store_dict = store_setting.store_options_dict[key]
            setup_storage_folders(store_dict["paths"])
            clear_cache(store_setting)


def locked_setting_setup(setting_document_type, create_function, lock_name="fmd_app_setup"):
    """
    Lock the setup of a setting document type.

    :param setting_document_type: class:`Document`
    :param create_function: function

    :return: class:`Document`

    """
    with redis_lock.Lock(redis_con, lock_name):
        try:
            setting = setting_document_type.objects.first()
        except Exception as e:
            logging.debug(f"Error while getting setting: {e}")
            setting = None
        if setting is None:
            logging.info(f"First application start detected for {setting_document_type}.")
            setting = create_function()
    return setting


def add_setting_references(server_setting, store_setting, webclient_setting, firmware_importer_setting):
    """
    Add the references to the setting documents.

    :param server_setting: class:'ServerSetting'
    :param store_setting: class:'StoreSetting'
    :param webclient_setting: class:'WebclientSetting'
    :param firmware_importer_setting: class:'FirmwareImporterSetting'

    """
    server_setting.store_setting_reference = store_setting.pk
    server_setting.webclient_setting_reference = webclient_setting.pk
    server_setting.firmware_importer_setting_reference = firmware_importer_setting.pk
    server_setting.save()
    store_setting.server_setting_reference = server_setting.pk
    store_setting.save()
    webclient_setting.server_setting_reference = server_setting.pk
    webclient_setting.save()
    firmware_importer_setting.server_setting_reference = server_setting.pk
    firmware_importer_setting.save()


def setup_default_settings():
    """
    Setup the default setting documents for FMD.

    :return: class:'ServerSetting'

    """
    with redis_lock.Lock(redis_con, "fmd_default_setup"):
        webclient_setting = locked_setting_setup(WebclientSetting, create_webclient_setting)
        store_setting = setup_file_store_setting()
        firmware_importer_setting = locked_setting_setup(FirmwareImporterSetting, create_firmware_importer_setting)
        server_setting = locked_setting_setup(ServerSetting, create_server_setting)
        add_setting_references(server_setting, store_setting, webclient_setting, firmware_importer_setting)
    return server_setting
