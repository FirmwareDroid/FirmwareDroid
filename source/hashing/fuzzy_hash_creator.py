# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import traceback
from firmware_handler.ext4_mount_util import is_path_mounted, exec_umount
from model import AndroidFirmware
from firmware_handler.firmware_file_exporter import get_firmware_file_abs_path, extract_image_files
from hashing.ssdeep.ssdeep_hasher import start_ssdeep_hashing
from hashing.tlsh.tlsh_hasher import start_tlsh_hashing
from context.context_creator import push_app_context
from utils.mulitprocessing_util.mp_util import start_process_pool
from utils.file_utils.file_util import create_temp_directories


@push_app_context
def start_fuzzy_hasher(firmware_id_list):
    """
    Creats a context and starts the ssdeep hasher.

    :param firmware_id_list: list(str) - list of class:'AndroidFirmware' object-id's.

    """
    logging.info(f"Fuzzy hashing started: {len(firmware_id_list)} firmware archives")
    start_process_pool(firmware_id_list, hash_firmware_files_parallel,
                       number_of_processes=os.cpu_count(),
                       use_id_list=False)


def hash_firmware_files_parallel(firmware_id_queue):
    """
    Create fuzzy hashes for all firmware files. Extracts and mounts the firmware.

    :param firmware_id_queue: multiprocessing.queue - queue if class:'AndroidFirmware' object-ids

    """
    while not firmware_id_queue.empty():
        firmware_id = firmware_id_queue.get()
        logging.info(f"Hasher: {firmware_id} estimated queue size {firmware_id_queue.qsize()}")
        cache_temp_file_dir, cache_temp_mount_dir = create_temp_directories()
        try:
            firmware = AndroidFirmware.objects.get(pk=firmware_id)
            if not firmware.hasFuzzyHashIndex:
                logging.info(f"Starting fuzzy hashing index creation: {firmware_id}")
                # TODO FIX THIS
                extract_image_files(firmware, cache_temp_file_dir.name, cache_temp_mount_dir.name)
                fuzzy_hash_firmware(firmware, cache_temp_mount_dir.name)
            else:
                logging.info(f"Firmware has index already: {firmware_id}")
        except Exception as err:
            logging.error(err)
            traceback.print_exc()
        finally:
            if is_path_mounted(cache_temp_mount_dir.name):
                exec_umount(cache_temp_mount_dir.name)


def fuzzy_hash_firmware(firmware, mount_path):
    """
    Create fuzzy hashes for all firmware files. Needs the firmware files to be accessible.

    :param firmware: class:'AndroidFirmware' - Android firmware which will be indexed.
    :param mount_path: str - path where the firmware is mounted.

    """
    for firmware_file_id_lazy in firmware.firmware_file_id_list:
        firmware_file = firmware_file_id_lazy.fetch()
        fuzzy_hash_firmware_files([firmware_file], mount_path)
    firmware.save()


def fuzzy_hash_firmware_files(firmware_file_list, mount_path):
    """
    Create fuzzy hashes for a firmware file. Needs the firmware file to be accessible in the file system.

    :param firmware_file_list: list(class:'FirmwareFile') - Android firmware file which will be indexed.
    :param mount_path: str - path where the firmware is accessible.

    """
    for firmware_file in firmware_file_list:
        if not firmware_file.isDirectory: #and firmware_file.partition_name == "system":
            firmware_file.absolute_store_path = get_firmware_file_abs_path(firmware_file, mount_path)
            firmware_file.save()
            if os.path.exists(firmware_file.absolute_store_path):
                create_fuzzy_hashes(firmware_file)
            else:
                logging.error(f"Could not access file: {firmware_file.absolute_store_path}")


def create_fuzzy_hashes(firmware_file):
    """
    Creates a fuzzy hash for the given file.

    :param firmware_file: class:'FirmwareFile'


    """
    if not firmware_file.ssdeep_reference:
        start_ssdeep_hashing(firmware_file)
    if not firmware_file.tlsh_reference:
        start_tlsh_hashing(firmware_file)
    #if not firmware_file.lzjd_reference:
    #    start_lzjd_hashing(firmware_file)
