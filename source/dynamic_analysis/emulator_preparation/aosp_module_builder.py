# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
"""
This script creates Android.mk and Android.bp file for an Android app that can be used in the build process of an
Android image.
"""
import os
import shutil
import tempfile
import logging
import traceback
import uuid
from context.context_creator import create_db_context, create_log_context
from dynamic_analysis.emulator_preparation.aosp_apk_module_builer import create_build_files_for_apps, \
    process_android_apps
from dynamic_analysis.emulator_preparation.aosp_framework_builder import process_framework_files
from dynamic_analysis.emulator_preparation.aosp_shared_library_builder import process_shared_libraries
from model import AndroidFirmware
from model.StoreSetting import get_active_store_paths_by_uuid
from utils.mulitprocessing_util.mp_util import start_process_pool


@create_db_context
@create_log_context
def start_aosp_module_file_creator(format_name, firmware_id_list, skip_file_export=False):
    worker_arguments = [format_name, skip_file_export]
    number_of_processes = len(firmware_id_list) if len(firmware_id_list) < os.cpu_count() else os.cpu_count()
    logging.info(f"Starting module build creator: format {format_name} with {len(firmware_id_list)} samples. "
                 f"Number of processes: {number_of_processes}")
    start_process_pool(firmware_id_list,
                       worker_process_firmware_multiprocessing,
                       number_of_processes=number_of_processes,
                       create_id_list=False,
                       worker_args_dict=worker_arguments)


@create_db_context
@create_log_context
def worker_process_firmware_multiprocessing(firmware_id_queue, format_name, skip_file_export):
    """
    Worker process for creating build files for a given firmware.

    :param firmware_id_queue: mp.Queue - Queue of firmware ids to process.
    :param format_name: str - 'mk' or 'bp' file format.
    :param skip_file_export: bool - flag to skip the file export.

    """
    logging.info(f"Worker process for format {format_name} started...")
    try:
        firmware_id = firmware_id_queue.get(timeout=.5)
        logging.info(f"Processing firmware {firmware_id}; Format: {format_name}...")
        try:
            firmware = AndroidFirmware.objects.get(pk=firmware_id)
            if firmware.aecs_build_file_path:
                remove_existing_aecs_archive(firmware.aecs_build_file_path)
            process_firmware(format_name, firmware, skip_file_export)
        except Exception as err:
            traceback.print_exc()
            logging.error(f"Could not process firmware {firmware_id}: {err}")
        firmware_id_queue.task_done()
    except Exception as err:
        logging.warning(f"Worker process: {err}")
    logging.info(f"Worker process finished...")


def remove_existing_aecs_archive(aecs_build_file_path):
    try:
        os.remove(aecs_build_file_path)
        logging.debug(f"Deleted existing build files for firmware {aecs_build_file_path}")
    except FileNotFoundError as err:
        logging.debug(f"No existing build files found for firmware {aecs_build_file_path}")


def process_firmware(format_name, firmware, skip_file_export):
    """
    Creates for every given Android app a AOSP compatible module build file and stores it to the database. The process
    support mk and bp file formats.

    :param format_name: str - 'mk' or 'bp' file format.
    :param firmware: class:'AndroidFirmware' - A list of class:'AndroidFirmware'
    :param skip_file_export: bool - flag to skip the file export.

    :return: list - A list of failed firmware that could not be processed.

    """
    is_successfully_created = create_build_files_for_firmware(firmware, format_name, skip_file_export)
    if not is_successfully_created:
        raise RuntimeError(f"Could not create build files for firmware {firmware.id}")


def create_build_files_for_firmware(firmware, format_name, skip_file_export):
    """
    Creates build files for a given firmware.

    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.
    :param format_name: str - 'mk' or 'bp' file format.
    :param skip_file_export: bool - flag to skip the file export.

    :return: bool - True if build files were successfully created for all apps, False otherwise.

    """
    is_successfully_created = False
    if format_name:
        logging.debug(f"Creating build files for firmware {firmware.id}...")
        is_successfully_created = create_build_files_for_apps(firmware.android_app_id_list, format_name)
        package_build_files_for_firmware(firmware, format_name, skip_file_export)
    return is_successfully_created


def package_build_files_for_firmware(firmware, format_name, skip_file_export):
    """
    Packages the build files for a given firmware into a zip file.

    :param format_name: str - 'mk' or 'bp' file format.
    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.
    :param skip_file_export: bool - flag to skip the file export.

    """
    logging.info(f"Packaging build files for firmware {firmware.md5}...")
    store_setting = firmware.get_store_setting()
    store_paths = store_setting.get_store_paths()
    with tempfile.TemporaryDirectory(dir=store_paths["FIRMWARE_FOLDER_CACHE"]) as tmp_root_dir:
        process_android_apps(firmware, tmp_root_dir)
        process_shared_libraries(firmware, tmp_root_dir, store_setting.id, format_name, skip_file_export)
        process_framework_files(firmware, tmp_root_dir, store_setting.id, format_name, skip_file_export)
        package_files(firmware, tmp_root_dir, store_paths)


def package_files(firmware, tmp_root_dir, store_paths):
    """
    Packages the build files for a given firmware into a zip file and stores it in the aecs_build_file_path of the
    firmware.

    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.
    :param tmp_root_dir: tempfile.TemporaryDirectory - A temporary directory to store the build files.
    :param store_paths: dict - A dictionary with the store paths.

    """
    logging.info(f"Packaging build files for firmware {firmware.id}...")
    with tempfile.TemporaryDirectory(dir=store_paths["FIRMWARE_FOLDER_CACHE"]) as tmp_output_dir:
        package_filename = f"{uuid.uuid4()}"
        output_zip = os.path.join(tmp_output_dir, package_filename)
        zip_file_path = shutil.make_archive(base_name=output_zip,
                                            format='zip',
                                            root_dir=tmp_root_dir)
        try:
            storage_uuid = firmware.absolute_store_path.split("/")[5]
            store_paths = get_active_store_paths_by_uuid(storage_uuid)
            aecs_output_dir = os.path.join(store_paths["FIRMWARE_FOLDER_FILE_EXTRACT"], "aecs_build_files")
            if not os.path.exists(aecs_output_dir):
                os.mkdir(aecs_output_dir)
            shutil.move(zip_file_path, aecs_output_dir)
        except FileNotFoundError as err:
            raise RuntimeError(f"Could not move zip file to {aecs_output_dir}: {err}")

    firmware.aecs_build_file_path = os.path.abspath(os.path.join(aecs_output_dir, package_filename + ".zip"))
    firmware.save()


