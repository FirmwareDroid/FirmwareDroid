import logging
import os
import re
from string import Template
from dynamic_analysis.emulator_preparation.aosp_file_exporter import (get_firmware_export_folder_root,
                                                                      get_subfolders)
from dynamic_analysis.emulator_preparation.aosp_meta_writer import create_modules
from dynamic_analysis.emulator_preparation.templates.shared_library_module_template import \
    ANDROID_MK_SHARED_LIBRARY_TEMPLATE, ANDROID_BP_SHARED_LIBRARY_TEMPLATE, AOSP_12_SHARED_LIBRARIES


def get_local_module_path(file_path, partition_name, format="mk"):
    """
    Get the local module path for the given partition_name.

    :param file_path: str - path to the shared library module.
    :param partition_name: str - name of the partition on Android.

    :return: str - local module path for the shared library module.

    """
    if format.lower() == "mk":
        target_out = "$(TARGET_OUT)"
    else:
        target_out = ""

    subfolder_list = get_subfolders(file_path, partition_name)
    if len(subfolder_list) <= 1:
        local_module_path = f"{target_out}/"
    else:
        local_module_path = f"{target_out}/{os.path.join(*subfolder_list)}"
    return local_module_path


def select_local_module_path(file_path, file_name, format):
    """
    Creates the local module path for the shared library module based on the input path

    :param format: str - format name of the shared library module.
    :param file_path: str - path to the shared library module.
    :param file_name: str - name of the file to remove from the path.

    :return: str - local module path for the shared library module.

    """
    if format.lower() == "mk":
        target_out = "$(TARGET_OUT)"
    else:
        target_out = ""

    if "/app/" in file_path:
        app_name = file_path.split("/app/")[1]
        local_module_path = f"{target_out}/app/{app_name}/lib/$(TARGET_ARCH_ABI)/"
    elif "/priv-app/" in file_path:
        app_name = file_path.split("/priv-app/")[1]
        local_module_path = f"{target_out}/priv-app/{app_name}/lib/$(TARGET_ARCH_ABI)/"
    elif "_apex/" in file_path:
        local_module_path = f"{target_out}/system/lib64/"
    else:
        partition_name = file_path.split("/")[9]
        local_module_path = get_local_module_path(file_path, partition_name, format)
    local_module_path = local_module_path.replace("//", "/").replace(file_name, "")

    return local_module_path


def get_overrides(file_name):
    for module_name in AOSP_12_SHARED_LIBRARIES:
        if module_name in file_name:
            return module_name
    return ""


def create_template_string(format_name, library_path):
    """
    Creates the template string for the shared library module.

    :param format_name: str - format name of the shared library module.
    :param library_path: str - path to the shared library module.

    :return: str - template string for the shared library module.
             str - the name of the local module.

    """
    file_template = ANDROID_MK_SHARED_LIBRARY_TEMPLATE if format_name.lower() == "mk" \
        else ANDROID_BP_SHARED_LIBRARY_TEMPLATE

    file_name = os.path.basename(library_path)
    local_src_files = file_name
    local_module = file_name.replace(".so", "")
    local_module_path = select_local_module_path(library_path, file_name, format_name)
    local_prebuilt_module_file = f"$(LOCAL_PATH)/{file_name}"
    local_overrides = get_overrides(file_name)
    template_out = Template(file_template).substitute(local_module=local_module,
                                                      local_module_path=local_module_path,
                                                      local_src_files=local_src_files,
                                                      local_prebuilt_module_file=local_prebuilt_module_file,
                                                      local_overrides=local_overrides
                                                      )
    return template_out, local_module


def process_shared_libraries(firmware, destination_folder, store_setting_id, format_name):
    """
    This function is used to process the shared libraries of a firmware. It extracts the shared libraries from the
    firmware and creates the shared library modules for AOSP firmware.

    :param firmware: class:'Firmware'
    :param destination_folder: str - path to the destination folder.
    :param store_setting_id: int - id of the store setting.
    :param format_name: str - format name of the shared library module.

    """
    filename_regex = r"\.so(\.\d+)?$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    source_folder = get_firmware_export_folder_root(store_setting_id, firmware)
    logging.debug(f"Processing shared libraries in {source_folder}")
    create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string)
