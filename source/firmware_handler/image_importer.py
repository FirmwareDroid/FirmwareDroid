# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
from firmware_handler.firmware_file_search import get_firmware_file_by_regex_list


def find_image_firmware_file(firmware_file_list, image_filename_pattern_list):
    """
    Checks within the given file list if there is a mountable system partition.

    :param image_filename_pattern_list: str - a list of regex pattern for searching the images' filename.
    :param firmware_file_list: The files which will be checked for their names.
    :raise ValueError: Exception raised when the file could not be found.

    :return: list(class:'FirmwareFile') - potential image files that match the regex pattern.

    """
    potential_image_files = []
    for firmware_file in firmware_file_list:
        filename = firmware_file.name.lower()
        for pattern in image_filename_pattern_list:
            if (not firmware_file.is_directory
                    and re.search(pattern, filename)
                    and not filename.startswith("._")):
                if "vbmeta" not in filename and "patch" not in filename:
                    logging.debug(f"Found potential image file:{firmware_file.name} for pattern: {pattern}")
                    potential_image_files.append(firmware_file)
    if not potential_image_files:
        raise ValueError(f"Could not find image file in the filelist based on the patterns: "
                         f"{' '.join(image_filename_pattern_list)}")
    potential_image_files = list(set(potential_image_files))
    return potential_image_files


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
