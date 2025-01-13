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
from dynamic_analysis.emulator_preparation.aosp_apex_module_builder import process_apex_files
from dynamic_analysis.emulator_preparation.aosp_apk_module_builer import create_build_files_for_apps, \
    process_android_apps
from dynamic_analysis.emulator_preparation.aosp_file_exporter import export_files_by_regex
from dynamic_analysis.emulator_preparation.aosp_shared_library_builder import process_shared_libraries
from firmware_handler.firmware_file_exporter import NAME_EXPORT_FOLDER
from model import AndroidFirmware
from model.StoreSetting import get_active_store_paths_by_uuid
from processing.standalone_python_worker import start_mp_process_pool_executor


@create_db_context
@create_log_context
def start_aosp_module_file_creator(format_name, firmware_id_list, skip_file_export=False):
    worker_argument_list = [format_name, skip_file_export]
    number_of_processes = len(firmware_id_list) if len(firmware_id_list) < os.cpu_count() else os.cpu_count()
    logging.info(f"Starting module build creator: format {format_name} with {len(firmware_id_list)} samples. "
                 f"Number of processes: {number_of_processes}")
    start_mp_process_pool_executor(firmware_id_list,
                                   worker_process_firmware_multiprocessing,
                                   number_of_processes=number_of_processes,
                                   create_id_list=False,
                                   worker_args_list=worker_argument_list)


@create_db_context
@create_log_context
def worker_process_firmware_multiprocessing(firmware_id, format_name, skip_file_export):
    """
    Worker process for creating build files for a given firmware.

    :param firmware_id: str - class:'AndroidFirmware' - An id for an instance of AndroidFirmware.
    :param format_name: str - 'mk' or 'bp' file format.
    :param skip_file_export: bool - flag to skip the file export.

    """
    logging.info(f"Worker process for format {format_name} started...")
    try:
        firmware = AndroidFirmware.objects.get(pk=firmware_id)
        logging.info(f"Processing firmware {firmware_id}; Format: {format_name}...")
        if firmware.aecs_build_file_path:
            remove_existing_aecs_archive(firmware.aecs_build_file_path, firmware)
        create_build_files_for_firmware(firmware, format_name, skip_file_export)
    except Exception as err:
        traceback.print_exc()
        logging.error(f"Could not process firmware {firmware_id}: {err}")
        raise err
    logging.info(f"Worker process finished...")


def remove_existing_aecs_archive(aecs_build_file_path, firmware):
    try:
        os.remove(aecs_build_file_path)
        firmware.aecs_build_file_path = None
        firmware.save()
        logging.debug(f"Deleted existing build files for firmware {aecs_build_file_path}")
    except FileNotFoundError as err:
        logging.debug(f"No existing build files found for firmware {aecs_build_file_path}")


def create_build_files_for_firmware(firmware, format_name, skip_file_export):
    """
    Creates build files for a given firmware.

    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.
    :param format_name: str - 'mk' or 'bp' file format.
    :param skip_file_export: bool - flag to skip the file export.

    :return: bool - True if build files were successfully created for all apps, False otherwise.

    """
    if format_name:
        logging.debug(f"Creating build files for firmware {firmware.id}...")
        create_build_files_for_apps(firmware.android_app_id_list, format_name)
        package_build_files_for_firmware(firmware, format_name, skip_file_export)


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
        store_path_abs = os.path.abspath(store_paths["FIRMWARE_FOLDER_FILE_EXTRACT"])
        export_destination_path = os.path.join(store_path_abs,
                                               NAME_EXPORT_FOLDER,
                                               str(firmware.pk))
        if not skip_file_export:
            search_pattern = "^.*$"
            export_files_by_regex(firmware, store_setting.id, search_pattern)
        copy_partitions(export_destination_path, tmp_root_dir)
        process_android_apps(firmware, tmp_root_dir)
        process_shared_libraries(firmware, tmp_root_dir, store_setting.id, format_name)
        process_apex_files(firmware, tmp_root_dir, store_setting.id, format_name)
        package_files(firmware, tmp_root_dir, store_paths)


def copy_partitions(source_path, destination_path):
    """
    Copy the partitions from the source path to the destination path.

    :param source_path: str - path to the source folder.
    :param destination_path: str - path to the destination folder.

    """
    logging.info(f"Copying partitions from {source_path} to {destination_path}...")
    destination_subfolder_path = os.path.join(destination_path, "ALL_FILES/")
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source path {source_path} does not exist.")
    shutil.copytree(source_path, destination_subfolder_path,
                    symlinks=False,
                    ignore_dangling_symlinks=True)


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
