import logging
import os
import re
from string import Template
from dynamic_analysis.emulator_preparation.aosp_file_exporter import get_firmware_export_folder_root
from dynamic_analysis.emulator_preparation.aosp_meta_writer import create_modules
from dynamic_analysis.emulator_preparation.templates.apex_prebuilt_template import APEX_PREBUILT_TEMPLATE, \
    APEX_EMULATOR_LIST, APEX_MANIFEST_TEMPLATE
from extractor.unblob_extractor import unblob_extract


def create_template_string(format_name, file_path):
    apex_filename = str(os.path.basename(file_path))
    apex_name = apex_filename.replace(".apex", "").replace(".capex", "")
    return "", apex_name


def map_apex_files_to_lists(apex_files):
    """
    Maps the apex files to the different lists based on the file type.

    :param apex_files:

    :return:
    """
    all_lists = {"native_shared_libs": [], "binaries": [], "java_libs": [], "prebuilts": []}
    for apex_file in apex_files:
        if apex_file.endswith(".so"):
            all_lists["native_shared_libs"].append(f"native_shared_libs: [\"{apex_file}\"]")
        elif apex_file.endswith(".apk"):
            all_lists["binaries"].append(f"binaries: [\"{apex_file}\"]")
        elif apex_file.endswith(".jar"):
            all_lists["java_libs"].append(f"java_libs: [\"{apex_file}\"]")
        else:
            all_lists["prebuilts"].append(f"prebuilts: [\"{apex_file}\"]")
    return all_lists

def create_apex_manifest_file(apex_name, apex_version):
    file_template = APEX_MANIFEST_TEMPLATE
    template_out = Template(file_template).substitute(apex_name=apex_name,
                                                      apex_version=apex_version
                                                      )
    return template_out


def get_apex_files(apex_file_path, destination_folder, ):
    """
    Extracts the apex files from the source folder to the destination folder and then creates a list of all files in the
    destination folder.

    """
    extract_apex_file(apex_file_path, destination_folder)
    apex_files = []
    for root, dirs, files in os.walk(destination_folder):
        for file in files:
            apex_files.append(os.path.join(root, file))
    return apex_files


def extract_apex_file(file_path, destination_dir):
    """
    Extracts the apex file to the destination directory.

    :param file_path: str - path to the apex file.
    :param destination_dir: str - path to the destination directory.
    :raises RuntimeError: In case the extraction fails.

    """
    is_success = unblob_extract(file_path, destination_dir, depth=10, worker_count=2)
    if not is_success:
        logging.error(f"Failed to extract {file_path}")
        raise RuntimeError(f"Failed to extract {file_path}")
    else:
        logging.info(f"Successfully extracted APEX {file_path}")


def create_prebuilt_apex_OLD(format_name, file_path):
    file_template = APEX_PREBUILT_TEMPLATE
    apex_filename = str(os.path.basename(file_path))
    apex_name = apex_filename.replace(".apex", "").replace(".capex", "")
    apex_relative_path_x86_x64 = f"{apex_filename}"
    apex_relative_path_arm64 = f"{apex_filename}"
    template_out = Template(file_template).substitute(apex_name=apex_name,
                                                      apex_filename=apex_filename,
                                                      apex_relative_path_arm64=apex_relative_path_arm64,
                                                      apex_relative_path_x86_x64=apex_relative_path_x86_x64
                                                      )
    return template_out, apex_name



def process_apex_files(firmware, destination_folder, store_setting_id, format_name):
    format_name = "BP"
    filename_regex = r"\.(c?apex)$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    source_folder = get_firmware_export_folder_root(store_setting_id, firmware)
    logging.debug(f"Processing shared libraries in {source_folder}")
    create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string)