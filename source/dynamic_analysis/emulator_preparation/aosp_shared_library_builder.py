import logging
import os
import re
import shutil
from string import Template
from dynamic_analysis.emulator_preparation.templates.shared_library_module_template import \
    ANDROID_MK_SHARED_LIBRARY_TEMPLATE, ANDROID_BP_SHARED_LIBRARY_TEMPLATE
from firmware_handler.firmware_file_exporter import start_firmware_file_export, NAME_EXPORT_FOLDER
from model.StoreSetting import StoreSetting


def copy_file(source_folder, destination_folder):
    """
    Moves the file from the source folder to the destination folder.

    :param source_folder: str - path to the source folder.
    :param destination_folder: str - path to the destination folder.

    :return: str - path to the zip file.

    """
    if not os.path.exists(destination_folder):
        os.makedirs(destination_folder)
    if not os.path.exists(source_folder):
        raise Exception(f"The source folder does not exist: {source_folder}")
    logging.info(f"Copying file from {source_folder} to {destination_folder}")
    shutil.copy(source_folder, destination_folder)


def create_template_string(format_name, library_path):
    """
    Creates the template string for the shared library module.

    :param format_name: str - format name of the shared library module.
    :param library_path: str - path to the shared library module.

    :return: str - template string for the shared library module.

    """
    file_template = ANDROID_MK_SHARED_LIBRARY_TEMPLATE if format_name.lower() == "mk" \
        else ANDROID_BP_SHARED_LIBRARY_TEMPLATE

    if format_name.lower() != "mk":
        raise NotImplementedError(f"Format name {format_name} is not supported yet.")

    library_name = os.path.basename(library_path)
    local_module = library_name.replace(".so", "")
    local_src_files = library_name

    # Installation path on the device
    if "/lib64/" in library_path:
        local_module_path = "$(TARGET_OUT)/lib64/"
    elif "/lib/" in library_path:
        local_module_path = "$(TARGET_OUT)/lib/"
    elif "/app/" in library_path:
        app_name = library_path.split("/app/")[1]
        local_module_path = f"$(TARGET_OUT)/app/{app_name}/lib/$(TARGET_ARCH_ABI)/"
    elif "/priv-app/" in library_path:
        app_name = library_path.split("/priv-app/")[1]
        local_module_path = f"$(TARGET_OUT)/priv-app/{app_name}/lib/$(TARGET_ARCH_ABI)/"
    else:
        local_module_path = "$(TARGET_OUT)/lib64/"

    local_prebuilt_module_file = f"$(LOCAL_PATH)/{library_name}"
    template_out = Template(file_template).substitute(local_module=local_module,
                                                      local_module_path=local_module_path,
                                                      local_src_files=local_src_files,
                                                      local_prebuilt_module_file=local_prebuilt_module_file
                                                      )
    return template_out


def write_template_to_file(template_out, destination_folder):
    """
    Writes the template string to a file.

    :param template_out: str - template string for the shared library module.
    :param destination_folder: str - path to the destination folder.

    :return: str - path to the shared library module.

    """
    file_path = os.path.join(destination_folder, "Android.mk")
    with open(file_path, "w") as file:
        file.write(template_out)
    return file_path


def create_shared_library_modules(source_folder, destination_folder, format_name):
    """
    This function is used to create the shared library module for AOSP firmware.

    :param source_folder: str - path to the source folder.
    :param destination_folder: str - path to the destination folder.
    :param format_name: str - format name of the shared library module.

    :return: str - path to the shared library module.

    """
    for root, dirs, files in os.walk(str(source_folder)):
        for file in files:
            source_file = os.path.join(root, file)
            if not os.path.exists(source_file):
                raise Exception(f"The source file does not exist: {source_file}")
            template_out = create_template_string(format_name, source_file)
            destination_folder = os.path.join(destination_folder,
                                              os.path.basename(source_file.replace(".so", "")))
            logging.info(f"Creating shared library module for {source_file} in {destination_folder}")
            copy_file(source_file, destination_folder)
            write_template_to_file(template_out, destination_folder)


def process_shared_libraries(firmware, destination_folder, store_setting_id, format_name):
    """
    This function is used to process the shared libraries of a firmware. It extracts the shared libraries from the
    firmware and creates the shared library modules for AOSP firmware.

    :param firmware: class:'Firmware'
    :param destination_folder: str - path to the destination folder.
    :param store_setting_id: int - id of the store setting.
    :param format_name: str - format name of the shared library module.

    """
    filename_regex = ".so$"
    search_pattern = re.compile(filename_regex, re.IGNORECASE)
    firmware_id_list = [firmware.id]
    start_firmware_file_export(search_pattern, firmware_id_list, store_setting_id)
    store_setting = StoreSetting.objects.get(pk=store_setting_id)
    source_folder = os.path.join(
        store_setting.store_options_dict[store_setting.uuid]["paths"]["FIRMWARE_FOLDER_FILE_EXTRACT"],
        NAME_EXPORT_FOLDER,
        str(firmware.id))
    if not os.path.exists(source_folder):
        raise Exception(f"The source folder does not exist: {source_folder}")
    logging.info(f"Processing shared libraries in {source_folder}")
    create_shared_library_modules(source_folder, destination_folder, format_name)
