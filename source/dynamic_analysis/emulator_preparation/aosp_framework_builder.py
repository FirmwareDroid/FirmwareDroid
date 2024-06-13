import logging
import os
import re
from dynamic_analysis.emulator_preparation.aosp_file_finder import export_files
from string import Template
from dynamic_analysis.emulator_preparation.asop_meta_writer import create_modules
from dynamic_analysis.emulator_preparation.templates.java_module_template import ANDROID_MK_JAVA_MODULE_TEMPLATE


def create_template_string(format_name, library_path):
    """
    Creates the template string for the shared library module.

    :param format_name: str - format name of the shared library module.
    :param library_path: str - path to the shared library module.

    :return: str - template string for the shared library module.

    """

    if format_name.lower() == "mk":
        file_template = ANDROID_MK_JAVA_MODULE_TEMPLATE
    else:
        raise NotImplementedError(f"Format name {format_name} is not supported yet.")

    file_name = os.path.basename(library_path)
    local_module = file_name.replace(".jar", "")
    local_src_files = file_name
    local_module_path = "$(TARGET_OUT)/system/framework/"
    template_out = Template(file_template).substitute(local_module=local_module,
                                                      local_module_path=local_module_path,
                                                      local_src_files=local_src_files,
                                                      )
    return template_out


def process_framework_files(firmware, destination_folder, store_setting_id, format_name):
    """
    This function is used to process the shared libraries of a firmware. It extracts the shared libraries from the
    firmware and creates the shared library modules for AOSP firmware.

    :param firmware: class:'Firmware'
    :param destination_folder: str - path to the destination folder.
    :param store_setting_id: int - id of the store setting.
    :param format_name: str - format name of the shared library module.

    """
    filename_regex = "framework[.]jar$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    source_folder = export_files(firmware, destination_folder, store_setting_id, format_name, search_pattern)
    logging.debug(f"Processing framework in {source_folder}")
    create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string)

