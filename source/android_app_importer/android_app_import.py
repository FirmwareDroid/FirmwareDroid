# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
from pathlib import Path
from shutil import copyfile
from firmware_handler.firmware_file_search import get_firmware_file_list_by_md5
from hashing.standard_hash_generator import sha256_from_file, md5_from_file, sha1_from_file
from model import AndroidApp


def store_android_apps_from_firmware(search_path, firmware_app_store, firmware_file_list):
    """
    Finds and stores android .apk files.

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


def copy_apk_file(android_app, destination_folder, firmware_mount_path, apk_abs_path=None, has_relative_path=True):
    """
    Copies apps to the filesystem and saves the Android app in the database.

    :param has_relative_path: bool - If the app has a relative path.
    :param apk_abs_path: str - absolute path of the apk file.
    :param android_app: class:'AndroidApp'
    :param destination_folder: str - The root-folder the apps will be copied to.
    :param firmware_mount_path: str - the source path in which the firmware is mounted.

    """
    apk_abs_path = get_apk_abs_path(apk_abs_path, firmware_mount_path, android_app)
    app_root_folder = get_app_root_folder(destination_folder, android_app, has_relative_path)
    android_app_destination_filepath = os.path.join(app_root_folder, android_app.filename)
    existing_android_app = is_apk_in_database(android_app)
    if existing_android_app is None:
        copy_and_save_new_android_app(apk_abs_path, android_app_destination_filepath, android_app, has_relative_path)
    else:
        update_existing_android_app(android_app, existing_android_app)


def get_apk_abs_path(apk_abs_path, firmware_mount_path, android_app):
    """
    Returns the absolute path of the apk file.

    :param apk_abs_path: str - absolute path of the apk file.
    :param firmware_mount_path: str - the source path in which the firmware is mounted.
    :param android_app: class:'AndroidApp'

    :return: str - absolute path of the apk file.
    """
    if not apk_abs_path:
        apk_abs_path = os.path.join(firmware_mount_path,
                                    "." + android_app.relative_firmware_path,
                                    android_app.filename)
    return apk_abs_path


def get_app_root_folder(destination_folder, android_app, has_relative_path):
    """
    Returns the root folder of the app.

    :param destination_folder: str - The root-folder the apps will be copied to.
    :param android_app: Class:'AndroidApp' - The Android app instance.
    :param has_relative_path: bool - If the app has a relative path.

    :return: str - The root folder of the app.
    """
    if has_relative_path:
        app_root_folder = destination_folder + android_app.relative_firmware_path + "/"
    else:
        app_root_folder = destination_folder + "/"
    Path(app_root_folder).mkdir(parents=True, exist_ok=True)
    return app_root_folder


def copy_and_save_new_android_app(apk_abs_path, android_app_destination_filepath, android_app, has_relative_path):
    """
    Copies the apk file to the destination folder and saves the Android app in the database.

    :param apk_abs_path: str - absolute path of the apk file.
    :param android_app_destination_filepath: str - The destination path of the apk file.
    :param android_app: class:'AndroidApp' - The Android app instance.

    """
    copyfile(apk_abs_path, android_app_destination_filepath)
    if not os.path.isfile(android_app_destination_filepath):
        raise OSError(f"Could not copy Android app: from {apk_abs_path} "
                      f"to {android_app_destination_filepath}")
    if has_relative_path:
        android_app.relative_store_path = android_app_destination_filepath
    else:
        logging.info("Replacing active store path with relative path")
        new_relative_path = android_app_destination_filepath.replace("/var/www/", "../")
        new_relative_path = re.sub('/+', '/', new_relative_path)
        android_app.relative_store_path = new_relative_path

    android_app.absolute_store_path = os.path.abspath(android_app_destination_filepath)
    android_app.save()
    logging.info(f"Exported Android app: {android_app.filename}")


def update_existing_android_app(android_app, existing_android_app):
    """
    Updates the existing Android app with the new Android app.

    :param android_app: Class:'AndroidApp' - The new Android app instance.
    :param existing_android_app: Class:'AndroidApp' - The existing Android app instance.
    """
    android_app.relative_store_path = existing_android_app.relative_store_path
    android_app.absolute_store_path = existing_android_app.absolute_store_path
    android_app.app_twins_reference_list.append(existing_android_app.pk)
    android_app.save()
    existing_android_app.app_twins_reference_list.append(android_app.pk)
    existing_android_app.save()
    logging.info(f"Found twin app: {android_app.filename} / {existing_android_app.filename}")


def is_apk_in_database(android_app):
    """
    Checks if an apk is already stored in the database based on querying the md5 hash of the file.

    :return: true - Class:AndroidApp, false - None

    """
    existing_android_app_list = AndroidApp.objects(md5=android_app.md5).limit(1)
    if len(existing_android_app_list) > 0:
        existing_android_app = existing_android_app_list[0]
    else:
        existing_android_app = None
    return existing_android_app


def extract_android_app(firmware_mount_path, firmware_app_store, firmware_file_list):
    """
    Returns a list of class:'AndroidApp' files within the given path.

    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware file that contains the android apps and
    it's optimized files (.odex, .vdex, ...).
    :param firmware_app_store: str - path in which the .apk files will be stored.
    :param firmware_mount_path: str - The path to search for android apps.

    :return: List of object class:'AndroidApp'.

    """
    firmware_app_list = []
    for root, dirs, files in os.walk(firmware_mount_path):
        for filename in files:
            app_abs_path = os.path.join(root, filename)
            if filename.lower().endswith(".apk") and os.path.isfile(app_abs_path):
                firmware_app_list = process_apk_file(filename, root, firmware_mount_path, firmware_app_store,
                                                     firmware_app_list, firmware_file_list, app_abs_path)

    logging.info(f"Found .apk files in partition: {len(firmware_app_list)}")

    if len(firmware_app_list) < 1:
        logging.debug(f"Could not find any .apk files in {firmware_mount_path}!")
    return firmware_app_list


def process_apk_file(filename, root, firmware_mount_path, firmware_app_store, firmware_app_list, firmware_file_list,
                     app_abs_path):
    """
    Processes a single .apk file, and it's optimized files.

    :param filename: str - name of the apk file.
    :param root: str - root path of the apk file.
    :param firmware_mount_path: str - The source path in which the firmware is mounted.
    :param firmware_app_store:  str - path in which the .apk files will be stored.
    :param firmware_app_list: list(class:'AndroidApp') - list of android apps to store.
    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware file that contains the android apps and
    :param app_abs_path: str - absolute path of the apk file.

    :return: list(class:'AndroidApp') - list of android apps to store.

    """
    relative_firmware_path = root.replace(firmware_mount_path, "")
    try:
        android_app = create_android_app(filename, relative_firmware_path, firmware_mount_path)
        copy_apk_file(android_app, firmware_app_store, firmware_mount_path)
    except Exception:
        delete_android_apps(firmware_app_list)
        raise
    firmware_app_list.append(android_app)
    app_base_path = Path(app_abs_path).parent.absolute()
    optimized_firmware_file_list = find_optimized_android_apps(app_base_path, filename, firmware_file_list)
    add_optimized_firmware_files(android_app, optimized_firmware_file_list, firmware_app_store, firmware_mount_path)
    return firmware_app_list


def delete_android_apps(firmware_app_list):
    """
    Deletes all android apps in the list.

    :param firmware_app_list: list(class:'AndroidApp') - list of android apps to delete.

    """
    for android_app in firmware_app_list:
        android_app.delete()


def add_optimized_firmware_files(android_app, optimized_firmware_file_list, firmware_app_store, firmware_mount_path):
    """
    Extracts android code optimized files (.odex, .vdex, ...) to the file system and saves the firmware file references.

    :param firmware_mount_path: str - The source path in which the firmware is mounted.
    :param android_app: class:'AndroidApp' -  app to save the reference in.
    :param optimized_firmware_file_list: list(class:'FirmwareFile') - list of opt firmware files to reference and copy.
    :param firmware_app_store: str - path to the app store root folder.

    """
    firmware_file_id_list = []
    for optimized_firmware_file in optimized_firmware_file_list:
        opt_relative_root_path = os.path.dirname(optimized_firmware_file.relative_path) \
            .replace(android_app.relative_firmware_path, "")
        opt_folder_path = firmware_app_store + android_app.relative_firmware_path + opt_relative_root_path + "/"
        Path(opt_folder_path).mkdir(parents=True, exist_ok=True)
        opt_store_path = os.path.join(opt_folder_path, optimized_firmware_file.name)

        opt_source_file_path = os.path.join(firmware_mount_path,
                                            "." + android_app.relative_firmware_path,
                                            "." + opt_relative_root_path,
                                            optimized_firmware_file.name)
        if os.path.exists(opt_source_file_path):
            copyfile(opt_source_file_path, opt_store_path)
            optimized_firmware_file.is_on_disk = True
            optimized_firmware_file.save()
            logging.info(f"Exported file: {optimized_firmware_file.name}")
            firmware_file_id_list.append(optimized_firmware_file.id)
        else:
            logging.warning(f"Could not export file, probably not readable: {opt_source_file_path}")
    android_app.opt_firmware_file_reference_list = firmware_file_id_list
    android_app.save()


def create_android_app(filename,
                       relative_firmware_path,
                       firmware_mount_path,
                       original_filename=None,
                       apk_abs_path=None):
    """
    Creates a class:'AndroidApp' with minimal attributes. Does not save the app in the database.

    :param apk_abs_path: str - absolute path of the apk file.
    :param original_filename: str - original filename of the apk file before renaming.
    :param filename: str - name of the apk file.
    :param relative_firmware_path: str - relative path of the apk file within the firmware partition.
    :param firmware_mount_path: The source path in which the firmware is mounted.

    :return: class:'AndroidApp'

    """
    if not apk_abs_path:
        apk_abs_path = os.path.join(firmware_mount_path, "." + relative_firmware_path, filename)

    is_file = os.path.isfile(apk_abs_path)
    has_access = os.access(apk_abs_path, os.R_OK)
    if is_file and has_access:
        sha256 = sha256_from_file(apk_abs_path)
        md5 = md5_from_file(apk_abs_path)
        sha1 = sha1_from_file(apk_abs_path)
        file_size_bytes = os.path.getsize(apk_abs_path)
    else:
        raise ValueError(f"Could not create Android app: {filename} from {apk_abs_path}. "
                         f"is_file: {is_file}, "
                         f"has_access: {has_access}")

    return AndroidApp(filename=filename,
                      original_filename=original_filename,
                      relative_firmware_path=relative_firmware_path,
                      sha256=sha256,
                      md5=md5,
                      sha1=sha1,
                      file_size_bytes=file_size_bytes)


def find_optimized_android_apps(search_path, search_filename, firmware_file_list):
    """
    Searches for optimized android files (.odex, .art, .vdex,...) in the directory including sub-directories.
    Uses the filename for search matching and matches only exact filename matches.

    :param search_path: str - root dir to search through.
    :param search_filename: str - file to search for.
    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware file that contains the android app.
    :return: list(class:'FirmwareFile') - list of firmware files that contain optimized code for an android app.

    """
    file_format_list = [".odex", ".art", ".vdex", ".apk.prof"]
    optimized_firmware_file_list = []
    for file_format in file_format_list:
        filename = search_filename.replace(".apk", file_format)
        file_path_list = find_file_in_directory(search_path, filename)
        for file_path in file_path_list:
            md5_hash = md5_from_file(file_path)
            optimized_firmware_file_list.extend(get_firmware_file_list_by_md5(firmware_file_list, md5_hash))
    return optimized_firmware_file_list


def find_file_in_directory(search_path, filename):
    """
    Finds all files of a given filetype in the search path and it's sub folders.

    :param search_path: str - root dir to search through.
    :param filename: str - file to search for.
    :return: list(str) - absolute file path of the found files.

    """
    result_file_path_list = []
    for root, dirs, file_list in os.walk(search_path):
        for current_filename in file_list:
            file_abs_path = os.path.join(root, current_filename)
            if current_filename == filename and os.path.isfile(file_abs_path):
                result_file_path_list.append(file_abs_path)

    return result_file_path_list
