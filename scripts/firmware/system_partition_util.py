import logging
import os

from scripts.extractor.ubi_extractor import extract_ubi_image
from scripts.firmware.firmware_file_search import get_firmware_file_by_regex_list
from scripts.extractor.expand_archives import extract_all_nested
from scripts.firmware.const_regex import SYSTEM_IMG_PATTERN_LIST
from scripts.firmware.ext4_mount_util import mount_android_ext4_image


def expand_and_mount(firmware, extract_dir_path, mount_dir_path):
    """
    Expands all files from the firmware and mounts the system.img.
    :param firmware: class:'AndroidFirmware'
    :param extract_dir_path: str - path where the file will be unpacked to.
    :param mount_dir_path: str - path where the systen.img will be mounted.
    """
    extract_all_nested(firmware.absolute_store_path, extract_dir_path, False)
    system_image_firmware_file = get_firmware_file_by_regex_list(firmware, SYSTEM_IMG_PATTERN_LIST)
    if system_image_firmware_file:
        system_abs_path = create_system_img_path(system_image_firmware_file, extract_dir_path)
        if not system_abs_path:
            raise ValueError(f"Could not set system.img absolute path: {system_image_firmware_file.name}")
        extract_ubi_image(system_abs_path, mount_dir_path) # TODO remove this
        if not mount_android_ext4_image(system_abs_path, mount_dir_path):
           logging.info("Mound failed")
    else:
        raise ValueError("Could not find system.img in database.")


def create_system_img_path(system_image, cache_temp_file_dir_path):
    """
    Attempts to create a path for the given image.
    :param system_image: class:'FirmwareFile'
    :param cache_temp_file_dir_path: temporaryDirectory
    :return: str - absolute path of the file if it exists or none if not.
    """
    system_image_absolute_path = os.path.abspath(os.path.join(cache_temp_file_dir_path, system_image.relative_path))
    if not os.path.exists(system_image_absolute_path):
        if system_image.relative_path.startswith("."):
            system_image_absolute_path = cache_temp_file_dir_path \
                                         + system_image.relative_path.replace(".", "", 1)
        else:
            system_image_absolute_path = cache_temp_file_dir_path + system_image.relative_path
    return system_image_absolute_path
