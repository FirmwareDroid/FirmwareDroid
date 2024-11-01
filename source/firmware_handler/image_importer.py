# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import re


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
        pattern_match_count = 0
        for pattern in image_filename_pattern_list:
            pattern_match_count += 1
            if (not firmware_file.is_directory
                    and re.search(pattern, filename)
                    and not filename.startswith("._")):
                if "vbmeta" not in filename and "patch" not in filename:
                    logging.debug(f"Found potential image file:{firmware_file.name} for pattern: {pattern}")
                    potential_image_files.append(firmware_file)
                    # good match already
                    if pattern_match_count < 3:
                        break
    if not potential_image_files:
        raise ValueError(f"Could not find image file in the filelist based on the patterns: "
                         f"{' '.join(image_filename_pattern_list)}")
    potential_image_files = list(set(potential_image_files))
    return potential_image_files
