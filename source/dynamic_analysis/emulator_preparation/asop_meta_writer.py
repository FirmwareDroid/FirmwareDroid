import logging
import os
import shutil

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

    if partition_name.lower() == "vendor" or partition_name.lower() == "oem" or partition_name.lower() == "odm":
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_VENDOR)
    elif partition_name.lower() == "product":
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_PRODUCT)
    else:
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_SYSTEM)

    with open(meta_file, 'a') as fp:
        fp.write("    " + module_naming + " \\\n")


def create_modules(source_folder, destination_folder, format_name, search_pattern, create_template_string):
    """
    This function is used to create the shared library module for AOSP firmware.

    :param search_pattern: regex - search pattern for the shared library.
    :param source_folder: str - path to the source folder.
    :param destination_folder: str - path to the destination folder.
    :param format_name: str - format name of the shared library module.
    :param create_template_string: function - function to create the template string for the shared library module.

    :return: str - path to the shared library module.

    """
    for root, dirs, files in os.walk(str(source_folder)):
        for file in files:
            if search_pattern.match(file):
                source_file = os.path.join(root, file)
                logging.info(f"Processing shared library: {source_file}")
                if not os.path.exists(source_file):
                    raise Exception(f"The source file does not exist: {source_file}")
                template_out = create_template_string(format_name, source_file)
                module_name = os.path.splitext(source_file)[0]
                module_folder = os.path.join(destination_folder, module_name)
                copy_file(source_file, module_folder)
                write_template_to_file(template_out, module_folder)
                partition_name = source_file.split("/")[7]
                add_module_to_meta_file(partition_name, destination_folder, module_name)


def write_template_to_file(template_out, destination_folder):
    """
    Writes the template string to a file.

    :param template_out: str - template string for the shared library module.
    :param destination_folder: str - path to the destination folder.

    :return: str - path to the shared library module.

    """
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