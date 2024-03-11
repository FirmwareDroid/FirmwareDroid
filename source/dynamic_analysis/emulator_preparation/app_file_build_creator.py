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
from string import Template
from mongoengine import DoesNotExist
from context.context_creator import create_db_context
from model import GenericFile, AndroidFirmware
from model.StoreSetting import get_active_store_paths_by_uuid
from utils.mulitprocessing_util.mp_util import start_process_pool

ANDROID_MK_TEMPLATE = "LOCAL_PATH := $$(call my-dir)\n" \
                      "\ninclude $$(CLEAR_VARS)\n" \
                      "\nLOCAL_MODULE_TAGS := optional \n" \
                      "\nLOCAL_MODULE := ib_${local_module}\n" \
                      "\nLOCAL_CERTIFICATE := ${local_certificate}\n" \
                      "\nLOCAL_SRC_FILES := ${local_src_files}\n" \
                      "\nLOCAL_MODULE_CLASS := APPS\n" \
                      "\nLOCAL_MODULE_SUFFIX := $$(COMMON_ANDROID_PACKAGE_SUFFIX)\n" \
                      "\nLOCAL_OPTIONAL_USES_LIBRARIES := ${local_optional_uses_libraries}\n" \
                      "\ninclude $$(BUILD_PREBUILT)\n"

ANDROID_BP_TEMPLATE = ""


@create_db_context
def start_app_build_file_creator(format_name, firmware_id_list):
    worker_arguments = [format_name]
    logging.debug(f"Starting app build file creator for format {format_name}... with {len(firmware_id_list)} firmware.")
    start_process_pool(firmware_id_list,
                       worker_process_firmware,
                       number_of_processes=os.cpu_count(),
                       create_id_list=False,
                       worker_args_dict=worker_arguments)


@create_db_context
def worker_process_firmware(firmware_id_queue, format_name):
    """
    Worker process for creating build files for a given firmware.

    :param firmware_id_queue: mp.Queue - Queue of firmware ids to process.
    :param format_name: str - 'mk' or 'bp' file format.

    """
    logging.debug(f"Worker process for format {format_name} started...")
    while True:
        firmware_id = firmware_id_queue.get(timeout=.5)
        logging.debug(f"Processing firmware {firmware_id}; Format: {format_name}...")
        try:
            firmware_list = AndroidFirmware.objects(pk=firmware_id, aecs_build_file_path__exists=False)
            process_firmware(format_name, firmware_list)
        except Exception as err:
            traceback.print_exc()
            logging.error(f"Could not process firmware {firmware_id}: {err}")
        firmware_id_queue.task_done()


def process_firmware(format_name, firmware_list):
    """
    Creates for every given Android app a AOSP compatible module build file and stores it to the database. The process
    support mk and bp file formats.

    :param format_name: str - 'mk' or 'bp' file format.
    :param firmware_list: list(class:'AndroidFirmware') - A list of class:'AndroidFirmware'

    :return: list - A list of failed firmware that could not be processed.
    """
    for firmware in firmware_list:
        is_successfully_created = create_build_files_for_firmware(firmware, format_name)
        if not is_successfully_created:
            raise RuntimeError(f"Could not create build files for firmware {firmware.id}")


def create_build_files_for_firmware(firmware, format_name):
    """
    Creates build files for a given firmware.

    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.
    :param format_name: str - 'mk' or 'bp' file format.

    :return: bool - True if build files were successfully created for all apps, False otherwise.

    """
    is_successfully_created = False
    if format_name:
        logging.debug(f"Creating build files for firmware {firmware.md5}...")
        is_successfully_created = create_build_files_for_apps(firmware.android_app_id_list, format_name)
        package_build_files_for_firmware(firmware)
    return is_successfully_created


def package_build_files_for_firmware(firmware):
    """
    Packages the build files for a given firmware into a zip file.
    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.

    """
    logging.debug(f"Packaging build files for firmware {firmware.md5}...")
    with tempfile.TemporaryDirectory() as tmp_root_dir:
        for android_app_lazy in firmware.android_app_id_list:
            android_app = android_app_lazy.fetch()
            logging.debug(android_app.filename)
            module_naming = f"ib_{android_app.md5}"
            tmp_app_dir = os.path.join(tmp_root_dir, module_naming)
            os.mkdir(tmp_app_dir)
            try:
                shutil.copy(android_app.absolute_store_path, tmp_app_dir)
            except FileNotFoundError as err:
                logging.error(f"{android_app.filename}: {err}")
                continue

            for generic_file_lazy in android_app.generic_file_list:
                try:
                    generic_file = generic_file_lazy.fetch()
                    if generic_file.filename == "Android.mk" or generic_file.filename == "Android.bp":
                        logging.debug(f"Found build file {generic_file.filename} for {android_app.filename}")
                        file_path = os.path.join(tmp_app_dir, generic_file.filename)
                        fp = open(file_path, 'wb')
                        fp.write(generic_file.file.read())
                        fp.close()
                except DoesNotExist as err:
                    logging.error(f"{generic_file_lazy.pk}: {err}")

            meta_file = os.path.join(tmp_root_dir, "meta_build.txt")
            fp = open(meta_file, 'a')
            fp.write("    " + module_naming + " \\\n")
            fp.close()

        with tempfile.TemporaryDirectory() as tmp_output_dir:
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


def create_build_files_for_apps(android_app_id_list, format_name):
    """
    Creates build files for a list of Android apps.

    :param android_app_id_list: list - A list of ObjectIDs for class:'AndroidApp'.
    :param format_name: str - 'mk' or 'bp' file format.

    :return: bool - True if build files were successfully created for all apps, False otherwise.

    """
    is_successfully_created = True
    for android_app_lazy in android_app_id_list:
        android_app = android_app_lazy.fetch()
        logging.debug(f"Creating build files for app {android_app.filename}...")
        if not create_build_file_for_app(android_app, format_name):
            is_successfully_created = False
    return is_successfully_created


def create_build_file_for_app(android_app, format_name):
    """
    Creates a build file for a given Android app.

    :param android_app: class:'AndroidApp' - An instance of AndroidApp.
    :param format_name: str - 'mk' or 'bp' file format.

    :return: bool - True if the build file was successfully created, False otherwise.

    """
    try:
        logging.debug(f"Creating build file for app {android_app.filename}...")
        template = ANDROID_MK_TEMPLATE if format_name.lower() == "mk" else ANDROID_BP_TEMPLATE
        create_soong_build_files(android_app, format_name, template)
        return True
    except Exception as err:
        logging.error(err)
        return False


def create_soong_build_files(android_app, file_format, file_template):
    """
    Create an Android.mk or Android.bp file and stores it into the db for the given Android app. A reference to the
    newly created file will be added to the Android app and stored in the db. If an Android.mk or Android.bp file
    already exists, it will be deleted.

    :param android_app: class:'AndroidApp' - App where the reference for the newly create file will be written to. If
    a reference already exists, it will be overwritten.
    :param file_format: str - mk or bp format.
    :param file_template: str - template string for an Android.mk or Android.bp file.

    """
    template_string = create_template_string(android_app, file_template)

    for existing_generic_file_reference in android_app.generic_file_list:
        try:
            existing_generic_file = existing_generic_file_reference.fetch()
            if existing_generic_file.filename == "Android." + file_format:
                logging.debug(f"Deleting existing {file_format} file for app {android_app.filename}...")
                existing_generic_file.delete()
        except Exception as err:
            logging.error(err)
            android_app.generic_file_list.remove(existing_generic_file_reference)

    generic_file = GenericFile(filename=f"Android.{file_format}",
                               file=bytes(template_string, 'utf-8'),
                               document_reference=android_app)
    generic_file.save()
    logging.debug(f"Created {file_format} file for app {android_app.filename}...")
    android_app.generic_file_list.append(generic_file)
    android_app.save()


def create_template_string(android_app, template_string):
    """
    Creates build file (Android.mk or Android.bp) as string for the AOSP image builder.

    :param android_app: class:'AndroidApp' - App class that is used to fill in the template variables.
    :param template_string: String template where variables will be substituted.

    :return: A template string with substituted variables. This string can be written to an Android.mk or Android.bp
    and should be valid for the AOSP build process.

    """
    local_module = f"{android_app.md5}"
    local_src_files = android_app.filename
    # TODO Fetch correct libraries
    local_optional_uses_libraries = ""
    local_certificate = "platform"
    final_template = Template(template_string).substitute(local_module=local_module,
                                                          local_src_files=local_src_files,
                                                          local_certificate=local_certificate,
                                                          local_optional_uses_libraries=local_optional_uses_libraries)
    logging.debug("Created template string")
    return final_template
