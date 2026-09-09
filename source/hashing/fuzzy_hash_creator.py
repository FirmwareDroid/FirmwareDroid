# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import tempfile
import traceback
from queue import Empty
from threading import Thread
from hashing.tlsh.tlsh_hasher import create_tlsh_hash
from model import AndroidFirmware, FirmwareFileSet
from firmware_handler.firmware_file_exporter import extract_firmware
from context.context_creator import create_db_context, create_log_context, create_multithread_log_context
from model.StoreSetting import get_active_store_by_index
from processing.standalone_python_worker import create_multi_threading_queue

NUMBER_OF_FUZZY_HASH_THREADS = 4
FIRMWARE_FILE_SET_CHUNK_SIZE = 1000


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


@create_multithread_log_context
@create_db_context
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
                firmware_file_list = extract_firmware(firmware.absolute_store_path, temp_dir_path)
                replace_firmware_files(firmware_file_list, firmware, store_paths)
                add_fuzzy_hashes_by_firmware_file_sets(firmware.firmware_file_set_list)
                firmware.has_fuzzy_hash_index = True
                firmware.save()
        except Exception as err:
            logging.error(err)
            traceback.print_exc()
        finally:
            firmware_id_queue.task_done()


def replace_firmware_files(firmware_file_list, firmware, store_paths):
    """
    Creates missing firmware files for the given firmware in case they do not exist.

    :param store_paths: str - path to the store.
    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware files.
    :param firmware: class:'AndroidFirmware' - firmware object.

    :return: list(class:'FirmwareFile') - list of firmware files.

    """
    firmware_file_sets = []
    for firmware_file_set_lazy in firmware.firmware_file_set_list:
        try:
            firmware_file_sets.append(firmware_file_set_lazy.fetch())
        except Exception as err:
            logging.warning(err)

    for firmware_file_set in firmware_file_sets:
        for existing_firmware_file_lazy in firmware_file_set.firmware_file_id_list:
            try:
                existing_firmware_file = existing_firmware_file_lazy.fetch()
                existing_firmware_file.delete()
            except Exception as err:
                logging.warning(err)
        firmware_file_set.delete()

    firmware.firmware_file_set_list = []
    firmware.save()
    firmware_file_ids = []
    for firmware_file in firmware_file_list:
        firmware_file.firmware_id_reference = firmware.id
        firmware_file.save()
        firmware_file_ids.append(firmware_file.id)

    firmware_file_set_list = []
    for i in range(0, len(firmware_file_ids), FIRMWARE_FILE_SET_CHUNK_SIZE):
        firmware_file_set = FirmwareFileSet(firmware_id_reference=firmware.id,
                                            firmware_file_id_list=firmware_file_ids[i:i + FIRMWARE_FILE_SET_CHUNK_SIZE]).save()
        firmware_file_set_list.append(firmware_file_set.id)

    firmware.firmware_file_set_list = firmware_file_set_list
    firmware.save()


def add_fuzzy_hashes_by_firmware_file_sets(firmware_file_set_list):
    """
    Creates fuzzy hashes for firmware files referenced by firmware file sets.

    :param firmware_file_set_list: list(class:'FirmwareFileSet') - list of lazy firmware file sets.

    """
    for firmware_file_set_lazy in firmware_file_set_list:
        firmware_file_set = firmware_file_set_lazy.fetch()
        for firmware_file_lazy in firmware_file_set.firmware_file_id_list:
            firmware_file = firmware_file_lazy.fetch()
            if not firmware_file.is_directory:
                logging.info(f"Creating fuzzy hashes for: {firmware_file.absolute_store_path}")
                try:
                    create_tlsh_hash(firmware_file)
                    #create_ssdeep_hash(firmware_file)
                except Exception as err:
                    logging.error(err)


def add_fuzzy_hashes(firmware_file_list):
    """
    Creates fuzzy hashes for the given firmware files and stored them in the database.
    """
    for firmware_file in firmware_file_list:
        if not firmware_file.is_directory:
            logging.info(f"Creating fuzzy hashes for: {firmware_file.absolute_store_path}")
            try:
                create_tlsh_hash(firmware_file)
                #create_ssdeep_hash(firmware_file)
            except Exception as err:
                logging.error(err)
