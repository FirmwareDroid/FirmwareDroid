import logging
import os
import shutil
from mongoengine import DoesNotExist
from string import Template
from dynamic_analysis.emulator_preparation.aosp_file_exporter import get_subfolders
from firmware_handler.firmware_file_exporter import remove_unblob_extract_directories
from model import GenericFile
from dynamic_analysis.emulator_preparation.aosp_meta_writer import add_module_to_meta_file, add_to_log_file
from dynamic_analysis.emulator_preparation.templates.android_app_module_template import ANDROID_MK_TEMPLATE, \
    ANDROID_BP_TEMPLATE


def create_build_files_for_apps(android_app_id_list, format_name):
    """
    Creates build files for a list of Android apps.

    :param android_app_id_list: list - A list of ObjectIDs for class:'AndroidApp'.
    :param format_name: str - 'mk' or 'bp' file format.


    """
    for android_app_lazy in android_app_id_list:
        android_app = android_app_lazy.fetch()
        logging.debug(f"Creating build files for app {android_app.filename}...")
        create_build_file_for_app(android_app, format_name)


def create_build_file_for_app(android_app, format_name):
    """
    Creates a build file for a given Android app.

    :param android_app: class:'AndroidApp' - An instance of AndroidApp.
    :param format_name: str - 'mk' or 'bp' file format.

    """
    logging.debug(f"Creating build file for app {android_app.filename}...")
    template = ANDROID_MK_TEMPLATE if format_name.lower() == "mk" else ANDROID_BP_TEMPLATE
    create_make_files(android_app, format_name, template)


def create_make_files(android_app, file_format, template_string):
    """
    Create an Android.mk or Android.bp file and stores it into the db for the given Android app. A reference to the
    newly created file will be added to the Android app and stored in the db. If an Android.mk or Android.bp file
    already exists, it will be deleted.

    :param android_app: class:'AndroidApp' - App where the reference for the newly create file will be written to. If
    a reference already exists, it will be overwritten.
    :param file_format: str - mk or bp format.
    :param template_string: str - template string for an Android.mk or Android.bp file.

    """
    template_string_complete, local_module = create_template_string(android_app, template_string)
    remove_existing_build_files(android_app, file_format)
    create_and_save_generic_file(android_app, file_format, template_string_complete)


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


def process_generic_files(android_app, tmp_app_dir):
    """
    Processes the generic files of a given Android app and creates build files for them. The build files will be stored
    in the tmp_app_dir.

    :param android_app: class:'AndroidApp' - An instance of AndroidApp.
    :param tmp_app_dir: tempfile.TemporaryDirectory - A temporary directory to store the build files.

    """
    for generic_file_lazy in android_app.generic_file_list:
        check_generic_file(android_app, generic_file_lazy)
        process_generic_file(generic_file_lazy, android_app, tmp_app_dir)


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
    signing_key = None

    if android_app.android_manifest_dict and android_app.android_manifest_dict["manifest"]:
        signing_key = get_signing_key_by_uid(android_app)

        if not signing_key:
            signing_key = get_signing_key_by_package_name(android_app)

    if not signing_key:
        signing_key = "platform"

    return signing_key


def get_signing_key_by_package_name(android_app):
    signing_key = ""
    if "@package" in android_app.android_manifest_dict["manifest"]:
        package_name = android_app.android_manifest_dict["manifest"]["@package"]
        if "networkstack" in package_name or "cellbroadcast" in package_name:
            signing_key = "networkstack"
    return signing_key


def get_signing_key_by_uid(android_app):
    signing_key = None
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
    else:
        logging.warning(f"No sharedUserId found for app {android_app.filename}")

    return signing_key


def get_apk_local_module_path(file_path, partition_name, android_app):
    """
    Get the local module path for the given partition_name.

    :param android_app: class:'AndroidApp' - App that a
    :param file_path: str - path to the module file.
    :param partition_name: str - name of the partition on Android.

    :return: str - local module path for the shared library module.

    """
    subfolder_list = get_subfolders(file_path, partition_name)
    if "/priv-app/" in android_app.absolute_store_path:
        local_module_path = f"$(TARGET_OUT)/priv-app/"
    elif ("/overlay/" in android_app.absolute_store_path
          and ("/vendor/" in android_app.absolute_store_path)
          or ("/odm/" in android_app.absolute_store_path)):
        local_module_path = f"$(TARGET_OUT)/odm/overlay/"
    elif ("/vendor/" in android_app.absolute_store_path
          or "/odm/" in android_app.absolute_store_path
          or "/oem/" in android_app.absolute_store_path):
        local_module_path = f"$(TARGET_OUT)/odm/app/"
    elif len(subfolder_list) <= 1:
        local_module_path = f"$(TARGET_OUT)/app/"
    else:
        path = os.path.join(*subfolder_list)
        fixed_path = remove_unblob_extract_directories(path)
        local_module_path = f"$(TARGET_OUT)/{fixed_path}"
        local_module_path = local_module_path.replace(android_app.filename, "")
    return local_module_path


def create_template_string(android_app, template_string):
    """
    Creates build file (Android.mk or Android.bp) as string for the AOSP image builder.

    :param android_app: class:'AndroidApp' - App class that is used to fill in the template variables.
    :param template_string: String template where variables will be substituted.

    :return: str - A template string with substituted variables.
            str - The string of the local module name

    """
    directory_name = android_app.filename.replace('.apk', '')
    local_module = f"{directory_name}"
    local_privileged_module = "false"
    if not os.path.exists(android_app.absolute_store_path):
        raise FileNotFoundError(f"File not found: {android_app.absolute_store_path} | {android_app.pk}")
    partition_name = android_app.absolute_store_path.split("/")[8]
    local_module_path = get_apk_local_module_path(android_app.absolute_store_path, partition_name, android_app)
    if "/priv-app" in local_module_path or "/framework" in local_module_path:
        local_privileged_module = "true"

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
    return final_template, local_module


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
        if not os.path.exists(tmp_app_dir):
            os.mkdir(tmp_app_dir)
        new_filename = android_app.filename
        destination_file_path = os.path.join(tmp_app_dir, new_filename)
        try:
            shutil.copy(android_app.absolute_store_path, destination_file_path)
        except FileNotFoundError as err:
            logging.error(f"{android_app.filename}: {err}")
            continue

        process_generic_files(android_app, tmp_app_dir)
        partition_name = android_app.absolute_store_path.split("/")[8]
        logging.debug(f"Partition name: {partition_name} for app {android_app.id}")
        add_module_to_meta_file(partition_name, tmp_root_dir, module_naming)
        log_entry = (f"Partition:{partition_name} "
                     f"| APK:{android_app.filename} "
                     f"| ID:{android_app.id} "
                     f"| Module:{module_naming}")
        add_to_log_file(tmp_root_dir, log_entry, "apk_module_builder.log")
