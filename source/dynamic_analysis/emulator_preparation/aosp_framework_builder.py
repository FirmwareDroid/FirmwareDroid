import os
import re
from dynamic_analysis.emulator_preparation.aosp_file_exporter import (export_files,
                                                                      get_firmware_export_folder_root,
                                                                      get_subfolders)
from string import Template
from dynamic_analysis.emulator_preparation.asop_meta_writer import create_modules
from dynamic_analysis.emulator_preparation.templates.java_module_template import ANDROID_MK_JAVA_MODULE_TEMPLATE


def get_local_module_path(file_path, partition_name, file_name):
    """
    Get the local module path for the given partition_name.

    :param file_name: str - name of the file to remove from the path.
    :param file_path: str - path to the shared library module.
    :param partition_name: str - name of the partition on Android.

    :return: str - local module path for the shared library module.

    """
    subfolder_list = get_subfolders(file_path, partition_name)
    if len(subfolder_list) == 0:
        local_module_path = f"$(TARGET_OUT)/"
    else:
        if partition_name == "system" and "system/framework" in file_path:
            # Redirect jar files to the emulator framework folder instead of the system/framework folder
            local_module_path = f"$(TARGET_OUT)/framework"
        elif partition_name == "system" and "system_ext/framework" in file_path:
            # Redirect jar files to the system_ext framework folder instead of the system/system_ext/framework folder
            local_module_path = f"$(TARGET_OUT)/system_ext/framework"
        else:
            local_module_path = f"$(TARGET_OUT)/{os.path.join(*subfolder_list)}"

    local_module_path = local_module_path.replace(file_name, "")
    return local_module_path


def create_template_string(format_name, file_path):
    """
    Creates the template string for the shared library module.

    :param format_name: str - format name of the shared library module.
    :param file_path: str - path to the shared library module.

    :return: str - template string for the shared library module.

    """
    if format_name.lower() == "mk":
        file_template = ANDROID_MK_JAVA_MODULE_TEMPLATE
    else:
        raise NotImplementedError(f"Format name {format_name} is not supported yet.")

    in_file_name = os.path.basename(file_path)
    local_module = in_file_name.replace(".jar", "") + "_INJECTED_PREBUILT_JAR"
    out_file_name = local_module + ".jar"
    local_src_files = in_file_name
    partition_name = file_path.split("/")[9]
    local_module_path = get_local_module_path(file_path, partition_name, in_file_name)
    template_out = Template(file_template).substitute(local_src_files=local_src_files,
                                                      local_module=local_module,
                                                      local_module_path=local_module_path,
                                                      local_scr_file_out=out_file_name,
                                                      )
    return template_out


def process_framework_files(firmware, destination_folder, store_setting_id, format_name, skip_file_export):
    """
    This function is used to process the shared libraries of a firmware. It extracts the shared libraries from the
    firmware and creates the shared library modules for AOSP firmware.

    :param firmware: class:'Firmware'
    :param destination_folder: str - path to the destination folder.
    :param store_setting_id: int - id of the store setting.
    :param format_name: str - format name of the shared library module.
    :param skip_file_export: bool - flag to skip the file export.

    """
    filename_regex = ".jar$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    if not skip_file_export:
        export_files(firmware, store_setting_id, search_pattern)
    source_folder = get_firmware_export_folder_root(store_setting_id, firmware)
    create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string)

