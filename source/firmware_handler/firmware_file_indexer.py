# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
from multiprocessing import Lock
from model import FirmwareFile, FirmwareFileSet
from hashing import md5_from_file
from utils.file_utils.file_util import get_file_libmagic

lock = Lock()
FIRMWARE_FILE_SET_CHUNK_SIZE = 1000


def create_firmware_file_list(scan_directory, partition_name):
    """
    Creates a list of firmware files from the given directory.

    :param partition_name: str - name of the partition.
    :param scan_directory: str - path to the directory to scan
    :return: list(class:'FirmwareFile')

    """
    result_firmware_file_list = []
    for root, dir_list, file_list in os.walk(scan_directory, followlinks=False):
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
        absolute_path = os.path.join(root, directory)
        if os.path.exists(absolute_path) and os.path.isdir(absolute_path):
            relative_dir_path = os.path.join(root.replace(scan_directory, ""), directory)
            parent_name = get_parent_name(root, scan_directory)
            firmware_file = create_firmware_file(name=directory,
                                                 parent_name=parent_name,
                                                 is_directory=True,
                                                 relative_file_path=relative_dir_path,
                                                 absolute_store_path=absolute_path,
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
                        is_symlink=is_link,
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
        from pymongo import UpdateOne
        firmware_file_ids = []
        bulk_ops = []
        for firmware_file in firmware_file_list:
            firmware_file.firmware_id_reference = firmware.id
            firmware_file_ids.append(firmware_file.id)
            bulk_ops.append(
                UpdateOne(
                    {"_id": firmware_file.id},
                    {
                        "$set": {
                            "firmware_id_reference": firmware.id,
                            "is_on_disk": getattr(firmware_file, "is_on_disk", False) is True,
                            "absolute_store_path": firmware_file.absolute_store_path,
                        }
                    }
                )
            )
            if len(bulk_ops) >= 1000:
                try:
                    FirmwareFile._get_collection().bulk_write(bulk_ops, ordered=False)
                except Exception as e:
                    logging.warning(f"bulk_write failed during add_firmware_file_references: {e}")
                bulk_ops = []

        if bulk_ops:
            try:
                FirmwareFile._get_collection().bulk_write(bulk_ops, ordered=False)
            except Exception as e:
                logging.warning(f"bulk_write failed during add_firmware_file_references: {e}")

        firmware_file_set_list = []
        for i in range(0, len(firmware_file_ids), FIRMWARE_FILE_SET_CHUNK_SIZE):
            firmware_file_set = FirmwareFileSet(firmware_id_reference=firmware.id,
                                                firmware_file_id_list=firmware_file_ids[i:i + FIRMWARE_FILE_SET_CHUNK_SIZE]).save()
            firmware_file_set_list.append(firmware_file_set.id)
        firmware.firmware_file_set_list = firmware_file_set_list
        firmware.has_file_index = True
        firmware.save()
        logging.debug(f"Successfully added firmware file references: {firmware.id} {len(firmware_file_list)}")
    else:
        raise ValueError(f"No firmware file references added: firmware-id {firmware.id} {len(firmware_file_list)}")


def reconcile_extracted_firmware_files(firmware=None):
    """
    Scans firmware files on disk for imported firmwares and reconciles the
    database records so that is_on_disk and absolute_store_path match actual disk state.
    """
    from model.AndroidFirmware import AndroidFirmware
    from pymongo import UpdateOne

    firmwares = [firmware] if firmware else AndroidFirmware.objects()
    total_updated = 0

    for fw in firmwares:
        try:
            store_setting = fw.get_store_setting()
            if not store_setting:
                continue
            store_paths = store_setting.get_store_paths()
            file_extract_base = store_paths.get("FIRMWARE_FOLDER_FILE_EXTRACT")
            if not file_extract_base or not os.path.isdir(file_extract_base):
                continue

            extract_base = os.path.join(file_extract_base, "firmware_extract", fw.md5)
            export_base = os.path.join(file_extract_base, "firmware_file_export", str(fw.id))

            has_extract = os.path.isdir(extract_base)
            has_export = os.path.isdir(export_base)
            if not has_extract and not has_export:
                continue

            files = FirmwareFile.objects(firmware_id_reference=fw.id)
            bulk_ops = []
            for f in files:
                rel = f.relative_path.lstrip("/")
                candidates = []
                if has_extract:
                    if f.partition_name in ["/", "root", "archive", None]:
                        candidates.append(os.path.join(extract_base, "intermediate_extractions", rel))
                    else:
                        candidates.append(os.path.join(extract_base, f.partition_name, rel))
                if has_export:
                    candidates.append(os.path.join(export_base, f.partition_name or "root", rel))

                matched_path = None
                for cand in candidates:
                    if os.path.exists(cand):
                        matched_path = os.path.realpath(cand)
                        break

                if matched_path:
                    if not f.is_on_disk or f.absolute_store_path != matched_path:
                        bulk_ops.append(
                            UpdateOne(
                                {"_id": f.id},
                                {
                                    "$set": {
                                        "is_on_disk": True,
                                        "absolute_store_path": matched_path,
                                    }
                                }
                            )
                        )
                        total_updated += 1
                        if len(bulk_ops) >= 1000:
                            FirmwareFile._get_collection().bulk_write(bulk_ops, ordered=False)
                            bulk_ops = []
            if bulk_ops:
                FirmwareFile._get_collection().bulk_write(bulk_ops, ordered=False)
        except Exception as err:
            logging.error(f"Error during reconcile_extracted_firmware_files for firmware {getattr(fw, 'id', None)}: {err}")

    logging.info(f"reconcile_extracted_firmware_files completed. Total files updated: {total_updated}")
    return total_updated
