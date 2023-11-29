# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import re
import tempfile
import threading
import logging
import os
import shutil
from pathlib import Path

from model import AndroidFirmware, FirmwareFile, AndroidApp
from threading import Thread
from firmware_handler.image_importer import create_abs_image_file_path, find_image_firmware_file, extract_image_files
from hashing.fuzzy_hash_creator import fuzzy_hash_firmware_files
from context.context_creator import create_db_context
from firmware_handler.firmware_file_indexer import create_firmware_file_list, add_firmware_file_references
from firmware_handler.const_regex_patterns import BUILD_PROP_PATTERN_LIST, EXT_IMAGE_PATTERNS_DICT
from firmware_handler.android_app_import import store_android_apps
from firmware_handler.build_prop_parser import BuildPropParser
from hashing.standard_hash_generator import md5_from_file, sha1_from_file, sha256_from_file
from extractor.expand_archives import extract_archive_layer
from setup.default_setup import get_active_file_store_paths
from utils.file_utils.file_util import get_filenames
from firmware_handler.firmware_version_detect import detect_by_build_prop
from utils.mulitprocessing_util.mp_util import create_multi_threading_queue
from bson import ObjectId

ALLOWED_ARCHIVE_FILE_EXTENSIONS = [".zip", ".tar"]
STORE_PATHS = get_active_file_store_paths()
lock = threading.Lock()


def start_firmware_mass_import(create_fuzzy_hashes):
    """
    Imports all .zip files from the import folder.

    :param create_fuzzy_hashes: bool - true if fuzzy hash index should be created.

    :return: list of string with the status (errors/success) of every file.
    """
    logging.info("FIRMWARE MASS IMPORT STARTED!")
    firmware_archives_queue = create_file_import_queue()
    num_threads = 5
    worker_list = []
    for i in range(num_threads):
        logging.info(f"Start importer thread {i}")
        worker = Thread(target=prepare_firmware_import, args=(firmware_archives_queue, create_fuzzy_hashes))
        worker.setDaemon(True)
        worker.start()
        worker_list.append(worker)
    firmware_archives_queue.join()


def create_file_import_queue():
    """
    Create a queue of firmware files from the import folder.

    :return: multi threading queue object containing the paths to the firmware archives to import.
    """
    firmware_import_folder_path = STORE_PATHS["FIRMWARE_FOLDER_IMPORT"]
    filename_list = get_filenames(firmware_import_folder_path)
    filename_list = list(filter(lambda x: x.endswith(".zip") or x.endswith(".tar"), filename_list))
    logging.info(f"{len(filename_list)} files to import from {firmware_import_folder_path}:"
                 f"\n\n{''.join(map(str, filename_list))}")
    if len(filename_list) == 0:
        logging.error(f"No files to import ({len(filename_list)} from {firmware_import_folder_path}")
        raise ValueError("No files in import folder!")
    file_queue = create_multi_threading_queue(filename_list)
    logging.info(
        f"Approximate number of files to import ({len(filename_list)} {file_queue.qsize()}) "
        f"from {firmware_import_folder_path}")
    return file_queue


def allow_import(firmware_file_path, md5):
    """
    Checks if the pre-conditions for an import are met.

    :return: (boolean, str) - True if pre-conditions are met. In case of false a string with the reason is returned.
    """
    reason = ""
    is_allowed = True
    _, file_extension = os.path.splitext(firmware_file_path)

    if file_extension not in ALLOWED_ARCHIVE_FILE_EXTENSIONS:
        is_allowed = False
        reason = "File extension of root archive is not supported."

    if AndroidFirmware.objects(md5=md5) or (AndroidFirmware.objects(md5=md5) is None):
        is_allowed = False
        reason = "Skipped file - Already in database. {str(filename)}"

    return is_allowed, reason


@create_db_context
def prepare_firmware_import(firmware_file_queue, create_fuzzy_hashes):
    """
    An multi-threaded import script that extracts meta information of a firmware file from the system.img.
    Stores a firmware into the database if it is not already stored.

    :param create_fuzzy_hashes: bool - true if fuzzy hash index should be created.
    :param firmware_file_queue: The queue of files to import.

    :return: A dict of the errors and success messages for every file.

    """
    while True:
        filename = firmware_file_queue.get()
        logging.info(f"Attempt to import: {str(filename)}")
        try:
            firmware_file_path = os.path.join(STORE_PATHS["FIRMWARE_FOLDER_IMPORT"], filename)
            md5 = md5_from_file(firmware_file_path)
            is_allowed, reason = allow_import(firmware_file_path, md5)
            if is_allowed:
                import_firmware(filename, md5, firmware_file_path, create_fuzzy_hashes)
            else:
                raise ValueError(reason)
        except Exception as err:
            logging.error(str(err))
        firmware_file_queue.task_done()


def open_firmware(firmware_archive_file_path, temp_extract_dir):
    """
    Extracts a firmware to the given folder.

    :param firmware_archive_file_path: str - path to the firmware to extract.
    :param temp_extract_dir: str - destination folder to extract the firmware to.

    :return: list(class:FirmwareFile)

    """
    extract_archive_layer(firmware_archive_file_path, temp_extract_dir, False)
    archive_firmware_file_list = get_firmware_archive_content(temp_extract_dir)
    return archive_firmware_file_list


def get_partition_firmware_files(archive_firmware_file_list,
                                 temp_extract_dir,
                                 partition_name,
                                 file_pattern_list,
                                 partition_temp_dir):
    """
    Creates a list of firmware files from known file partitions.

    :param partition_temp_dir:
    :param partition_name:
    :param file_pattern_list:
    :param archive_firmware_file_list: list(class:FirmwareFile) - list of firmware archive firmware files.
    :param temp_extract_dir: tempfile.TemporaryDirectory - directory where the firmware archive was extracted to.

    :return: list(class:FirmwareFile) - list of found partition firmware files.
    """
    firmware_file_list = []
    partition_firmware_file_list = create_partition_file_index(partition_name,
                                                               file_pattern_list,
                                                               archive_firmware_file_list,
                                                               temp_extract_dir,
                                                               partition_temp_dir)
    firmware_file_list.extend(partition_firmware_file_list)
    return firmware_file_list


def create_partition_file_index(partition_name, file_pattern_list, archive_firmware_file_list,
                                temp_extract_dir, partition_temp_dir):
    """
    Gets a list of all files found in a specific partition.

    :param partition_name: str - name of the partition.
    :param file_pattern_list: list(str) - a list of known name patterns for partitions.
    :param archive_firmware_file_list: list(class:'FirmwareFile') - a list of the root elements found in the
    firmware archive.
    :param temp_extract_dir: str - path to the extraction directory.
    :param partition_temp_dir: str - path where the partition is read from.

    :return: list(class:'FirmwareFile') - with all found firmware files within a particular partition.
    """
    partition_firmware_file_list = create_partition_firmware_files(archive_firmware_file_list,
                                                                   temp_extract_dir,
                                                                   file_pattern_list,
                                                                   partition_name,
                                                                   partition_temp_dir)
    return partition_firmware_file_list


def index_partitions(temp_extract_dir, files_dict, create_fuzzy_hashes, md5):
    """
    Creates for every readable partition an index of all files. Special files (apk, build_properties, etc.)
    are indexed in a separated lists for further processing.

    :param temp_extract_dir: str - path to the directory where the files have been extracted.
    :param files_dict: dict - containing the different file lists.
    :param create_fuzzy_hashes: boolean - create fuzzy hashes index.
    :param md5: str - md5 hash of the firmware

    :return: dict - extentions of the original dict with all newly found files.
    """
    for partition_name, file_pattern_list in EXT_IMAGE_PATTERNS_DICT.items():
        with tempfile.TemporaryDirectory(dir=STORE_PATHS["FIRMWARE_FOLDER_CACHE"],
                                         suffix=f"_mount_{partition_name}") as partition_temp_dir:
            partition_firmware_file_list = create_partition_file_index(partition_name,
                                                                       file_pattern_list,
                                                                       files_dict["archive_firmware_file_list"],
                                                                       temp_extract_dir,
                                                                       partition_temp_dir)
            files_dict["firmware_file_list"].extend(partition_firmware_file_list)
            firmware_app_store = os.path.join(STORE_PATHS["FIRMWARE_FOLDER_APP_EXTRACT"],
                                              md5,
                                              partition_name)
            try:
                files_dict["firmware_app_list"].extend(store_android_apps(partition_temp_dir, firmware_app_store,
                                                                          files_dict["firmware_file_list"]))
            except ValueError:
                pass
            files_dict["build_prop_file_list"].extend(
                extract_build_prop(partition_firmware_file_list, partition_temp_dir))
            if create_fuzzy_hashes:
                fuzzy_hash_firmware_files(partition_firmware_file_list, partition_temp_dir)
    return files_dict


def store_firmware_archive(firmware_archive_file_path, md5, version_detected):
    """
    Renames and moves the firmware archive to the permanent storage.

    :param firmware_archive_file_path: str - path to the firmware archive.
    :param md5: str - md5 hash of the firmware archive.
    :param version_detected: str - version of the firmware if known.

    :return: str, str - name of the firmware within the permanent storage and path to the storage.
    """
    _, file_extension = os.path.splitext(firmware_archive_file_path)
    store_filename = md5 + file_extension
    firmware_archive_store_path = Path(os.path.join(STORE_PATHS["FIRMWARE_FOLDER_STORE"],
                                                    version_detected,
                                                    md5))
    if not firmware_archive_store_path.exists():
        firmware_archive_store_path.mkdir(parents=True, exist_ok=True)

    if firmware_archive_store_path.exists():
        firmware_store_path = Path(os.path.join(firmware_archive_store_path.absolute().as_posix(), store_filename))
        shutil.copy(firmware_archive_file_path, firmware_store_path.absolute().as_posix())
        if firmware_store_path.exists():
            os.remove(firmware_archive_file_path)
        else:
            raise OSError(f"Could not copy firmware archive to destination folder: "
                          f"{firmware_store_path.absolute().as_posix()}")
    else:
        raise OSError(f"Firmware store directory could not be created: "
                      f"{firmware_archive_store_path.absolute().as_posix()}")

    return store_filename, firmware_store_path.absolute().as_posix()


def import_firmware(original_filename, md5, firmware_archive_file_path, create_fuzzy_hashes):
    """
    Attempts to store a firmware archive into the database.

    :param create_fuzzy_hashes: boolean - create a fuzzy hash index for all files in the firmware.
    :param original_filename: str - name of the file to import.
    :param md5: md5 - checksum of the file to check.
    :param firmware_archive_file_path: str - path of the firmware archive.

    """
    with tempfile.TemporaryDirectory(dir=STORE_PATHS["FIRMWARE_FOLDER_CACHE"],
                                     suffix="_extract") as temp_extract_dir:
        files_dict = {
            "firmware_app_list": [],
            "build_prop_file_list": [],
            "firmware_file_list": [],
            "archive_firmware_file_list": []
        }
        try:
            sha1 = sha1_from_file(firmware_archive_file_path)
            sha256 = sha256_from_file(firmware_archive_file_path)
            file_size = os.path.getsize(firmware_archive_file_path)

            archive_firmware_file_list = open_firmware(firmware_archive_file_path, temp_extract_dir)
            files_dict["archive_firmware_file_list"].extend(archive_firmware_file_list)
            files_dict["firmware_file_list"].extend(archive_firmware_file_list)
            files_dict = index_partitions(temp_extract_dir, files_dict, create_fuzzy_hashes, md5)

            version_detected = detect_by_build_prop(files_dict["build_prop_file_list"])
            store_filename, firmware_store_path = store_firmware_archive(firmware_archive_file_path, md5,
                                                                         version_detected)

            store_firmware_object(store_filename=store_filename,
                                  original_filename=original_filename,
                                  firmware_store_path=firmware_store_path,
                                  md5=md5,
                                  sha256=sha256,
                                  sha1=sha1,
                                  android_app_list=files_dict["firmware_app_list"],
                                  file_size=file_size,
                                  build_prop_file_id_list=files_dict["build_prop_file_list"],
                                  version_detected=version_detected,
                                  firmware_file_list=files_dict["firmware_file_list"],
                                  has_fuzzy_hash_index=create_fuzzy_hashes)
            logging.info(f"Firmware Import success: {original_filename}")
        except Exception as error:
            logging.exception(f"Firmware Import failed: {original_filename} error: {str(error)}")

            if files_dict["firmware_file_list"] and len(files_dict["firmware_file_list"]) > 0:
                firmware_file_id_object_list = []
                for firmware_file in files_dict["firmware_file_list"]:
                    firmware_file_id_object_list.append(ObjectId(firmware_file.id))
                FirmwareFile.objects(pk__in=firmware_file_id_object_list).delete()
                logging.info("Cleanup: Removed firmware-files from DB")

            if files_dict["firmware_app_list"] and len(files_dict["firmware_app_list"]) > 0:
                android_app_id_object_list = []
                for android_app in files_dict["firmware_app_list"]:
                    android_app_id_object_list.append(ObjectId(android_app.id))
                AndroidApp.objects(pk__in=android_app_id_object_list).delete()
                logging.info("Cleanup: Removed android apps from DB")

            shutil.move(firmware_archive_file_path, STORE_PATHS["FIRMWARE_FOLDER_IMPORT_FAILED"])
            logging.info(f"Cleanup: Firmware file moved to failed folder: {original_filename}")


def get_firmware_archive_content(cache_temp_file_dir_path):
    """
    Creates an index of the files within the firmware.

    :param cache_temp_file_dir_path: str - dir path in which the extracted files are.

    :return: list class:'FirmwareFile'
    """
    firmware_files = []
    top_level_firmware_files = create_firmware_file_list(cache_temp_file_dir_path, "/")
    firmware_files.extend(top_level_firmware_files)
    return firmware_files


def create_partition_firmware_files(archive_firmware_file_list,
                                    extracted_archive_dir_path,
                                    file_pattern_list,
                                    partition_name,
                                    temp_dir_path):
    """
    Index all ext files of the given firmware. Creates a list of class:'FirmwareFile' from an accessible partition.

    :param file_pattern_list: list(str) - list of regex patterns to detect an image file by name.
    :param temp_dir_path: str - path to the directory in which the image files will be loaded temporarily.
    :param partition_name: str - unique identifier of the partition.
    :param extracted_archive_dir_path: str - path of the root folder where the firmware archive was extracted to.
    :param archive_firmware_file_list: list(class:'FirmwareFile') - list of top level firmware files from the archive.
    :raises: RuntimeError - in case the system partition cannot be accessed.

    :return: list(class:'FirmwareFile') - list of files found in the image. In case the image could not be processed the
    method returns an empty list.
    """
    firmware_file_list = []
    try:
        partition_folder = os.path.join(extracted_archive_dir_path, partition_name)
        if os.path.exists(partition_folder) and os.path.isdir(partition_folder) and any(os.scandir(partition_folder)):
            shutil.move(partition_folder, temp_dir_path)
        else:
            image_firmware_file = find_image_firmware_file(archive_firmware_file_list, file_pattern_list)
            image_absolute_path = create_abs_image_file_path(image_firmware_file, extracted_archive_dir_path)
            extract_image_files(image_absolute_path, temp_dir_path)
        partition_firmware_files = create_firmware_file_list(temp_dir_path, partition_name)
        firmware_file_list.extend(partition_firmware_files)
    except (RuntimeError, ValueError) as err:
        if partition_name != "system":
            logging.warning(err)
        else:  # Abort import if we cannot import system partition.
            raise
    return firmware_file_list


def store_firmware_object(store_filename, original_filename, firmware_store_path, md5, sha256, sha1, android_app_list,
                          file_size, build_prop_file_id_list, version_detected, firmware_file_list,
                          has_fuzzy_hash_index):
    """
    Creates class:'AndroidFirmware' object and saves it to the database. Creates references to other documents.

    :param has_fuzzy_hash_index: bool - true if fuzzy hash index was created. False if fuzzy hash index was not created.
    :param version_detected: str - detected version of the firmware.
    :param store_filename: str - Name of the file within the file store.
    :param original_filename: str - original filename before renaming.
    :param firmware_store_path: str - relative path within the filesystem
    :param md5: str - checksum
    :param sha256: str - checksum
    :param sha1: str - checksum
    :param android_app_list: list of class:'AndroidApp'
    :param file_size: int - size of firmware file.
    :param build_prop_file_id_list: list(class:'BuildPropFile')
    :param firmware_file_list: list(class:'FirmwareFile')

    :return: class:'AndroidFirmware'
    """
    absolute_store_path = os.path.abspath(firmware_store_path)
    logging.info(f"firmware_store_path: {firmware_store_path} absolute_store_path: {absolute_store_path}")
    firmware = AndroidFirmware(filename=store_filename,
                               original_filename=original_filename,
                               relative_store_path=firmware_store_path,
                               absolute_store_path=absolute_store_path,
                               md5=md5,
                               sha256=sha256,
                               sha1=sha1,
                               android_app_id_list=map(lambda x: x.id, android_app_list),
                               file_size_bytes=file_size,
                               version_detected=version_detected,
                               hasFileIndex=True,
                               hasFuzzyHashIndex=has_fuzzy_hash_index,
                               build_prop_file_id_list=build_prop_file_id_list)
    firmware.save()
    logging.info(f"Stored firmware with id {str(firmware.id)} in database.")
    add_firmware_file_references(firmware, firmware_file_list)
    add_app_firmware_references(firmware, android_app_list)
    return firmware


def add_app_firmware_references(firmware, android_app_list):
    """
    Adds the firmware reference to the app.

    :param firmware: class:'AndroidFirmware'
    :param android_app_list: list - class:'AndroidApp'

    """
    for app in android_app_list:
        app.firmware_id_reference = firmware.id
        app.save()


def extract_build_prop(firmware_file_list, mount_path):
    """
    Extracts the build.prop file from the given directory and creates an parsed it's content.

    :param mount_path: str - path where the firmware image is mounted to.
    :param firmware_file_list: list(class:'FirmwareFile') - list of firmware-files that contains a
    minimum of one build.prop file

    :return: list(class:'BuildPropFile') - list of BuildPropFile documents.
    """
    build_prop_firmware_file_list = find_build_prop_file_paths(firmware_file_list)
    build_prop_file_list = []
    for firmware_file in build_prop_firmware_file_list:
        try:
            firmware_file.absolute_store_path = os.path.join(mount_path, "." + firmware_file.absolute_store_path)
            build_prop_parser = BuildPropParser(firmware_file)
            build_prop_file = build_prop_parser.create_build_prop_document()
            build_prop_file_list.append(build_prop_file)
        except FileNotFoundError:
            pass
    return build_prop_file_list


def find_build_prop_file_paths(firmware_file_list):
    """
    Returns a build.prop file if found within the given path.

    :param firmware_file_list: list(class:FirmwareFile)

    :return: list(class:FirmwareFile) - list of build.prop firmware files.
    """
    build_prop_firmware_file_list = []
    for firmware_file in firmware_file_list:
        for pattern in BUILD_PROP_PATTERN_LIST:
            if re.search(pattern, firmware_file.name.lower()):
                build_prop_firmware_file_list.append(firmware_file)
    return build_prop_firmware_file_list
