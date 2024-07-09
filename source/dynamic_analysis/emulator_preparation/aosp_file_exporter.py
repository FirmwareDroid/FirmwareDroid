import os
from firmware_handler.firmware_file_exporter import start_regex_firmware_file_export, NAME_EXPORT_FOLDER
from model import StoreSetting


def export_files_by_regex(firmware, store_setting_id, search_pattern):
    """
    This function is used to process the shared libraries of a firmware. It extracts the shared libraries from the
    firmware and creates the shared library modules for AOSP firmware.

    :param firmware: class:'Firmware'
    :param store_setting_id: int - id of the store setting.
    :param search_pattern: regex - search pattern for the shared library.

    """
    firmware_id_list = [firmware.id]
    start_regex_firmware_file_export(search_pattern, firmware_id_list, store_setting_id)


def get_firmware_export_folder_root(store_setting_id, firmware):
    """
    Get the file export folder for the firmware.

    :param store_setting_id: str - id of the store setting.
    :param firmware: class:'Firmware'

    :return: str - path to the file export folder.

    """
    store_setting = StoreSetting.objects.get(pk=store_setting_id)
    source_folder = os.path.join(
        store_setting.store_options_dict[store_setting.uuid]["paths"]["FIRMWARE_FOLDER_FILE_EXTRACT"],
        NAME_EXPORT_FOLDER,
        str(firmware.id))
    source_folder = os.path.abspath(source_folder)
    if not os.path.exists(source_folder):
        os.makedirs(source_folder)
    return source_folder


def is_top_folder(library_path, folder_name):
    """
    Check if the library path is the top folder.

    :param library_path: str - path to the library.
    :param folder_name: str - name of the top folder.

    :return: bool - True if the library path is the top folder, False otherwise.

    """
    path_list = library_path.split(os.sep)
    return path_list[0] == folder_name


def get_subfolders(library_path, top_folder_name):
    """
    Get the subfolders after a specific top folder.

    :param library_path: str - path to the library.
    :param top_folder_name: str - name of the top folder.

    :return: list(str) - list of subfolders after the folder in case there are any subfolders.

    """
    subfolders = []
    if top_folder_name in library_path and not is_top_folder(library_path, top_folder_name):
        path_list = library_path.split(os.sep)
        top_folder_index = path_list.index(top_folder_name.replace("/", ""))
        subfolders = path_list[top_folder_index + 1:]
        subfolders = subfolders[:-1]
    return subfolders


def replace_first_from_right(original, target, replacement):
    """
    Replace the first occurrence of the target string from the right in the original string with the replacement string.

    :param original: str - the original string
    :param target: str - the target string to replace from the right
    :param replacement: str - the replacement string to replace with in the original string

    :return: str - result
    """
    original_reversed = original[::-1]
    target_reversed = target[::-1]
    replacement_reversed = replacement[::-1]
    result_reversed = original_reversed.replace(target_reversed, replacement_reversed, 1)
    result = result_reversed[::-1]

    return result

