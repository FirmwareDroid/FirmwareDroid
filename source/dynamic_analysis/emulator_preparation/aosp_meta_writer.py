import logging
import os
import re
import shutil

META_BUILD_FILENAME_SYSTEM_EXT = "meta_build_system_ext.txt"
META_BUILD_FILENAME_SYSTEM = "meta_build_system.txt"
META_BUILD_FILENAME_VENDOR = "meta_build_vendor.txt"
META_BUILD_FILENAME_PRODUCT = "meta_build_product.txt"


def add_module_to_meta_file(partition_name, tmp_root_dir, module_naming):
    """
    Writes the module naming to a meta file for the given Android app.

    :param partition_name: str - The partition name of the app.
    :param tmp_root_dir: str - A temporary directory to store the build files.
    :param module_naming: str - A string to name the module in the build file.

    :return:
    """

    if "vendor" in partition_name.lower() or "oem" in partition_name.lower() or "odm" in partition_name.lower():
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_VENDOR)
    elif "product" in partition_name.lower():
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_PRODUCT)
    elif "system_ext" in partition_name.lower():
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_SYSTEM_EXT)
    else:
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_SYSTEM)

    with open(meta_file, 'a') as fp:
        fp.write("    " + module_naming + " \\\n")


def add_to_log_file(tmp_root_dir, log_entry, log_name):
    """
    Adds a log entry to the log file.

    :param log_name: str - The name of the log file.
    :param tmp_root_dir: str - A temporary directory to store the log file.
    :param log_entry: str - A log entry to be added to the log file.

    """
    log_file = os.path.join(tmp_root_dir, log_name)
    with open(log_file, 'a') as fp:
        fp.write(log_entry + "\n")


def copy_replacer_script(destination_folder):
    """
    Copy the replacer script to the destination folder.

    :param destination_folder: str - path to the destination folder.

    """
    replacer_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates/replacer.sh")
    destination_path = os.path.join(destination_folder, "replacer.sh")
    shutil.copy(replacer_script_path, destination_path)


def create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string):
    """
    This function is used to create a module for AOSP firmware. It searches for the files in the source folder based on
    the search pattern and creates a module for each file found in the destination folder. The module is created using
    the template string created by the create_template_string function. The module is then added to the meta file.


    :param search_pattern: regex - search pattern for the file.
    :param source_folder: str - path to the source folder.
    :param destination_folder: str - path to the destination folder.
    :param format_name: str - format name of module (e.g., MK or BP).
    :param create_template_string: function - function to create the template string for the module.

    :return: str - path to the module.

    """
    if source_folder and destination_folder:
        source_folder = os.path.abspath(source_folder)
        destination_folder = os.path.abspath(destination_folder)
    else:
        raise Exception(f"Source folder is not provided.")

    logging.info(f"Creating AOSP modules from {source_folder} to {destination_folder}")
    for root, dirs, files in os.walk(str(source_folder)):
        for file in files:
            if re.search(search_pattern, file):
                source_file = os.path.join(root, file)
                logging.info(f"Creating module for: {source_file} to {destination_folder}")
                if not os.path.exists(source_file):
                    raise Exception(f"The source file does not exist: {source_file}")
                template_out, module_name = create_template_string(format_name, source_file)
                module_folder = os.path.join(destination_folder, module_name)
                copy_file(source_file, module_folder)
                write_template_to_file(template_out, module_folder, format_name)
                partition_name = source_file.split("/")[7]
                add_module_to_meta_file(partition_name, destination_folder, module_name)
                log_entry = (f"Module: {module_name}"
                             f"| File: {source_file}")
                add_to_log_file(destination_folder, log_entry, "meta_module_builder.log")


def write_template_to_file(template_out, destination_folder, format_name):
    """
    Writes the template string to a file.

    :param format_name: str - format name of the module either mk or bp.
    :param template_out: str - template string for the module.
    :param destination_folder: str - path to the destination folder.

    :return: str - path to the module.

    """
    if format_name.lower() == "bp":
        file_path = os.path.join(destination_folder, "Android.bp")
    else:
        file_path = os.path.join(destination_folder, "Android.mk")
    with open(file_path, "w") as file:
        file.write(template_out)
    return file_path


def copy_file(source_folder, destination_folder):
    """
    Moves the file from the source folder to the destination folder.

    :param source_folder: str - path to the source folder.
    :param destination_folder: str - path to the destination folder.

    :return: str - path to the zip file.

    """
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    if not os.path.exists(source_folder):
        raise Exception(f"The source folder does not exist: {source_folder}")
    logging.info(f"Copying file from {source_folder} to {destination_folder}")
    shutil.copy(source_folder, destination_folder)
