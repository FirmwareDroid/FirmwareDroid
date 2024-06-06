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
from context.context_creator import create_db_context, create_log_context
from dynamic_analysis.emulator_preparation.templates.android_app_module_template import ANDROID_MK_TEMPLATE, \
    ANDROID_BP_TEMPLATE
from model import GenericFile, AndroidFirmware
from model.StoreSetting import get_active_store_paths_by_uuid
from utils.mulitprocessing_util.mp_util import start_process_pool

META_BUILD_FILENAME_SYSTEM = "meta_build_system.txt"
META_BUILD_FILENAME_VENDOR = "meta_build_vendor.txt"
META_BUILD_FILENAME_PRODUCT = "meta_build_product.txt"


@create_db_context
@create_log_context
def start_aosp_module_file_creator(format_name, firmware_id_list):
    worker_arguments = [format_name]
    logging.debug(f"Starting app build file creator for format {format_name}... with {len(firmware_id_list)} firmware.")
    start_process_pool(firmware_id_list,
                       worker_process_firmware,
                       number_of_processes=os.cpu_count(),
                       create_id_list=False,
                       worker_args_dict=worker_arguments)


@create_db_context
@create_log_context
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
        logging.debug(f"Creating build files for firmware {firmware.id}...")
        is_successfully_created = create_build_files_for_apps(firmware.android_app_id_list, format_name)
        package_build_files_for_firmware(firmware)
    return is_successfully_created


def package_build_files_for_firmware(firmware):
    """
    Packages the build files for a given firmware into a zip file.
    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.
    """
    logging.info(f"Packaging build files for firmware {firmware.md5}...")
    with tempfile.TemporaryDirectory() as tmp_root_dir:
        process_android_apps(firmware, tmp_root_dir)
        package_files(firmware, tmp_root_dir)


def process_android_apps(firmware, tmp_root_dir):
    """
    Processes the Android apps of a given firmware and creates build files for them.

    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.
    :param tmp_root_dir: tempfile.TemporaryDirectory - A temporary directory to store the build files.

    """
    for android_app_lazy in firmware.android_app_id_list:
        android_app = android_app_lazy.fetch()
        module_naming = f"{android_app.filename.replace('.apk', '')}"
        tmp_app_dir = os.path.join(tmp_root_dir, module_naming)
        os.mkdir(tmp_app_dir)
        new_filename = android_app.filename
        destination_file_path = os.path.join(tmp_app_dir, new_filename)
        try:
            shutil.copy(android_app.absolute_store_path, destination_file_path)
        except FileNotFoundError as err:
            logging.error(f"{android_app.filename}: {err}")
            continue

        process_generic_files(android_app, tmp_app_dir, tmp_root_dir, module_naming)


def process_generic_files(android_app, tmp_app_dir, tmp_root_dir, module_naming):
    """
    Processes the generic files of a given Android app and creates build files for them. The build files will be stored
    in the tmp_app_dir.

    :param tmp_root_dir: str - A temporary directory to store the build files.
    :param android_app: class:'AndroidApp' - An instance of AndroidApp.
    :param tmp_app_dir: tempfile.TemporaryDirectory - A temporary directory to store the build files.
    :param module_naming: str - A string to name the module in the build file.

    """
    for generic_file_lazy in android_app.generic_file_list:
        check_generic_file(android_app, generic_file_lazy)
        process_generic_file(generic_file_lazy, android_app, tmp_app_dir)

    write_to_meta_file(android_app, tmp_root_dir, module_naming)


def check_generic_file(android_app, generic_file_lazy):
    """
    Checks if a generic file is valid. If not, it will be removed from the Android app.
    :param android_app: class:'AndroidApp' - An instance of AndroidApp.
    :param generic_file_lazy: class:'GenericFile' - An instance of GenericFile.
    """
    try:
        generic_file = generic_file_lazy.fetch()
    except Exception as err:
        android_app.generic_file_list.remove(generic_file_lazy)
        android_app.save()
        logging.debug(f"Removed dead reference{generic_file_lazy.pk} from {android_app.id}: {err}")


def process_generic_file(generic_file_lazy, android_app, tmp_app_dir):
    """
    Processes a generic file of a given Android app and creates a build file for it. The build file will be stored in

    :param generic_file_lazy: class:'GenericFile' - An instance of GenericFile.
    :param android_app: class:'AndroidApp' - An instance of AndroidApp.
    :param tmp_app_dir: str - A temporary directory to store the build files.

    """
    try:
        generic_file = generic_file_lazy.fetch()
        if generic_file.filename.lower() == "android.mk" or generic_file.filename.lower() == "android.bp":
            if not generic_file.file:
                raise DoesNotExist(f"Filename: {generic_file.filename} has zero size. Deleting... "
                                   f"generic file id:{generic_file.pk}")
            logging.debug(f"Found build file {generic_file.filename} for {android_app.filename}")
            file_path = os.path.join(tmp_app_dir, generic_file.filename)
            with open(file_path, 'wb') as fp:
                fp.write(generic_file.file.read())
    except Exception as err:
        logging.error(f"{generic_file_lazy.pk}: {err}")


def write_to_meta_file(android_app, tmp_root_dir, module_naming):
    """
    Writes the module naming to a meta file for the given Android app.

    :param android_app: class:'AndroidApp' - An instance of AndroidApp.
    :param tmp_root_dir: str - A temporary directory to store the build files.
    :param module_naming: str - A string to name the module in the build file.

    :return:
    """
    partition_name = android_app.absolute_store_path.split("/")[8]
    logging.debug(f"Partition name: {partition_name} for app {android_app.id}")
    if partition_name.lower() == "vendor":
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_VENDOR)
    elif partition_name.lower() == "product":
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_PRODUCT)
    else:
        meta_file = os.path.join(tmp_root_dir, META_BUILD_FILENAME_SYSTEM)

    with open(meta_file, 'a') as fp:
        fp.write("    " + module_naming + " \\\n")


def package_files(firmware, tmp_root_dir):
    """
    Packages the build files for a given firmware into a zip file and stores it in the aecs_build_file_path of the
    firmware.

    :param firmware: class:'AndroidFirmware' - An instance of AndroidFirmware.
    :param tmp_root_dir: tempfile.TemporaryDirectory - A temporary directory to store the build files.

    """
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
            logging.error(f"Could not create build files for app {android_app.filename}")
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
        logging.error(f"Error with app {android_app.pk}; {err}")
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
    remove_existing_build_files(android_app, file_format)
    create_and_save_generic_file(android_app, file_format, template_string)


def remove_existing_build_files(android_app, file_format):
    """
    Removes an existing Android.mk or Android.bp file for the given Android app.

    :param android_app: class:'AndroidApp' - App where the reference for the newly create file will be written to. If
    :param file_format: str - mk or bp format.

    """
    for existing_generic_file_reference in android_app.generic_file_list:
        try:
            existing_generic_file = existing_generic_file_reference.fetch()
            if existing_generic_file.filename.lower() == "android." + file_format.lower() \
                    or existing_generic_file.filename == "Android.MK":
                logging.debug(f"Deleting existing {file_format} file for app {android_app.filename}...")
                existing_generic_file.delete()
                android_app.generic_file_list.remove(existing_generic_file_reference)
        except Exception as err:
            logging.error(err)
            android_app.generic_file_list.remove(existing_generic_file_reference)


def create_and_save_generic_file(android_app, file_format, template_string):
    """
    Creates a generic file and saves it to the database. The reference to the generic file will be added to the

    :param android_app: class:'AndroidApp' - App where the reference for the newly create file will be written to. If
    :param file_format: str - mk or bp format.
    :param template_string: str - template string for an Android.mk or Android.bp file.

    """
    generic_file = GenericFile(filename=f"Android.{file_format.lower()}",
                               file=bytes(template_string, 'utf-8'),
                               document_reference=android_app)
    generic_file.save()
    logging.debug(f"Created {file_format} file for app {android_app.filename}...")
    android_app.generic_file_list.append(generic_file)
    android_app.save()


def select_signing_key(android_app):
    """
    Selects the signing key for the Android app based on the path of the app and the sharedUserId.
    Possible keys are: networkstack, media, shared, platform, testkey
        shared: sharedUserId="android.uid.shared"
        networkstack: sharedUserId="android.uid.networkstack"
        media: sharedUserId="android.uid.media"
        platform: sharedUserId="android.uid.system"

    Default use is the platform key.

    :return: str - The signing key for the Android app.

    """
    signing_key = "platform"

    if android_app.android_manifest_dict and android_app.android_manifest_dict["manifest"]:
        if "@ns0:sharedUserId" in android_app.android_manifest_dict["manifest"]:
            manifest = android_app.android_manifest_dict["manifest"]
            shared_user_id = manifest["@ns0:sharedUserId"]
            logging.debug(f"UserID found: {shared_user_id} for app {android_app.filename}")
            if shared_user_id == "android.uid.shared" or shared_user_id == "android.shared":
                signing_key = "shared"
            elif shared_user_id == "android.uid.networkstack" or shared_user_id == "android.networkstack":
                signing_key = "networkstack"
            elif shared_user_id == "android.uid.media" or shared_user_id == "android.media":
                signing_key = "media"
            logging.debug(f"Selected signing key: {signing_key} for app {android_app.filename} "
                          f"based on sharedUserId: {shared_user_id}")
    return signing_key


def create_template_string(android_app, template_string):
    """
    Creates build file (Android.mk or Android.bp) as string for the AOSP image builder.

    :param android_app: class:'AndroidApp' - App class that is used to fill in the template variables.
    :param template_string: String template where variables will be substituted.

    :return: A template string with substituted variables. This string can be written to an Android.mk or Android.bp
    and should be valid for the AOSP build process.

    """
    directory_name = android_app.filename.replace('.apk', '')
    local_module = f"{directory_name}"
    local_privileged_module = "false"
    if "/priv-app/" in android_app.absolute_store_path:
        local_module_path = f"$(TARGET_OUT)/priv-app/"
        local_privileged_module = "true"
    elif ("/overlay/" in android_app.absolute_store_path
          and ("/vendor/" in android_app.absolute_store_path) or ("/odm/" in android_app.absolute_store_path)):
        local_module_path = f"$(TARGET_OUT)/odm/overlay/"
    elif ("/vendor/" in android_app.absolute_store_path
          or "/odm/" in android_app.absolute_store_path
          or "/oem/" in android_app.absolute_store_path):
        local_module_path = f"$(TARGET_OUT)/odm/app/"
    else:
        local_module_path = f"$(TARGET_OUT)/app/"
    local_src_files = android_app.filename
    local_optional_uses_libraries = ""

    local_certificate = select_signing_key(android_app)
    local_enforce_uses_libraries = "false"
    local_dex_preopt = "false"
    final_template = Template(template_string).substitute(local_module=local_module,
                                                          local_module_path=local_module_path,
                                                          local_src_files=local_src_files,
                                                          local_certificate=local_certificate,
                                                          local_enforce_uses_libraries=local_enforce_uses_libraries,
                                                          local_dex_preopt=local_dex_preopt,
                                                          local_privileged_module=local_privileged_module,
                                                          local_optional_uses_libraries=local_optional_uses_libraries)
    logging.debug("Created template string")
    return final_template
