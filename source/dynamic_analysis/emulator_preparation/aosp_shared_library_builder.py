import logging
import os
import re
from string import Template
from dynamic_analysis.emulator_preparation.aosp_file_exporter import (export_files, get_firmware_export_folder_root,
                                                                      is_top_folder, \
    get_subfolders)
from dynamic_analysis.emulator_preparation.asop_meta_writer import create_modules
from dynamic_analysis.emulator_preparation.templates.shared_library_module_template import \
    ANDROID_MK_SHARED_LIBRARY_TEMPLATE, ANDROID_BP_SHARED_LIBRARY_TEMPLATE


def get_lib_local_module_path(library_path, folder_name):
    """
    Get the local module path for the given folder_name.

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
            local_module_path = f"$(TARGET_OUT)/{folder_name}/{os.path.join(*subfolder_list)}"
    return local_module_path, subfolder_list


def get_local_module_path(file_path, partition_name):
    """
    Get the local module path for the given partition_name.

    :param file_path: str - path to the shared library module.
    :param partition_name: str - name of the partition on Android.

    :return: str - local module path for the shared library module.

    """
    subfolder_list = get_subfolders(file_path, partition_name)
    if len(subfolder_list) == 0:
        local_module_path = f"$(TARGET_OUT)/"
    else:
        local_module_path = f"$(TARGET_OUT)/{os.path.join(*subfolder_list)}"
    return local_module_path


def select_local_module_path(file_path, file_name):
    """
    Creates the local module path for the shared library module based on the input path

    :param file_path: str - path to the shared library module.
    :param file_name: str - name of the file to remove from the path.

    :return: str - local module path for the shared library module.

    """
    if "/app/" in file_path:
        app_name = file_path.split("/app/")[1]
        local_module_path = f"$(TARGET_OUT)/app/{app_name}/lib/$(TARGET_ARCH_ABI)/"
    elif "/priv-app/" in file_path:
        app_name = file_path.split("/priv-app/")[1]
        local_module_path = f"$(TARGET_OUT)/priv-app/{app_name}/lib/$(TARGET_ARCH_ABI)/"
    else:
        partition_name = file_path.split("/")[9]
        local_module_path = get_local_module_path(file_path, partition_name)
    local_module_path = local_module_path.replace("//", "/").replace(file_name, "")
    return local_module_path


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

    file_name = os.path.basename(library_path)
    local_src_files = file_name
    local_module = file_name.replace(".so", "")
    local_module_path = select_local_module_path(library_path, file_name)
    local_prebuilt_module_file = f"$(LOCAL_PATH)/{file_name}"
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
    filename_regex = r"\.so(\.\d+)?$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    if not skip_file_export:
        export_files(firmware, store_setting_id, search_pattern)
    source_folder = get_firmware_export_folder_root(store_setting_id, firmware)
    logging.debug(f"Processing shared libraries in {source_folder}")
    create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string)
