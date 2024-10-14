# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
import shutil
import tempfile
import traceback
from queue import Empty
from threading import Thread
from context.context_creator import create_db_context, create_log_context, create_multithread_log_context
from extractor.expand_archives import extract_first_layer
from firmware_handler.const_regex_patterns import EXT_IMAGE_PATTERNS_DICT
from firmware_handler.firmware_file_indexer import create_firmware_file_list
from model import StoreSetting, AndroidFirmware
from processing.standalone_python_worker import create_multi_threading_queue

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
    logging.info(f"Start exporting firmware files by regex {filename_regex} for firmware {firmware_id_list}")
    start_regex_firmware_file_export(search_pattern, firmware_id_list, store_setting_id)


def start_regex_firmware_file_export(search_pattern, firmware_id_list, store_setting_id):
    """
    Starts to export firmware files to the filesystem by a regex pattern. Searches for the files in the firmware
    by filename and exports them to the file system. Using a regex pattern to filter the files and multiple threads
    to export the files.

    :return: str - path to the exported file.

    """
    firmware_id_queue = create_multi_threading_queue(firmware_id_list)
    for i in range(NUMBER_OF_EXPORTER_THREADS):
        worker = Thread(target=export_worker_multithreading, args=(firmware_id_queue, store_setting_id, search_pattern))
        worker.daemon = True
        worker.start()
    firmware_id_queue.join()


@create_db_context
@create_multithread_log_context
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
            logging.debug(f"Exporting files for firmware {firmware_id}")
            logging.debug(f"Queue size: {firmware_id_queue.qsize()}")
        except Empty:
            break
        try:
            firmware = AndroidFirmware.objects.get(pk=firmware_id)
            store_setting = StoreSetting.objects.get(pk=store_setting_id, is_active=True)
            if not store_setting:
                raise ValueError(f"Store settings not found for id {store_setting_id}")
            store_paths = store_setting.get_store_paths()
            with (tempfile.TemporaryDirectory(dir=store_paths["FIRMWARE_FOLDER_CACHE"]) as temp_dir_path):
                firmware_file_list = extract_firmware(firmware.absolute_store_path, temp_dir_path)
                for firmware_file in firmware_file_list:
                    # Excluding some Unblob specific file extensions to prevent them from being exported
                    if not firmware_file.is_directory \
                            and re.search(search_pattern, firmware_file.name) \
                            and ".unknown" not in firmware_file.name \
                            and ".padding" not in firmware_file.name \
                            and "_extract" not in firmware_file.name:
                        logging.debug(f"Exporting firmware file {firmware_file.id} {firmware_file.name}")
                        firmware_file.firmware_id_reference = firmware.id
                        if firmware_file.partition_name == "/":
                            firmware_file.partition_name = "root"
                        destination_path_abs = get_file_export_path_abs(store_setting, firmware_file)
                        is_successful = export_firmware_file(firmware_file, temp_dir_path, destination_path_abs)
                        if not is_successful:
                            raise ValueError(f"Could not export firmware file {firmware_file.id} {firmware_file.name}")
            logging.info(f"Exported files from firmware {firmware.id} to {store_paths['FIRMWARE_FOLDER_FILE_EXTRACT']}")
        except Exception as e:
            logging.error(f"Could not export firmware files for firmware {firmware_id}. Error: {e}")
            traceback.print_stack()
        finally:
            firmware_id_queue.task_done()


def extract_firmware(firmware_archive_file_path, temp_extract_dir):
    """
    Extracts a firmware to the given folder.

    :param firmware_archive_file_path: str - path to the firmware to extract.
    :param temp_extract_dir: str - destination folder to extract the firmware to.

    :return: list(class:FirmwareFile)

    """
    from firmware_handler.firmware_importer import create_partition_file_index
    firmware_file_list = []
    extract_first_layer(firmware_archive_file_path, temp_extract_dir)
    logging.info(f"Extracted first layer of firmware {firmware_archive_file_path} to {temp_extract_dir}")
    top_level_firmware_file_list = create_firmware_file_list(temp_extract_dir, "/")
    for partition_name, file_pattern_list in EXT_IMAGE_PATTERNS_DICT.items():
        logging.info(f"Attempt to index files for partition: {partition_name}")
        partition_temp_dir = tempfile.mkdtemp(dir=temp_extract_dir, prefix=f"fmd_extract_{partition_name}_")
        partition_temp_dir = os.path.abspath(partition_temp_dir)
        partition_firmware_file_list, is_successful = create_partition_file_index(partition_name,
                                                                                  file_pattern_list,
                                                                                  top_level_firmware_file_list,
                                                                                  temp_extract_dir,
                                                                                  partition_temp_dir)
        if is_successful:
            firmware_file_list.extend(partition_firmware_file_list)
        else:
            logging.warning(f"Could not index files for partition: {partition_name}")
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
    destination_folder_abs = os.path.abspath(destination_folder)
    logging.debug(f"Exporting firmware file {firmware_file.id} to {destination_folder_abs}")
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
    if firmware_file and firmware_file.absolute_store_path and os.path.exists(firmware_file.absolute_store_path):
        copy_firmware_file(firmware_file, firmware_file.absolute_store_path, destination_dir_path)
        is_successful = True
    else:
        logging.error(f"Could not find firmware file {firmware_file.id} {firmware_file.name} "
                      f"{firmware_file.absolute_store_path}."
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

