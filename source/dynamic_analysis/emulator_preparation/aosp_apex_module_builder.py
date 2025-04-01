import logging
import os
import re
from dynamic_analysis.emulator_preparation.aosp_file_exporter import get_firmware_export_folder_root
from dynamic_analysis.emulator_preparation.aosp_meta_writer import create_modules


def create_template_string(format_name, file_path):
    apex_filename = str(os.path.basename(file_path))
    apex_name = apex_filename.replace(".apex", "").replace(".capex", "")
    return "", apex_name


def process_apex_files(firmware, destination_folder, store_setting_id, format_name):
    format_name = "BP"
    filename_regex = r"\.(c?apex)$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    source_folder = get_firmware_export_folder_root(store_setting_id, firmware)
    logging.debug(f"Processing shared libraries in {source_folder}")
    create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string)