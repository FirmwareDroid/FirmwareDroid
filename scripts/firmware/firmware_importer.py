import re
import tempfile
import threading
import flask
import logging
import os
import shutil

from scripts.firmware.image_importer import create_abs_image_file_path, find_image_firmware_file, extract_image_files
from scripts.hashing.fuzzy_hash_creator import fuzzy_hash_firmware_files
from model import AndroidFirmware
from threading import Thread
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.firmware.firmware_file_indexer import create_firmware_file_list, add_firmware_file_references
from scripts.firmware.const_regex import BUILD_PROP_PATTERN_LIST, EXT_IMAGE_PATTERNS_DICT
from scripts.firmware.android_app_import import store_android_apps
from scripts.firmware.build_prop_parser import BuildPropParser
from scripts.hashing.file_hashs import md5_from_file, sha1_from_file, sha256_from_file
from scripts.extractor.expand_archives import extract_all_nested
from scripts.utils.file_utils.file_util import get_filenames, create_directories
from scripts.firmware.firmware_version_detect import detect_by_build_prop
from scripts.utils.mulitprocessing_util.mp_util import create_multi_threading_queue

lock = threading.Lock()


def start_firmware_mass_import():
    """
    Imports all .zip files from the import folder.
    :return: list of string with the status (errors/success) of every file.
    """
    create_app_context()
    app = flask.current_app
    logging.info("FIRMWARE MASS IMPORT STARTED!")
    num_threads = int(app.config["MASS_IMPORT_NUMBER_OF_THREADS"])
    firmware_file_queue = create_queue()
    worker_list = []
    for i in range(num_threads):
        worker = Thread(target=prepare_firmware_import, args=(firmware_file_queue,))
        worker.setDaemon(True)
        worker.start()
        worker_list.append(worker)
    firmware_file_queue.join()


def create_queue():
    """
    Create a queue of firmware files from the import folder.
    :return: A queue.
    """
    firmware_import_folder_path = flask.current_app.config["FIRMWARE_FOLDER_IMPORT"]
    filename_list = get_filenames(firmware_import_folder_path)
    filename_list = filter(lambda x: x.endswith(".zip") or x.endswith(".tar") or x.endswith(".tar.md5"), filename_list)
    if not filename_list:
        raise ValueError("No .zip files in import folder!")
    return create_multi_threading_queue(filename_list)


def prepare_firmware_import(firmware_file_queue):
    """
    An multi-threaded import script that extracts meta information of a firmware file from the system.img.
    Stores a firmware into the database if it is not already stored.
    :param firmware_file_queue: The queue of files to import.
    :return: A dict of the errors and success messages for every file.
    """
    create_app_context()
    app = flask.current_app
    while True:
        filename = firmware_file_queue.get()
        logging.info(f"Attempt to import: {str(filename)}")
        try:
            firmware_file_path = os.path.join(app.config["FIRMWARE_FOLDER_IMPORT"], filename)
            md5 = md5_from_file(firmware_file_path)
            if not AndroidFirmware.objects(md5=md5) or (AndroidFirmware.objects(md5=md5) is not None):
                import_firmware(filename, md5, firmware_file_path)
            else:
                raise ValueError(f"Skipped file - Already in database. {str(filename)}")
        except Exception as err:
            logging.error(str(err))
        firmware_file_queue.task_done()


def import_firmware(original_filename, md5, firmware_archive_file_path):
    """
    Attempts to store a firmware archive into the database.
    :param original_filename: str - name of the file to import.
    :param md5: md5 - checksum of the file to check.
    :param firmware_archive_file_path: str - path of the firmware archive.
    """
    temp_extract_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"],
                                                   suffix="_extract")
    version_detected = 0
    build_prop = None
    firmware_app_list = []
    firmware_file_list = []
    try:
        sha1 = sha1_from_file(firmware_archive_file_path)
        sha256 = sha256_from_file(firmware_archive_file_path)
        file_size = os.path.getsize(firmware_archive_file_path)
        extract_all_nested(firmware_archive_file_path, temp_extract_dir.name, False)
        archive_firmware_file_list = get_firmware_archive_content(temp_extract_dir.name)
        firmware_file_list.extend(archive_firmware_file_list)
        for partition_name, file_pattern_list in EXT_IMAGE_PATTERNS_DICT.items():
            temp_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"],
                                                   suffix=f"_mount_{partition_name}")
            partition_firmware_file_list = get_partition_firmware_files(archive_firmware_file_list,
                                                                        temp_extract_dir.name,
                                                                        file_pattern_list,
                                                                        partition_name,
                                                                        temp_dir.name)
            firmware_file_list.extend(partition_firmware_file_list)

            firmware_app_store = os.path.join(flask.current_app.config["FIRMWARE_FOLDER_APP_EXTRACT"],
                                              md5,
                                              partition_name)
            if partition_name == "system":  # Todo remove this statement as soon as build_prop_parser is refactored
                firmware_app_list.extend(store_android_apps(temp_dir.name, firmware_app_store, firmware_file_list))
                build_prop = extract_build_prop(temp_dir.name)
                version_detected = detect_by_build_prop(build_prop)
            else:
                try:
                    firmware_app_list.extend(store_android_apps(temp_dir.name, firmware_app_store, firmware_file_list))
                except ValueError as err:
                    logging.warning(err)
            fuzzy_hash_firmware_files(partition_firmware_file_list, temp_dir.name)

        filename, file_extension = os.path.splitext(firmware_archive_file_path)
        store_filename = md5 + file_extension
        firmware_archive_store_path = os.path.join(flask.current_app.config["FIRMWARE_FOLDER_STORE"],
                                                   version_detected,
                                                   store_filename)
        create_directories(firmware_archive_store_path)
        shutil.move(firmware_archive_file_path, firmware_archive_store_path)
        store_firmware_object(store_filename=store_filename,
                              original_filename=original_filename,
                              firmware_store_path=firmware_archive_store_path,
                              md5=md5,
                              sha256=sha256,
                              sha1=sha1,
                              android_app_list=firmware_app_list,
                              file_size=file_size,
                              build_prop=build_prop,
                              version_detected=version_detected,
                              firmware_file_list=firmware_file_list)
        logging.info(f"Firmware Import success: {original_filename}")
    except Exception as e:
        logging.exception(f"Firmware Import failed: {original_filename} error: {str(e)}")
        if firmware_file_list and len(firmware_file_list) > 0:
            for firmware_file in firmware_file_list:
                firmware_file.delete()
        if firmware_app_list and len(firmware_app_list) > 0:
            for android_app in firmware_app_list:
                android_app.delete()
        shutil.move(firmware_archive_file_path, flask.current_app.config["FIRMWARE_FOLDER_IMPORT_FAILED"])


def get_firmware_archive_content(cache_temp_file_dir_path):
    """
    Creates an index of the files within the firmware and attempts to find the system.img
    :param cache_temp_file_dir_path: str - dir path in which the extracted files are.

    :return: list class:'FirmwareFile'
    """
    firmware_files = []
    top_level_firmware_files = create_firmware_file_list(cache_temp_file_dir_path, "/")
    firmware_files.extend(top_level_firmware_files)
    return firmware_files


def get_partition_firmware_files(archive_firmware_file_list,
                                 extracted_archive_dir_path,
                                 file_pattern_list,
                                 partition_name,
                                 temp_dir_path):
    """
    Index all ext files of the given firmware. Creates a list of class:'FirmwareFile' from an Android all
    accessible partitions.
    :param file_pattern_list: list(str) - list of regex patterns to detect an image file by name.
    :param temp_dir_path: str - path to the directoy in which the image files will be loaded temporarily.
    :param partition_name: str - unique identifier of the partition.
    :param extracted_archive_dir_path: str - path of the root folder where the firmware archive was extracted to.
    :param archive_firmware_file_list: list(class:'FirmwareFile') - list of top level firmware files from the archive.
    :raises: RuntimeError - in case the system partition cannot be accessed.
    :return: list(class:'FirmwareFile') - list of files found in the image. In case the image could not be processed the
    method returns an empty list.
    """
    firmware_file_list = []
    try:
        image_firmware_file = find_image_firmware_file(archive_firmware_file_list, file_pattern_list)
        image_absolute_path = create_abs_image_file_path(image_firmware_file, extracted_archive_dir_path)
        extract_image_files(image_absolute_path, temp_dir_path)
        partition_firmware_files = create_firmware_file_list(temp_dir_path, partition_name)
        firmware_file_list.extend(partition_firmware_files)
    except (RuntimeError, ValueError) as err:
        if partition_name == "system":  # Abort if we cannot import system partition.
            raise
        else:
            logging.warning(err)
    return firmware_file_list


def store_firmware_object(store_filename, original_filename, firmware_store_path, md5, sha256, sha1, android_app_list,
                          file_size, build_prop, version_detected, firmware_file_list):
    """
    Creates class:'AndroidFirmware' object and saves it to the database. Creates references to other documents.
    :param version_detected: str - detected version of the firmware.
    :param store_filename: str - Name of the file within the file store.
    :param original_filename: str - original filename before renaming.
    :param firmware_store_path: str - relative path within the filesystem
    :param md5: str - checksum
    :param sha256: str - checksum
    :param sha1: str - checksum
    :param android_app_list: list of class:'AndroidApp'
    :param file_size: int - size of firmware file.
    :param build_prop: class:'BuildPropFile'
    :param firmware_file_list: list of class:'FirmwareFile'
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
                               hasFuzzyHashIndex=True,
                               build_prop=build_prop)
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


def extract_build_prop(source_path):
    """
    Extracts the build.prop file from the given directory and creates an parsed it's content.
    :param source_path: str - path of the directory to search through.
    :return: class:'BuildPropFile'
    """
    build_prop_file_path = find_build_prop_path(source_path)
    build_prop_parser = BuildPropParser(build_prop_file_path)
    build_prop = build_prop_parser.create_build_prop_document()
    return build_prop


def find_build_prop_path(search_path):
    """
    Returns a build.prop file if found within the given path.
    :param search_path: The path in which the file will be searched.
    :return: class:Path to the build.prop file.
    """
    for root, dirs, files in os.walk(search_path):
        for filename in files:
            for pattern in BUILD_PROP_PATTERN_LIST:
                if re.search(pattern, filename.lower()):
                    path = os.path.join(root, filename)
                    logging.info("Build.prop file path: " + str(path))
                    return path
    raise ValueError("Could not find build.prop file in image.")
