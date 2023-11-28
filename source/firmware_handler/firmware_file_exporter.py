# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import shutil
import time
from firmware_handler.image_importer import extract_image_files
from context.context_creator import create_db_context
from firmware_handler.ext4_mount_util import is_path_mounted, exec_umount
from model import FirmwareFile
from utils.mulitprocessing_util.mp_util import start_python_interpreter
from utils.file_utils.file_util import create_temp_directories

from setup.default_setup import get_active_file_store_paths
STORE_PATHS = get_active_file_store_paths()



@create_db_context
def start_file_export_by_regex(filename_regex, firmware_id_list):
    """
    Starts a firmware file export. Uses a regex and the given firmware to pre-filter firmware-files.

    :param filename_regex: regular expression pattern object - regex for filtering the set of firmware files by
    filename.
    :param firmware_id_list: list(class:'AndroidFirmware')

    """
    firmware_file_id_list = get_filtered_firmware_file_list(filename_regex, firmware_id_list)
    start_file_export_by_id(firmware_file_id_list)


def get_filtered_firmware_file_list(filename_regex, firmware_id_list):
    """
    Gets a list of firmware file id's filtered by the given filename regex and the given firmware list.

    :param filename_regex: regular expression pattern object - regex for filtering the set of firmware files by
    filename.
    :param firmware_id_list: list(class:'AndroidFirmware')
    :return: list(object-id's) - list of object-id's from class:'FirmwareFile'

    """
    firmware_file_id_list = []
    if filename_regex and len(firmware_id_list) > 0:
        for firmware_id in firmware_id_list:
            firmware_file_list = FirmwareFile.objects(firmware_id_reference=firmware_id, name=filename_regex)
            if len(firmware_file_list) > 0:
                for firmware_file in firmware_file_list:
                    firmware_file_id_list.append(firmware_file.id)
    return firmware_file_id_list


@create_db_context
def start_file_export_by_id(firmware_file_id_list):
    """
    Starts to export firmware files to the filesystem.

    :param firmware_file_id_list: list(str) - list of object-ids of the class:'FirmwareFile'.
    :return: str - path to the exported file.

    """
    if len(firmware_file_id_list) > 0:
        start_python_interpreter(firmware_file_id_list, export_firmware_files_by_id,
                                 number_of_processes=os.cpu_count(),
                                 use_id_list=False)


def export_firmware_files_by_id(firmware_file_id_queue):
    """
    Copies a firmware file to the file extract store (on disk).

    :param firmware_file_id_queue: multiprocessing.queue - queue of id to process.

    """
    while not firmware_file_id_queue.empty():
        firmware_file_id = firmware_file_id_queue.get()
        firmware_file = FirmwareFile.objects.get(pk=firmware_file_id)
        firmware = firmware_file.firmware_id_reference.fetch()
        cache_temp_file_dir, cache_temp_mount_dir = create_temp_directories()
        #   TODO fix this method
        extract_image_files(firmware, cache_temp_file_dir.name, cache_temp_mount_dir.name)
        logging.info(f"Export file: {firmware.name}")
        try:
            firmware_file = FirmwareFile.objects.get(pk=firmware_file_id)
            export_firmware_file(firmware_file, cache_temp_mount_dir.name)
        except FileExistsError:
            pass
        if is_path_mounted(cache_temp_mount_dir.name):
            exec_umount(cache_temp_mount_dir.name)


def export_firmware_file(firmware_file, mount_dir_path):
    """
    Exports a file from the firmware to the file extract folder.

    :param firmware_file: class:'FirmwareFile'
    :param mount_dir_path: str - path to the expanded firmware.

    """
    firmware_file_abs_path = get_firmware_file_abs_path(firmware_file, mount_dir_path)
    destination_folder = get_destination_folder(firmware_file)
    copy_firmware_file(firmware_file, firmware_file_abs_path, destination_folder)


def copy_firmware_file(firmware_file, source_path, destination_path):
    """
    Copy a class:'FirmwareFile' to the filesystem.

    :param firmware_file: class:'FirmwareFile'
    :param source_path: str - path of the extracted class:'FirmwareFile'
    :param destination_path: str - path to copy the file/folder to.

    """
    if firmware_file.isDirectory:
        dst_file_path = shutil.copytree(source_path, destination_path)
    else:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        time.sleep(5)
        dst_file_path = shutil.copy(source_path, destination_path)
        logging.info(f"File copy successful: {destination_path}")
    time.sleep(5)
    if not os.path.exists(dst_file_path):
        OSError(f"Could not copy firmware file {firmware_file.id} to {destination_path}")


def get_destination_folder(firmware_file):
    """
    Creates a unique destination folder for a firmware file.

    :param firmware_file: class:'FirmwareFile'
    :return: str - absolute path of the output folder.

    """
    destination_folder = os.path.join(STORE_PATHS["FIRMWARE_FOLDER_FILE_EXTRACT"],
                                      str(firmware_file.id),
                                      "." + firmware_file.relative_path)
    return os.path.abspath(destination_folder)


def get_firmware_file_abs_path(firmware_file, mount_dir_path):
    """
    Creates an absolute path from the mount directory and the relative firmware file path.

    :param firmware_file: class:'FirmwareFile'
    :param mount_dir_path: str - path of the mount directory.
    :return: str - absolute path of the firmware file.

    """
    if firmware_file.relative_path.startswith("/"):
        firmware_file_abs_path = os.path.join(mount_dir_path,
                                              firmware_file.relative_path.replace("/", "", 1))
    else:
        firmware_file_abs_path = os.path.join(mount_dir_path, firmware_file.relative_path)
    return os.path.abspath(firmware_file_abs_path)
