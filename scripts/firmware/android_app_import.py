import logging
import os
from pathlib import Path
from shutil import copyfile
from scripts.hashing.file_hashs import sha256_from_file, md5_from_file, sha1_from_file
from model import AndroidApp


def extract_android_apps(firmware_app_list, destination_folder, firmware_mount_path):
    """
    Copies apps to the filesystem and saves meta-information in the database.
    :param firmware_app_list: list of class:'AndroidApp'
    :param destination_folder: The root-folder the apps will be copied to.
    :param firmware_mount_path: The source path in which the firmware is mounted.
    """
    for android_app in firmware_app_list:
        app_folder = destination_folder + android_app.relative_firmware_path + "/"
        Path(app_folder).mkdir(parents=True, exist_ok=True)
        android_app_filepath = os.path.join(firmware_mount_path,
                                            "." + android_app.relative_firmware_path,
                                            android_app.filename)
        if os.path.isfile(android_app_filepath) and os.access(android_app_filepath, os.R_OK):
            android_app.sha256 = sha256_from_file(android_app_filepath)
            android_app.md5 = md5_from_file(android_app_filepath)
            android_app.sha1 = sha1_from_file(android_app_filepath)
            android_app_destination_filepath = os.path.join(app_folder, android_app.filename)
            copyfile(android_app_filepath, android_app_destination_filepath)
            if not os.path.isfile(android_app_destination_filepath):
                raise ValueError(f"Could not copy Android app: from {android_app_filepath} "
                                 f"to {android_app_destination_filepath}")
            android_app.relative_store_path = android_app_destination_filepath
            android_app.absolute_store_path = os.path.abspath(android_app_destination_filepath)
            android_app.file_size_bytes = os.path.getsize(android_app.absolute_store_path)
            #logging.info(f"Save Android App in db {android_app.filename} from {android_app.absolute_store_path}")
            android_app.save()
        else:
            raise ValueError(f"Could not extract Android app: {android_app.filename} from {android_app_filepath}.")


def find_android_apps(search_path):
    """
    Returns a list of .apkandroid_app_list files within the given path.
    :param search_path: The path to search through.
    :return: List of object class:'AndroidApp'.
    """
    firmware_apps = []
    for root, dirs, files in os.walk(search_path):
        for filename in files:
            app_abs_path = os.path.join(root, filename)
            if filename.lower().endswith(".apk") and os.path.isfile(app_abs_path):
                app_path = root.replace(search_path, "")
                android_app = AndroidApp(filename=filename,
                                         relative_firmware_path=app_path)
                firmware_apps.append(android_app)
    logging.info(f"Found .apk files in partition: {len(firmware_apps)}")
    if len(firmware_apps) < 1:
        raise ValueError(f"Could not find any .apk files in {search_path}!")
    return firmware_apps
