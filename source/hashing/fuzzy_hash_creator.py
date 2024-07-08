# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import tempfile
import traceback
from queue import Empty
from threading import Thread
from mongoengine import DoesNotExist
from hashing.ssdeep.ssdeep_hasher import create_ssdeep_hash
from hashing.tlsh.tlsh_hasher import create_tlsh_hash
from model import AndroidFirmware, FirmwareFile
from firmware_handler.firmware_file_exporter import extract_firmware
from context.context_creator import create_db_context, create_log_context
from model.StoreSetting import get_active_store_by_index
from utils.mulitprocessing_util.mp_util import create_multi_threading_queue

NUMBER_OF_FUZZY_HASH_THREADS = 4


@create_log_context
@create_db_context
def start_fuzzy_hasher(firmware_id_list, storage_index):
    """
    Creates a context and starts the fuzzy hashing process.

    :param storage_index: int - index of the storage.
    :param firmware_id_list: list(str) - list of class:'AndroidFirmware' object-id's.

    """
    logging.info(f"Fuzzy hashing started with {len(firmware_id_list)} firmware ids.")
    start_fuzzy_hash_multithreading(firmware_id_list, storage_index)


def start_fuzzy_hash_multithreading(firmware_id_list, storage_index):
    """
    Starts to export firmware files to the filesystem.

    :return: str - path to the exported file.

    """
    firmware_id_queue = create_multi_threading_queue(firmware_id_list)
    for i in range(NUMBER_OF_FUZZY_HASH_THREADS):
        worker = Thread(target=fuzzy_hash_worker_multithreading, args=(firmware_id_queue, storage_index))
        worker.setDaemon(True)
        worker.start()
    firmware_id_queue.join()


def fuzzy_hash_worker_multithreading(firmware_id_queue, storage_index):
    """
    Create fuzzy hashes for all firmware files. Extracts and mounts the firmware.

    :param storage_index: int - index of the storage.
    :param firmware_id_queue: class:'Queue' - queue of firmware-id's.

    """
    while True:
        try:
            firmware_id = firmware_id_queue.get(block=False, timeout=300)
            logging.info(f"Fuzzy Hasher: Indexing firmware-id: {firmware_id} "
                         f"estimated queue size {firmware_id_queue.qsize()}")
        except Empty:
            break
        try:
            firmware = AndroidFirmware.objects.get(pk=firmware_id)
            store_setting = get_active_store_by_index(storage_index)
            if not store_setting:
                raise ValueError(f"Store settings not found for index: {storage_index}")
            store_paths = store_setting.get_store_paths()
            with tempfile.TemporaryDirectory(dir=store_paths["FIRMWARE_FOLDER_CACHE"]) as temp_dir_path:
                firmware_file_list = extract_firmware(firmware.absolute_store_path, temp_dir_path, store_paths)
                firmware_file_list = create_missing_firmware_files(firmware_file_list, firmware)
                add_fuzzy_hashes(firmware_file_list)
        except Exception as err:
            logging.error(err)
            traceback.print_exc()
        finally:
            firmware_id_queue.task_done()


def create_missing_firmware_files(firmware_file_list, firmware):
    """
    Creates missing firmware files for the given firmware.

    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware files.
    :param firmware: class:'AndroidFirmware' - firmware object.

    :return: list(class:'FirmwareFile') - list of firmware files.

    """
    resulting_firmware_files = []
    for firmware_file in firmware_file_list:
        try:
            firmware_file = FirmwareFile.objects.get(md5=firmware_file.md5, firmware_id_reference=firmware.id)
            resulting_firmware_files.append(firmware_file)
        except DoesNotExist:
            firmware_file.firmware_id_reference = firmware.id
            firmware_file.save()
            firmware.firmware_files.append(firmware_file)
            firmware.save()
            resulting_firmware_files.append(firmware_file)
    return resulting_firmware_files


def add_fuzzy_hashes(firmware_file_list):
    """
    Creates fuzzy hashes for the given firmware files.

    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware files to be hashed.

    """
    for firmware_file in firmware_file_list:
        if not firmware_file.is_directory:
            if os.path.exists(firmware_file.absolute_store_path):
                try:
                    create_tlsh_hash(firmware_file)
                    create_ssdeep_hash(firmware_file)
                except Exception as err:
                    logging.error(err)
            else:
                logging.warning(f"Could not hash file: {firmware_file.absolute_store_path}")
