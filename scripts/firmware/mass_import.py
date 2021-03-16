import re
import threading
import flask
import logging
import os
import shutil

from scripts.firmware.system_partition_util import create_system_img_path
from scripts.hashing.fuzzy_hash_creator import hash_firmware_files
from model import AndroidFirmware
from threading import Thread
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.firmware.firmware_file_indexer import create_firmware_file_list, add_firmware_file_references
from scripts.firmware.const_regex import SYSTEM_IMG_PATTERN_LIST, BUILD_PROP_PATTERN_LIST
from scripts.firmware.android_app_import import find_android_apps, extract_android_apps
from scripts.firmware.build_prop_parser import BuildPropParser
from scripts.firmware.ext4_mount_util import exec_umount, is_path_mounted, mount_android_ext4_image
from scripts.hashing.file_hashs import md5_from_file, sha1_from_file, sha256_from_file
from scripts.extractor.expand_archives import extract_all_nested
from scripts.utils.file_utils.file_util import get_filenames, create_temp_directories, cleanup_directories
from scripts.extractor.ubi_extractor import extract_ubi_image
from scripts.firmware.firmware_version_detect import detect_by_build_prop
from scripts.utils.mulitprocessing_util.mp_util import create_multi_threading_queue

lock = threading.Lock()


def start_mass_import():
    """
    Imports all .zip files from the import folder.
    :return: list of string with the status (errors/success) of every file.
    """
    create_app_context()
    app = flask.current_app
    logging.info("MASS IMPORT STARTED!")
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


def import_firmware(original_filename, md5, firmware_file_path):
    """
    Attempts to store a firmware archive into the database.
    :param original_filename: str - name of the file to import.
    :param md5: md5 - checksum of the file to check.
    :param firmware_file_path: str - path of the firmware archive.
    """
    temp_extract_dir, temp_mount_dir, firmware_app_store, store_filename, firmware_store_path \
        = create_import_paths(md5, firmware_file_path)
    try:
        sha1 = sha1_from_file(firmware_file_path)
        sha256 = sha256_from_file(firmware_file_path)
        file_size = os.path.getsize(firmware_file_path)
        extract_all_nested(firmware_file_path, temp_extract_dir.name, False)
        firmware_files = get_firmware_content(temp_extract_dir.name, temp_mount_dir.name)
        firmware_app_list = store_android_apps(temp_mount_dir.name, firmware_app_store)
        build_prop = extract_build_prop(temp_mount_dir.name)
        version_detected = detect_by_build_prop(build_prop)
        firmware = store_firmware_object(store_filename=store_filename,
                                         original_filename=original_filename,
                                         firmware_store_path=firmware_store_path,
                                         md5=md5,
                                         sha256=sha256,
                                         sha1=sha1,
                                         firmware_app_list=firmware_app_list,
                                         file_size=file_size,
                                         build_prop=build_prop,
                                         version_detected=version_detected,
                                         firmware_file_list=firmware_files)
        hash_firmware_files(firmware, temp_mount_dir.name)
        shutil.move(firmware_file_path, firmware_store_path)
        logging.info(f"Firmware Import success: {original_filename}")
    except Exception as e:
        logging.exception(f"Firmware Import failed: {original_filename} error: {str(e)}")
        cleanup_directories(firmware_file_path, firmware_app_store)
    finally:
        if is_path_mounted(temp_mount_dir.name):
            exec_umount(temp_mount_dir.name)


def create_import_paths(md5, firmware_file_path):
    """
    Creates the paths and directories needed for importing a firmware.
    :param md5: str - md5 has used as filename for storing the file.
    :param firmware_file_path: str - path of the file to store.
    :return: dir - tempdir, dir -tempdir, str -path_apps, str - future_filename_firmware, str -firmware_store_path
    """
    app = flask.current_app
    temp_extract_dir, temp_mount_dir = create_temp_directories()
    firmware_app_store = os.path.join(app.config["FIRMWARE_FOLDER_APP_EXTRACT"], md5)
    filename, file_extension = os.path.splitext(firmware_file_path)
    store_filename = md5 + file_extension
    firmware_store_path = os.path.join(app.config["FIRMWARE_FOLDER_STORE"], store_filename)
    logging.info(f"firmware_store_path: {firmware_store_path}")
    if not temp_extract_dir \
            or not temp_mount_dir \
            or not firmware_app_store \
            or not store_filename \
            or not firmware_store_path:
        raise ValueError(f"Could not create import paths! "
                         f"firmware_app_store: {firmware_app_store}, "
                         f"store_filename: {store_filename},"
                         f"firmware_store_path: {firmware_store_path}")
    return temp_extract_dir, temp_mount_dir, firmware_app_store, store_filename, firmware_store_path


def get_firmware_content(cache_temp_file_dir_path, cache_temp_mount_dir_path):
    """
    Creates an index of the files within the firmware and attempts to find the system.img
    :param cache_temp_file_dir_path: str - dir path in which the extracted files are.
    :param cache_temp_mount_dir_path: str - dir path in which the system.img will be mounted.
    :return: list class:'FirmwareFile'
    """
    top_level_firmware_files = create_firmware_file_list(cache_temp_file_dir_path, "/")
    system_image = find_system_image(top_level_firmware_files)
    system_image_absolute_path = create_system_img_path(system_image, cache_temp_file_dir_path)
    if not mount_android_ext4_image(system_image_absolute_path, cache_temp_mount_dir_path):
        extract_ubi_image(system_image_absolute_path, cache_temp_mount_dir_path)
    second_level_firmware_files = create_firmware_file_list(cache_temp_mount_dir_path, "system")
    firmware_files = []
    firmware_files.extend(top_level_firmware_files)
    firmware_files.extend(second_level_firmware_files)
    return firmware_files


def store_android_apps(search_path, firmware_app_store):
    """
    Finds and stores all android .apk files.
    :param search_path: str - path to search for .apk files.
    :param firmware_app_store: str - path in which the .apk files will be stored.
    :return: list of class:'AndroidApp'
    """
    firmware_app_list = find_android_apps(search_path)
    extract_android_apps(firmware_app_list, firmware_app_store, search_path)
    return firmware_app_list


def store_firmware_object(store_filename, original_filename, firmware_store_path, md5, sha256, sha1, firmware_app_list,
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
    :param firmware_app_list: list of class:'AndroidApp'
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
                               android_app_id_list=map(lambda x: x.id, firmware_app_list),
                               file_size_bytes=file_size,
                               version_detected=version_detected,
                               hasFileIndex=True,
                               build_prop=build_prop)
    firmware.save()
    logging.info(f"Stored firmware with id {str(firmware.id)} in database.")
    add_firmware_file_references(firmware, firmware_file_list)
    add_app_firmware_references(firmware, firmware_app_list)
    return firmware


def add_app_firmware_references(firmware, app_list):
    """
    Adds the firmware reference to the app.
    :param firmware: class:'AndroidFirmware'
    :param app_list: list - class:'AndroidApp'
    """
    for app in app_list:
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


def find_system_image(firmware_files):
    """
    Checks within the given file list if there is a mountable system partition.
    :param firmware_files: The files which will be checked for their names.
    :return: class:'FirmwareFile' object of the system.img or system.ext4.img file.
    """
    for file in firmware_files:
        file_name = file.name.lower()
        for pattern in SYSTEM_IMG_PATTERN_LIST:
            if not file.isDirectory and re.search(pattern, file_name.lower()):
                logging.info("Found system image file: " + str(file.name))
                return file
    raise ValueError("Could not find system.img or system.ext4.img file!")
