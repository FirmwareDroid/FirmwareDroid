import os
import re
from string import Template
from dynamic_analysis.emulator_preparation.aosp_file_exporter import get_subfolders, replace_first_from_right, \
    get_firmware_export_folder_root
from dynamic_analysis.emulator_preparation.asop_meta_writer import create_modules
from dynamic_analysis.emulator_preparation.templates.executables_module_template import \
    ANDROID_MK_EXECUTABLE_MODULE_TEMPLATE


def get_local_module_path(file_path, partition_name, filename):
    """
    Get the local module path for the given partition_name.

    :param file_path: str - path to the module file.
    :param partition_name: str - name of the partition on Android.
    :param filename: str - name of the file to remove from the path.

    :return: str - local module path for the shared library module.

    """
    subfolder_list = get_subfolders(file_path, partition_name)
    if len(subfolder_list) == 0:
        local_module_path = "$(TARGET_OUT)/"
    else:
        local_module_path = f"$(TARGET_OUT)/{os.path.join(*subfolder_list)}"
        local_module_path = replace_first_from_right(local_module_path, filename, "")
    return local_module_path


def get_file_template(format_name):
    if format_name.lower() == "mk":
        file_template = ANDROID_MK_EXECUTABLE_MODULE_TEMPLATE
    else:
        raise NotImplementedError(f"Format name {format_name} is not supported yet.")
    return file_template


def create_template_string(format_name, file_path):
    file_template = get_file_template(format_name)
    in_file_name = os.path.basename(file_path)
    partition_name = file_path.split("/")[9]
    local_module = in_file_name + "_INJECTED_PREBUILT_EXECUTABLE_" + partition_name.upper()
    local_src_files = in_file_name
    local_module_path = get_local_module_path(file_path, partition_name, in_file_name)
    template_out = Template(file_template).substitute(local_src_files=local_src_files,
                                                      local_module=local_module,
                                                      local_module_path=local_module_path,
                                                      )
    return template_out, local_module


def process_executable_files(firmware, destination_folder, store_setting_id, format_name):
    filename_regex = "^[^./]+$|^(.*/)?[^./]+$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    source_folder = get_firmware_export_folder_root(store_setting_id, firmware)
    create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string)
