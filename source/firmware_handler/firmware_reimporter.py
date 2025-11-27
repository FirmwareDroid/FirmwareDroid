import logging
import os
import shutil
from api.v2.types.GenericDeletion import delete_queryset_background
from context.context_creator import create_db_context, create_apk_scanner_log_context
from firmware_handler.firmware_importer import import_firmware_from_store
from model import AndroidFirmware, StoreSetting


@create_db_context
@create_apk_scanner_log_context
def start_firmware_re_import(firmware_id_list, create_fuzzy_hashes=False):
    """
    The reimporter is a function that reimports firmware files into the importer queue.

    First, copies the firmware into the importer queue.
    Second, deletes the firmware from the database.
    Third, runs the firmware importer.
    
    :param create_fuzzy_hashes: boolean - True: will create fuzzy hashes for all files in the firmware found.
    :param firmware_id_list: list(str) - ids of class:'AndroidFirmware'
    
    """
    logging.info(f"Starting re-import of firmware with ids: {firmware_id_list}")

    store_dict = bundle_firmware_to_store_dict(firmware_id_list)
    logging.info(f"Created firmware bundle: {store_dict.items()}")
    for store_setting_pk, firmware_list in store_dict.items():
        store_setting = StoreSetting.objects.get(pk=store_setting_pk)
        store_path = store_setting.store_options_dict[store_setting.uuid]["paths"]
        importer_path = store_path["FIRMWARE_FOLDER_IMPORT"]
        importer_path = os.path.abspath(importer_path)
        for android_firmware in firmware_list:
            copy_firmware_to_importer(android_firmware, importer_path)
        firmware_id_list = [firmware.pk for firmware in firmware_list]
        delete_queryset_background(firmware_id_list, AndroidFirmware)
        import_firmware_from_store(store_setting, create_fuzzy_hashes=create_fuzzy_hashes)


def bundle_firmware_to_store_dict(firmware_id_list):
    """
    Bundles firmware files to store settings.

    :param firmware_id_list: str - ids of class:'AndroidFirmware'

    :return: dict - key: store_setting.pk, value: list of class:'AndroidFirmware'
    """
    store_dict = {}
    android_firmware_list = AndroidFirmware.objects.filter(pk__in=firmware_id_list)
    logging.info(f"Found firmware files: {len(android_firmware_list)}")
    for android_firmware in android_firmware_list:
        store_setting = android_firmware.get_store_setting()
        if store_setting.pk in store_dict:
            store_dict[store_setting.pk].append(android_firmware)
        else:
            store_dict[store_setting.pk] = [android_firmware]
    return store_dict


def copy_firmware_to_importer(android_firmware, importer_path):
    """
    Copies the firmware file to the importer path.

    :param android_firmware: class:'AndroidFirmware'
    :param importer_path: str - path to the importer folder of the store setting.

    """
    if not os.path.exists(importer_path):
        raise FileNotFoundError(f"File {importer_path} not found.")
    if not os.path.exists(android_firmware.absolute_store_path):
        raise FileNotFoundError(f"File {android_firmware.absolute_store_path} not found.")
    import_file_path = os.path.join(importer_path, android_firmware.original_filename)
    shutil.copyfile(android_firmware.absolute_store_path, import_file_path, follow_symlinks=False)
    if not os.path.exists(importer_path):
        raise FileNotFoundError(f"File {importer_path} not found.")
    logging.info(f"Copied firmware with id: {android_firmware.pk} to importer path: {import_file_path}")

