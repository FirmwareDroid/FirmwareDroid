# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
from extractor.ext4_extractor import extract_simg_ext4, extract_ext4
from extractor.unblob_extractor import unblob_extract
from firmware_handler.firmware_file_search import get_firmware_file_by_regex_list
from extractor.ubi_extractor import extract_ubi_image
from firmware_handler.ext4_mount_util import mount_android_image


def find_image_firmware_file(firmware_file_list, image_filename_pattern_list):
    """
    Checks within the given file list if there is a mountable system partition.

    :param image_filename_pattern_list: str - a list of regex pattern for searching the images filename.
    :param firmware_file_list: The files which will be checked for their names.
    :raise ValueError: Exception raised when the file could not be found.

    :return: class:'FirmwareFile' object of the system.img or system.ext4.img file.

    """
    for firmware_file in firmware_file_list:
        filename = firmware_file.name.lower()
        for pattern in image_filename_pattern_list:
            if (not firmware_file.is_directory
                    and re.search(pattern, filename)
                    and not filename.startswith("._")):
                logging.debug("Found image file: " + str(firmware_file.name))
                return firmware_file
    raise ValueError(f"Continuing. Could not find any image file in the filelist based on the patterns: "
                     f"{' '.join(image_filename_pattern_list)}")


def extract_image_files(image_path, extract_dir_path, store_paths):
    """
    Expands all files from the firmware and mounts the system.img.

    :param store_paths: dict(str, stry) - paths to the file storage.
    :param image_path: str - absolute path to the image file.
    :param extract_dir_path: str - path where the files will be extracted or mounted to.

    :raise RuntimeError: In case none of the support methods can extract files from the image.

    """
    file_extension = os.path.splitext(image_path)[1]
    if file_extension == ".img" or file_extension == ".image":
        if extract_simg_ext4(image_path, extract_dir_path, store_paths):
            logging.debug("Image extraction successful with simg_ext4extractor")
        elif extract_ext4(image_path, extract_dir_path):
            logging.debug("Image extraction successful with ext4extractor")
        elif unblob_extract(image_path, extract_dir_path):
            logging.debug("Image extraction successful with unblob extraction suite")
        elif mount_android_image(image_path, extract_dir_path, store_paths):
            logging.debug("Image mount successful")
        elif extract_ubi_image(image_path, extract_dir_path):
            logging.debug("Image extraction successful with UBI")
        else:
            raise RuntimeError(f"Could not extract data from image: {image_path} Maybe unknown format or mount error.")
    else:
        if unblob_extract(image_path, extract_dir_path):
            logging.debug("Image extraction successful with unblob extraction suite")


def create_abs_image_file_path(image_file, cache_temp_file_dir_path):
    """
    Attempts to create a path for the given image.

    :param image_file: class:'FirmwareFile'
    :param cache_temp_file_dir_path: temporaryDirectory
    :return: str - absolute path of the file if it exists or none if not.

    """
    image_absolute_path = os.path.abspath(os.path.join(cache_temp_file_dir_path, image_file.relative_path))
    if not os.path.exists(image_absolute_path):
        if image_file.relative_path.startswith("."):
            image_absolute_path = cache_temp_file_dir_path \
                                         + image_file.relative_path.replace(".", "", 1)
        else:
            image_absolute_path = cache_temp_file_dir_path + image_file.relative_path
    return image_absolute_path


def find_image_abs_path(firmware, source_dir_path, image_filename_pattern_list):
    """
    Attempts to find the images absolute path within the extracted firmware archive.

    :param firmware: class:'AndroidFirmware' - Android firmware to search through.
    :param source_dir_path: str - path to the firmware root directory where the image was extracted to.
    :param image_filename_pattern_list: str - a list of regex pattern for searching the images filename.
    :return: str - absolute path to the image file.

    """
    image_firmware_file = get_firmware_file_by_regex_list(firmware, image_filename_pattern_list)
    if not image_firmware_file:
        raise ValueError("Could not find image file in database.")
    return create_abs_image_file_path(image_firmware_file, source_dir_path)
