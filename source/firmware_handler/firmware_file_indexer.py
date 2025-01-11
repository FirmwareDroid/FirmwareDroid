# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
from multiprocessing import Lock
from model import FirmwareFile
from hashing import md5_from_file
from utils.file_utils.file_util import get_file_libmagic

lock = Lock()


def create_firmware_file_list(scan_directory, partition_name):
    """
    Creates a list of firmware files from the given directory.

    :param partition_name: str - name of the partition.
    :param scan_directory: str - path to the directory to scan
    :return: list(class:'FirmwareFile')

    """
    result_firmware_file_list = []
    for root, dir_list, file_list in os.walk(scan_directory):
        result_firmware_file_list = process_directories(dir_list,
                                                        root,
                                                        scan_directory,
                                                        partition_name,
                                                        result_firmware_file_list)
        result_firmware_file_list = process_files(file_list,
                                                  root,
                                                  scan_directory,
                                                  partition_name,
                                                  result_firmware_file_list)
    return result_firmware_file_list


def normalize_file_path(file_path):
    """
    Normalize and escape the file path.

    :param file_path: str - path to the file.

    :return: str - normalized and escaped file path.

    """
    file_path = file_path.strip()
    file_path = os.path.normpath(file_path)
    return file_path


def get_parent_name(root, scan_directory):
    """
    Get the name of the parent directory.

    :param root: str - path to the current directory
    :param scan_directory: str - path to the directory to scan

    :return: str - name of the parent directory.

    """
    parent_name = os.path.basename(root) if os.path.basename(root) else "/"
    if parent_name == os.path.basename(scan_directory):
        parent_name = "/"
    return parent_name


def process_directories(dir_list, root, scan_directory, partition_name, result_firmware_file_list):
    """
    Process the directories in the given directory.

    :param dir_list: list(str) - list of directories
    :param root: str - path to the current directory
    :param scan_directory: str - path to the directory to scan
    :param partition_name: str - name of the partition.
    :param result_firmware_file_list: list(class:'FirmwareFile') - list of firmware files

    :return: list(class:'FirmwareFile') - list of firmware files

    """
    for directory in dir_list:
        relative_dir_path = os.path.join(root.replace(scan_directory, ""), directory)
        parent_name = get_parent_name(root, scan_directory)
        firmware_file = create_firmware_file(name=directory,
                                             parent_name=parent_name,
                                             is_directory=True,
                                             relative_file_path=relative_dir_path,
                                             absolute_store_path=os.path.join(root, directory),
                                             partition_name=partition_name,
                                             md5=None)
        result_firmware_file_list.append(firmware_file)
    return result_firmware_file_list


def process_files(file_list, root, scan_directory, partition_name, result_firmware_file_list):
    """
    Process the files in the given directory.

    :param file_list: list(str) - list of files
    :param root: str - path to the current directory
    :param scan_directory: str - path to the directory to scan
    :param partition_name: str - name of the partition.
    :param result_firmware_file_list: list(class:'FirmwareFile') - list of firmware files

    :return: list(class:'FirmwareFile') - list of firmware files

    """
    for filename in file_list:
        relative_file_path = os.path.join(root.replace(scan_directory, ""), filename)
        filename_path = os.path.join(root, filename)
        if os.path.isfile(filename_path) and os.path.exists(filename_path):
            try:
                md5_file = md5_from_file(filename_path)
                file_size_bytes = os.path.getsize(filename_path)
                parent_name = get_parent_name(root, scan_directory)
                filename_abs_path = os.path.abspath(str(filename_path))
                filename_abs_path = os.path.realpath(filename_abs_path)
                filename_abs_path = normalize_file_path(filename_abs_path)
                if not os.path.exists(filename_abs_path) or not os.path.isfile(filename_abs_path):
                    raise ValueError(f"Firmware File could not be created because file does not exist: "
                                     f"{filename_abs_path}")

                firmware_file = create_firmware_file(name=filename,
                                                     parent_name=parent_name,
                                                     is_directory=False,
                                                     file_size_bytes=file_size_bytes,
                                                     relative_file_path=relative_file_path,
                                                     absolute_store_path=filename_abs_path,
                                                     partition_name=partition_name,
                                                     meta_dict={"libmagic": get_file_libmagic(filename_path)},
                                                     md5=md5_file)
                result_firmware_file_list.append(firmware_file)
            except Exception as err:
                logging.warning(err)
    return result_firmware_file_list


def create_firmware_file(name,
                         parent_name,
                         is_directory,
                         relative_file_path,
                         absolute_store_path,
                         partition_name,
                         md5,
                         file_size_bytes=None,
                         meta_dict=None):
    """
    Creates a class:'FirmwareFile' document. Does not save the document to the database.

    :param absolute_store_path: str - absolute path to the file.
    :param meta_dict: dict - metadata for the file.
    :param file_size_bytes: int - file size in bytes
    :param partition_name: str - name of the partition.
    :param name: str - name of file or directory
    :param parent_name: str - name of the parent directory
    :param is_directory: bool - true if it is a directory
    :param relative_file_path: str - relative path within the firmware
    :param md5: str - md5 digest of the file.

    :return: class:'FirmwareFile' - instance of FirmwareFile

    """
    if meta_dict is None:
        meta_dict = {}
    is_link = os.path.islink(absolute_store_path)
    return FirmwareFile(name=name,
                        parent_dir=parent_name,
                        is_directory=is_directory,
                        is_link=is_link,
                        file_size_bytes=file_size_bytes,
                        absolute_store_path=absolute_store_path,
                        relative_path=relative_file_path,
                        partition_name=partition_name,
                        meta_dict=meta_dict,
                        md5=md5).save()


def add_firmware_file_references(firmware, firmware_file_list):
    """
    Add the firmware references for the given files. Saves the reference in the database.

    :param firmware: class:'AndroidFirmware'
    :param firmware_file_list: list of class:'FirmwareFile'

    """
    if len(firmware_file_list) > 0:
        logging.debug(f"Add file references for: {firmware.id}")
        firmware_file_ids = []
        for firmware_file in firmware_file_list:
            firmware_file.firmware_id_reference = firmware.id
            firmware_file.save()
            firmware_file_ids.append(firmware_file.id)
        firmware.firmware_file_id_list = firmware_file_ids
        firmware.has_file_index = True
        firmware.save()
        logging.debug(f"Successfully added firmware file references: {firmware.id} {len(firmware_file_list)}")
    else:
        raise ValueError(f"No firmware file references added: firmware-id {firmware.id} {len(firmware_file_list)}")
