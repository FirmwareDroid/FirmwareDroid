import logging
import os
import re
from string import Template
from dynamic_analysis.emulator_preparation.aosp_file_finder import export_files, get_file_export_folder
from dynamic_analysis.emulator_preparation.asop_meta_writer import create_modules
from dynamic_analysis.emulator_preparation.templates.shared_library_module_template import \
    ANDROID_MK_SHARED_LIBRARY_TEMPLATE, ANDROID_BP_SHARED_LIBRARY_TEMPLATE


def is_top_folder(library_path, folder_name):
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
    return subfolders


def get_lib_local_module_path(library_path, folder_name):
    """
    Get the local module path for the shared library module.

    :param library_path: str - path to the shared library module.
    :param folder_name: str - name of the lib folder on Android.

    :return: str - local module path for the shared library module.
    """
    subfolder_list = []
    if is_top_folder(library_path, folder_name):
        local_module_path = f"$(TARGET_OUT)/{folder_name}/"
    else:
        subfolder_list = get_subfolders(library_path, folder_name)
        if len(subfolder_list) == 0:
            local_module_path = f"$(TARGET_OUT)/{folder_name}/"
        else:
            local_module_path = f"$(TARGET_OUT)/{folder_name}/{os.path.join(*subfolder_list)}/"
    return local_module_path, subfolder_list


def create_template_string(format_name, library_path):
    """
    Creates the template string for the shared library module.

    :param format_name: str - format name of the shared library module.
    :param library_path: str - path to the shared library module.

    :return: str - template string for the shared library module.

    """
    file_template = ANDROID_MK_SHARED_LIBRARY_TEMPLATE if format_name.lower() == "mk" \
        else ANDROID_BP_SHARED_LIBRARY_TEMPLATE

    if format_name.lower() != "mk":
        raise NotImplementedError(f"Format name {format_name} is not supported yet.")

    library_name = os.path.basename(library_path)
    local_src_files = library_name
    local_module = library_name.replace(".so", "")

    if "/app/" in library_path:
        app_name = library_path.split("/app/")[1]
        local_module_path = f"$(TARGET_OUT)/app/{app_name}/lib/$(TARGET_ARCH_ABI)/"
    elif "/priv-app/" in library_path:
        app_name = library_path.split("/priv-app/")[1]
        local_module_path = f"$(TARGET_OUT)/priv-app/{app_name}/lib/$(TARGET_ARCH_ABI)/"
    elif "/lib64/" in library_path:
        local_module_path, subfolder_list = get_lib_local_module_path(library_path, "/lib64/")
        if len(subfolder_list) > 0:
            local_module = f"{os.path.join(*subfolder_list)}_{local_module}".replace("/", "_")
    elif "/lib/" in library_path:
        local_module_path, subfolder_list = get_lib_local_module_path(library_path, "/lib/")
        # Android emulator uses lib64 for 64-bit libraries and does not have a lib folder for 32-bit libraries.
        local_module_path = local_module_path.replace("lib", "lib64")
        if len(subfolder_list) > 0:
            local_module = f"{os.path.join(*subfolder_list)}_{local_module}".replace("/", "_")
    else:
        local_module_path = "$(TARGET_OUT)/lib64/"

    local_prebuilt_module_file = f"$(LOCAL_PATH)/{library_name}"
    template_out = Template(file_template).substitute(local_module=local_module,
                                                      local_module_path=local_module_path,
                                                      local_src_files=local_src_files,
                                                      local_prebuilt_module_file=local_prebuilt_module_file
                                                      )
    return template_out


def process_shared_libraries(firmware, destination_folder, store_setting_id, format_name, skip_file_export):
    """
    This function is used to process the shared libraries of a firmware. It extracts the shared libraries from the
    firmware and creates the shared library modules for AOSP firmware.

    :param skip_file_export: bool - flag to skip the file export.
    :param firmware: class:'Firmware'
    :param destination_folder: str - path to the destination folder.
    :param store_setting_id: int - id of the store setting.
    :param format_name: str - format name of the shared library module.

    """
    filename_regex = ".so$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    if not skip_file_export:
        export_files(firmware, store_setting_id, search_pattern)
    source_folder = get_file_export_folder(store_setting_id, firmware)
    logging.debug(f"Processing shared libraries in {source_folder}")
    create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string)
