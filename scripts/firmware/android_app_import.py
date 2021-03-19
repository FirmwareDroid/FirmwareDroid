import logging
import os
from pathlib import Path
from shutil import copyfile
from scripts.firmware.firmware_file_search import get_firmware_file_by_md5
from scripts.hashing.file_hashs import sha256_from_file, md5_from_file, sha1_from_file
from model import AndroidApp


def store_android_apps(search_path, firmware_app_store, firmware_file_list):
    """
    Finds and stores all android .apk files.
    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware file that contains the android app.
    :param search_path: str - path to search for .apk files.
    :param firmware_app_store: str - path in which the .apk files will be stored.
    :return: list of class:'AndroidApp'
    """
    firmware_app_list = extract_android_app(search_path, firmware_app_store, firmware_file_list)
    for android_app in firmware_app_list:
        add_firmware_file_reference(android_app, firmware_file_list)
    return firmware_app_list


def add_firmware_file_reference(android_app, firmware_file_list):
    """
    Adds references between Android app and firmware files.
    :param android_app: class:'AndroidApp' - app to save reference to.
    :param firmware_file_list: list - class:'FirmwareFile'
    """
    firmware_file = list(filter(lambda x: x.md5 == android_app.md5, firmware_file_list))[0]
    android_app.firmware_file_reference = firmware_file.id
    android_app.save()
    firmware_file.android_app_reference = android_app.id
    firmware_file.save()


def copy_apk_file(android_app, destination_folder, firmware_mount_path):
    """
    Copies apps to the filesystem and saves the Android app in the database.
    :param android_app: class:'AndroidApp'
    :param destination_folder: The root-folder the apps will be copied to.
    :param firmware_mount_path: The source path in which the firmware is mounted.
    """
    apk_source_path = os.path.join(firmware_mount_path,
                                   "." + android_app.relative_firmware_path,
                                   android_app.filename)
    app_root_folder = destination_folder + android_app.relative_firmware_path + "/"
    Path(app_root_folder).mkdir(parents=True, exist_ok=True)
    android_app_destination_filepath = os.path.join(app_root_folder, android_app.filename)
    copyfile(apk_source_path, android_app_destination_filepath)
    if not os.path.isfile(android_app_destination_filepath):
        raise OSError(f"Could not copy Android app: from {apk_source_path} "
                      f"to {android_app_destination_filepath}. Is path available?")
    android_app.relative_store_path = android_app_destination_filepath
    android_app.absolute_store_path = os.path.abspath(android_app_destination_filepath)
    android_app.save()


def extract_android_app(firmware_mount_path, firmware_app_store, firmware_file_list):
    """
    Returns a list of class: files within the given path.
    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware file that contains the android apps and
    it's optimized files (.odex, .vdex, ...).
    :param firmware_app_store: str - path in which the .apk files will be stored.
    :param firmware_mount_path: str - The path to search for android apps.
    :return: List of object class:'AndroidApp'.
    """
    firmware_apps = []
    for root, dirs, files in os.walk(firmware_mount_path):
        for filename in files:
            app_abs_path = os.path.join(root, filename)
            if filename.lower().endswith(".apk") and os.path.isfile(app_abs_path):
                relative_firmware_path = root.replace(firmware_mount_path, "")
                android_app = create_android_app(filename, relative_firmware_path, firmware_mount_path)
                copy_apk_file(android_app, firmware_app_store, firmware_mount_path)
                optimized_firmware_files = find_optimized_android_apps(android_app.absolute_store_path,
                                                                       filename,
                                                                       firmware_file_list)
                android_app.app_optimization_file_reference_list = list(map(lambda x: x.id, optimized_firmware_files))
                android_app.save()
                firmware_apps.append(android_app)
    logging.info(f"Found .apk files in partition: {len(firmware_apps)}")
    if len(firmware_apps) < 1:
        raise ValueError(f"Could not find any .apk files in {firmware_mount_path}!")
    return firmware_apps


def create_android_app(filename, relative_firmware_path, firmware_mount_path):
    """
    Creates a class:'AndroidApp' with minimal attributes. Does not save the app in the database.
    :param filename: str - name of the apk file.
    :param relative_firmware_path: str - relative path of the apk file within the firmware partition.
    :param firmware_mount_path: The source path in which the firmware is mounted.
    :return: class:'AndroidApp'
    """
    apk_abs_path = os.path.join(firmware_mount_path,
                                "." + relative_firmware_path,
                                filename)
    if os.path.isfile(apk_abs_path) and os.access(apk_abs_path, os.R_OK):
        sha256 = sha256_from_file(apk_abs_path)
        md5 = md5_from_file(apk_abs_path)
        sha1 = sha1_from_file(apk_abs_path)
        file_size_bytes = os.path.getsize(apk_abs_path)
    else:
        raise ValueError(f"Could not extract Android app: {filename} from {relative_firmware_path}.")

    return AndroidApp(filename=filename,
                      relative_firmware_path=relative_firmware_path,
                      sha256=sha256,
                      md5=md5,
                      sha1=sha1,
                      file_size_bytes=file_size_bytes)


def find_optimized_android_apps(search_path, filename, firmware_file_list):
    """
    Searches for optimized android files (.odex, .art, .vdex,...) in the directory including sub-directories.
    Uses the filename for search matching and matches only exact filename matches.
    :param search_path: str - root dir to search through.
    :param filename: str - file to search for.
    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware file that contains the android app.
    :return: list(class:'FirmwareFile') - list of firmware files that contain optimized code for an android app.
    """
    file_format_list = [".odex", ".art", ".vdex", ".apk.prof"]
    optimized_firmware_files = []
    for file_format in file_format_list:
        filename = filename.replace(".apk", file_format)
        file_path_list = find_file_in_directory(search_path, filename)
        for file_path in file_path_list:
            md5_hash = md5_from_file(file_path)
            firmware_file = get_firmware_file_by_md5(firmware_file_list, md5_hash)
            optimized_firmware_files.append(firmware_file)
    return optimized_firmware_files


def find_file_in_directory(search_path, filename):
    """
    Finds all files of a given filetype in the search path and it's sub folders.
    :param search_path: str - root dir to search through.
    :param filename: str - file to search for.
    :return: list(str) - absolute file path of the found files.
    """
    result_file_path_list = []
    for root, dirs, file_list in os.walk(search_path):
        for currrent_filename in file_list:
            file_abs_path = os.path.join(root, currrent_filename)
            if currrent_filename == filename and os.path.isfile(file_abs_path):
                result_file_path_list.append(file_abs_path)
    return result_file_path_list
