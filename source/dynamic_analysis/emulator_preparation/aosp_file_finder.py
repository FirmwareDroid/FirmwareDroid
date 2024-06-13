import os
from firmware_handler.firmware_file_exporter import start_firmware_file_export, NAME_EXPORT_FOLDER
from model import StoreSetting


def find_and_export_files(firmware, destination_folder, store_setting_id, format_name, search_pattern):
    """
    This function is used to process the shared libraries of a firmware. It extracts the shared libraries from the
    firmware and creates the shared library modules for AOSP firmware.

    :param firmware: class:'Firmware'
    :param destination_folder: str - path to the destination folder.
    :param store_setting_id: int - id of the store setting.
    :param format_name: str - format name of the shared library module.

    """

    firmware_id_list = [firmware.id]
    start_firmware_file_export(search_pattern, firmware_id_list, store_setting_id)
    store_setting = StoreSetting.objects.get(pk=store_setting_id)
    source_folder = os.path.join(
        store_setting.store_options_dict[store_setting.uuid]["paths"]["FIRMWARE_FOLDER_FILE_EXTRACT"],
        NAME_EXPORT_FOLDER,
        str(firmware.id))
    if not os.path.exists(source_folder):
        raise Exception(f"The source folder does not exist: {source_folder}")
    return source_folder

