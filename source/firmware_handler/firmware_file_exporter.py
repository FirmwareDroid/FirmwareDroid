# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import glob
import logging
import os
import re
import shutil
import tempfile
from queue import Empty
from threading import Thread
from context.context_creator import create_db_context, create_log_context
from extractor.expand_archives import extract_archive_layer
from firmware_handler.const_regex_patterns import EXT_IMAGE_PATTERNS_DICT
from firmware_handler.firmware_file_indexer import create_firmware_file_list
from hashing import md5_from_file
from model import StoreSetting, AndroidFirmware
from utils.mulitprocessing_util.mp_util import create_multi_threading_queue

NUMBER_OF_EXPORTER_THREADS = 10
NAME_EXPORT_FOLDER = "firmware_file_export"
UNBLOB_WORKER_COUNT = 1
UNBLBOB_DEPTH = 10


@create_db_context
@create_log_context
def start_file_export_by_regex(filename_regex, firmware_id_list, store_setting_id):
    """
    Starts a firmware file export. Uses a regex and the given firmware to pre-filter firmware-files.

    :param store_setting_id: str - id of the store setting.
    :param firmware_id_list: list(str) - list of firmware ids to export.
    :param filename_regex: str - regex for filtering the set of firmware files by
    filename.

    """
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    if len(firmware_id_list) == 0:
        raise ValueError("No firmware ids given.")
    if not search_pattern:
        raise ValueError("No search pattern given.")
    if not store_setting_id:
        raise ValueError("No store setting id given.")
    start_firmware_file_export(search_pattern, firmware_id_list, store_setting_id)


def start_firmware_file_export(search_pattern, firmware_id_list, store_setting_id):
    """
    Starts to export firmware files to the filesystem.

    :return: str - path to the exported file.

    """
    firmware_id_queue = create_multi_threading_queue(firmware_id_list)
    for i in range(NUMBER_OF_EXPORTER_THREADS):
        logging.debug(f"Start exporter thread {i} of {NUMBER_OF_EXPORTER_THREADS}")
        worker = Thread(target=export_worker_multithreading, args=(firmware_id_queue, store_setting_id, search_pattern))
        worker.setDaemon(True)
        worker.start()
    firmware_id_queue.join()


@create_db_context
@create_log_context
def export_worker_multithreading(firmware_id_queue, store_setting_id, search_pattern):
    """
    Copies a firmware file to the file extract store (on disk).

    :param search_pattern: regex pattern to filter the firmware files.
    :param store_setting_id: str - id of the store setting.
    :param firmware_id_queue: class:'Queue' - queue of firmware file ids to export.

    """
    while True:
        try:
            firmware_id = firmware_id_queue.get(block=False, timeout=300)
        except Empty:
            logging.debug("No more files to export on. Exiting.")
            break
        firmware = AndroidFirmware.objects.get(pk=firmware_id)
        store_setting = StoreSetting.objects.get(pk=store_setting_id, is_active=True)
        if not store_setting:
            raise ValueError(f"Store settings not found for id {store_setting_id}")
        store_paths = store_setting.get_store_paths()
        with tempfile.TemporaryDirectory(dir=store_paths["FIRMWARE_FOLDER_CACHE"]) as temp_dir_path:
            firmware_file_list = extract_firmware(firmware.absolute_store_path, temp_dir_path, store_paths)
            for firmware_file in firmware_file_list:
                if re.search(search_pattern, firmware_file.name):
                    firmware_file.firmware_id_reference = firmware.id
                    if firmware_file.partition_name == "/":
                        firmware_file.partition_name = "root"
                    destination_path_abs = get_file_export_path_abs(store_setting, firmware_file)
                    is_successful = export_firmware_file(firmware_file, temp_dir_path, destination_path_abs)
                    if is_successful:
                        logging.debug(f"Exported firmware file {firmware_file.id} to {destination_path_abs}")

        firmware_id_queue.task_done()


def extract_firmware(firmware_archive_file_path, temp_extract_dir, store_paths):
    """
    Extracts a firmware to the given folder.

    :param firmware_archive_file_path: str - path to the firmware to extract.
    :param temp_extract_dir: str - destination folder to extract the firmware to.

    :return: list(class:FirmwareFile)

    """
    from firmware_handler.firmware_importer import create_partition_file_index
    firmware_file_list = []
    extract_archive_layer(firmware_archive_file_path, temp_extract_dir, False, 2)
    top_level_firmware_file_list = create_firmware_file_list(temp_extract_dir, "/")
    for partition_name, file_pattern_list in EXT_IMAGE_PATTERNS_DICT.items():
        logging.info(f"Attempt to index files for partition: {partition_name}")
        partition_temp_dir = tempfile.mkdtemp(dir=temp_extract_dir)
        partition_firmware_file_list, is_successful = create_partition_file_index(partition_name,
                                                                                  file_pattern_list,
                                                                                  top_level_firmware_file_list,
                                                                                  temp_extract_dir,
                                                                                  partition_temp_dir,
                                                                                  store_paths)
        if is_successful:
            firmware_file_list.extend(partition_firmware_file_list)
    return firmware_file_list


def remove_unblob_extract_directories(path):
    """
    Removes the unblob "_extract" directories from the path.

    :param path: str - path to remove the directories from.

    :return: str - path without the "_extract" directories.

    """
    directories = path.split(os.sep)
    directories = [dir for dir in directories if "_extract" not in dir]
    new_path = os.sep.join(directories)
    return new_path


def get_file_export_path_abs(store_setting, firmware_file):
    """
    Returns the absolute path, where the file is exported to.

    :param store_setting: class:'StoreSetting'
    :param firmware_file: class:'FirmwareFile'

    :return: str - absolute path of the output folder.

    """
    store_paths = store_setting.store_options_dict[store_setting.uuid]["paths"]
    logging.debug(f"Normalize path: {firmware_file.relative_path}")
    minimized_relative_path = remove_unblob_extract_directories(firmware_file.relative_path)
    logging.debug(f"Minimized path: {minimized_relative_path}")
    store_path_abs = os.path.abspath(store_paths["FIRMWARE_FOLDER_FILE_EXTRACT"])
    logging.debug(f"{store_path_abs},"
                  f"{NAME_EXPORT_FOLDER}, "
                  f"{firmware_file.firmware_id_reference.pk},"
                  f"{firmware_file.partition_name},"
                  f"{minimized_relative_path}")

    destination_folder = os.path.join(store_path_abs,
                                      NAME_EXPORT_FOLDER,
                                      str(firmware_file.firmware_id_reference.pk),
                                      firmware_file.partition_name,
                                      "." + minimized_relative_path)

    logging.debug(f"Exporting firmware file {firmware_file.id} to {destination_folder}")
    destination_folder_abs = os.path.abspath(destination_folder)
    logging.info(f"Exporting firmware file {firmware_file.id} to {destination_folder_abs}")
    return destination_folder_abs


def export_firmware_file(firmware_file, source_dir_path, destination_dir_path):
    """
    Exports a file from the firmware to the file extract folder.

    :param destination_dir_path: str - path to the file storage, where the file will be copied to.
    :param firmware_file: class:'FirmwareFile'
    :param source_dir_path: str - path to the extracted firmware.

    :return: bool - flag if the export was successful.
    """
    is_successful = False
    if os.path.exists(source_dir_path) and firmware_file:
        firmware_file_abs_path = get_firmware_file_abs_path(firmware_file, source_dir_path)
    else:
        raise FileNotFoundError(f"Source directory {source_dir_path} does not exist.")

    if firmware_file_abs_path:
        copy_firmware_file(firmware_file, firmware_file_abs_path, destination_dir_path)
        is_successful = True
    else:
        logging.error(f"Could not find firmware file {firmware_file.id} {firmware_file.name}."
                      f" Skipping file {source_dir_path}")
    return is_successful


def create_directory(destination_path, firmware_file):
    if os.path.splitext(destination_path)[1] or firmware_file.is_directory is False:
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    else:
        os.makedirs(destination_path, exist_ok=True)


def copy_firmware_file(firmware_file, source_path, destination_path):
    """
    Copy a class:'FirmwareFile' to the filesystem.

    :param firmware_file: class:'FirmwareFile'
    :param source_path: str - path of the extracted class:'FirmwareFile'
    :param destination_path: str - path to copy the file/folder to.

    """
    create_directory(destination_path, firmware_file)
    dst_file_path = None
    try:
        if os.path.isdir(source_path):
            dst_file_path = shutil.copytree(source_path, destination_path)
        else:
            dst_file_path = shutil.copy(source_path, destination_path)
    except OSError as e:
        logging.error(f"Could not copy: {source_path} to {os.path.dirname(destination_path)} error: {e}")
    if dst_file_path is None or not os.path.exists(dst_file_path):
        raise OSError(f"Could not copy firmware file {firmware_file.id} to {destination_path}")


def find_firmware_file_abs_path(firmware_file, source_dir_path):
    """
    Finds a file in the extracted firmware directory by md5 matching.

    :param firmware_file: class:'FirmwareFile'
    :param source_dir_path: str - path of the mount directory.

    :return: str - path of the firmware file.

    """
    file_abs_path = None
    candidate_files = []
    for root, dirs, files in os.walk(source_dir_path):
        if firmware_file.name in files:
            for file in files:
                if file == firmware_file.name:
                    file_abs_path = os.path.join(root, file)
                    if os.path.exists(file_abs_path):
                        md5 = md5_from_file(file_abs_path)
                        if md5 == firmware_file.md5:
                            break
                        else:
                            candidate_files.append(file_abs_path)
                    else:
                        file_abs_path = None
    if file_abs_path is None and len(candidate_files) > 0:
        file_abs_path = candidate_files[0]
    return file_abs_path


def get_firmware_file_abs_path(firmware_file, source_dir_path):
    """
    Creates an absolute path from the extracted firmware directory and the relative firmware file path.

    :param firmware_file: class:'FirmwareFile'
    :param source_dir_path: str - path of the mount directory.
    :return: str - absolute path of the firmware file.

    """
    logging.info(f"Searching for firmware file {firmware_file.id} in {source_dir_path}")
    firmware_file_abs_path = find_firmware_file_abs_path(firmware_file, source_dir_path)
    if not firmware_file_abs_path:
        logging.error(f"Could not find firmware file {firmware_file.id} {firmware_file.name}."
                      f" Skipping file {source_dir_path}")
        firmware_file_abs_path = None
    logging.info(f"Found firmware file {firmware_file.id} at {firmware_file_abs_path}")
    return firmware_file_abs_path
