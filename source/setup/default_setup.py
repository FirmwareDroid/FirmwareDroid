import logging
import redis_lock
from model import WebclientSetting
from model.StoreSetting import StoreSetting, create_file_store_setting, setup_storage_folders
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
        if not application_setting:
            logging.info("First application start detected.")
            application_setting = create_application_setting()
    return application_setting


def create_application_setting():
    """
    Creates a class:'WebclientSetting' instance and saves it to the database.

    :return: class:'WebclientSetting'

    """
    return WebclientSetting(is_signup_active=True,
                            is_firmware_upload_active=True).save()
