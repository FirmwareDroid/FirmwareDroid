import os
import shutil
from api.v2.types.GenericDeletion import delete_queryset_background
from context.context_creator import create_db_context, create_log_context
from firmware_handler.firmware_importer import import_firmware_from_store
from model import AndroidFirmware


@create_db_context
@create_log_context
def start_firmware_reimport(firmware_id_list):
    """
    The reimporter is a function that reimports firmware files into the importer queue.

    First, copies the firmware into the importer queue.
    Second, deletes the firmware from the database.
    Third, runs the firmware importer.
    
    :param firmware_id_list: list(str) - ids of class:'AndroidFirmware'
    
    """
    for firmware_id in firmware_id_list:
        android_firmware = AndroidFirmware.objects.get(pk=firmware_id)
        store_setting = android_firmware.get_store_setting()
        store_path = store_setting.store_options_dict[store_setting.uuid]["paths"]
        storage_index = store_setting.storage_index
        importer_path = store_path["FIRMWARE_FOLDER_IMPORT"]
        copy_firmware_to_importer(android_firmware, importer_path)
        delete_queryset_background()
        import_firmware_from_store(storage_index, create_fuzzy_hashes=True)


def copy_firmware_to_importer(android_firmware, importer_path):
    if not os.path.exists(importer_path):
        raise FileNotFoundError(f"File {importer_path} not found.")
    if not os.path.exists(android_firmware.absolute_store_path):
        raise FileNotFoundError(f"File {android_firmware.absolute_store_path} not found.")
    shutil.copyfile(android_firmware.absolute_store_path, importer_path)
    if not os.path.exists(importer_path):
        raise FileNotFoundError(f"File {importer_path} not found.")

