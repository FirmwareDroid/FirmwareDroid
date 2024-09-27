# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
import threading
from extractor.ext4_extractor import extract_dat, extract_simg_ext4, extract_ext4
from extractor.bin_extractor.bin_extractor import extract_bin
from extractor.nb0_extractor import extract_nb0
from extractor.pac_extractor import extract_pac
from extractor.unblob_extractor import unblob_extract
from extractor.unzipper import extract_tar, extract_zip, extract_gz
from extractor.lz4_extractor import extract_lz4
from extractor.brotli_extractor import extract_brotli
from firmware_handler.const_regex_patterns import EXT_IMAGE_PATTERNS_DICT

EXTRACTION_SEMAPHORE = threading.Semaphore(20)
MAX_EXTRACTION_DEPTH = 10
IMG_FILE_TYPE_REGEX = r".(img|dat)$"
SUPPORTED_FILE_TYPE_REGEX = r"(zip|tar|md5|lz4|pac|nb0|bin|br|dat|tgz|gz|app|rar)$"

EXTRACT_FUNCTION_MAP_DICT = {
    ".zip": extract_zip,
    ".tar": extract_tar,
    ".tgz": extract_tar,
    ".gz": extract_gz,
    ".md5": extract_tar,
    ".lz4": extract_lz4,
    ".pac": extract_pac,
    ".nb0": extract_nb0,
    ".bin": extract_bin,
    ".br": extract_brotli,
    ".dat": extract_dat,
}


def delete_file_safely(file_path):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass


def get_file_size_mb(file_path):
    size_in_bytes = os.path.getsize(file_path)
    size_in_mb = size_in_bytes / (1024 * 1024)
    return size_in_mb


def get_file_list(destination_dir):
    file_list = []
    for root, dirs, files in os.walk(destination_dir):
        for file in files:
            file_path = str(os.path.join(root, file))
            file_path_abs = os.path.abspath(file_path)
            file_list.append(file_path_abs)
    return file_list


def match_filename_against_patterns(filename, patterns_dict):
    """
    Matches a filename against a dictionary of patterns.

    :param filename: str - filename to match.
    :param patterns_dict: regex patterns to match against.

    :return: bool - flag if the filename matches the patterns.
    """
    for pattern_list in patterns_dict.values():
        for pattern in pattern_list:
            file_extension = os.path.splitext(filename)[1]
            if re.search(pattern, filename) and not re.search(SUPPORTED_FILE_TYPE_REGEX, file_extension):
                logging.info(f"Matched pattern: {pattern} for file: {filename}")
                return True
    return False


def is_partition_found(file_list):
    """
    Check if a main partition was found in the extracted archive.

    :param file_list: list(str) - file paths to check for.

    :return: bool - flag if the main partition was found.

    """
    has_partition = False
    for file in file_list:
        if match_filename_against_patterns(file, EXT_IMAGE_PATTERNS_DICT):
            has_partition = True
            break
    return has_partition


def has_extracted_all_supported_files(file_list):
    """
    Check if all supported files were extracted.

    :param file_list: list(str) - file paths to check for.

    :return: bool - flag if all supported files were extracted.

    """
    has_all_files = True
    for file in file_list:
        if not os.path.isfile(file):
            continue
        if re.search(SUPPORTED_FILE_TYPE_REGEX, file):
            has_all_files = False
            break
    logging.info(f"Has all files extracted: {has_all_files}")
    return has_all_files


def filter_supported_files(file_list):
    pattern = re.compile(SUPPORTED_FILE_TYPE_REGEX)
    filtered_list = [file for file in file_list if os.path.isfile(file) and pattern.search(file)]
    return filtered_list


def extract_first_layer(firmware_archive_file_path, destination_dir):
    """
    Extract the first layer of the firmware archive. Stops extracting when an Android partition (.img file) is found.

    :param firmware_archive_file_path: str - path to the firmware archive.
    :param destination_dir: str - path to the folder where the data is extracted to.

    :return: list(str) - list of paths to the extracted files.

    """
    file_list = extract_list_of_files([firmware_archive_file_path],
                                      destination_dir,
                                      delete_compressed_file=False,
                                      unblob_depth=1)
    logging.info(f"Extracted files count: {len(file_list)}: {file_list}")
    file_list = filter_supported_files(file_list)
    logging.info(f"Filtered files count: {len(file_list)}: {file_list}")
    max_depth = 0
    while max_depth < MAX_EXTRACTION_DEPTH and has_extracted_all_supported_files(file_list) is False:
        try:
            logging.info(f"Checking for Android partition in the first layer depth: {max_depth} | "
                         f"File count: {len(file_list)}")
            file_list = extract_list_of_files(file_list,
                                              destination_dir,
                                              delete_compressed_file=True,
                                              unblob_depth=1)
            logging.info(f"Extracted files count: {len(file_list)}")
            filtered_file_list = filter_supported_files(file_list)
            logging.info(f"Filtered files count: {len(filtered_file_list)}")
            if len(filtered_file_list) > 0:
                file_list = filtered_file_list
        except Exception as err:
            logging.warning(err)
        finally:
            max_depth = max_depth + 1
    logging.info(f"First layer processing done. Depth: {max_depth}")
    return file_list


def get_raw_image(file_path_list):
    raw_image_path = None
    for file_path in file_path_list:
        if os.path.basename(file_path) == "raw.image":
            raw_image_path = file_path
    return raw_image_path


def extract_second_layer(firmware_archive_file_path, destination_dir):
    logging.info(f"Extracting all layers of the firmware archive: {firmware_archive_file_path}")
    extract_image_file(firmware_archive_file_path, destination_dir)
    extracted_file_abs_path_list = get_file_list(destination_dir)
    return extracted_file_abs_path_list


def extract_image_file(image_path, extract_dir_path):
    if extract_simg_ext4(image_path, extract_dir_path):
        logging.debug("Image extraction successful with simg_ext4extractor")
    elif extract_ext4(image_path, extract_dir_path):
        logging.debug("Image extraction successful with ext4extractor")
    elif unblob_extract(image_path, extract_dir_path):
        logging.debug("Image extraction successful with unblob extraction suite")
    else:
        raise RuntimeError(f"Could not extract data from image: {image_path} Maybe unknown format or mount error.")


def extract_list_of_files(file_path_list,
                          destination_dir,
                          delete_compressed_file,
                          unblob_depth=1):
    """
    Extract the compressed file to the destination directory.

    :param file_path_list: list(str) - paths to be processed.
    :param destination_dir: str - path to the folder where the data is extracted to.
    :param delete_compressed_file: bool - delete the compressed file after extraction.
    :param unblob_depth: int - depth of unblob extraction.

    :return: list(str) - list of paths to the extracted files.
    """
    extracted_files_path_list = []
    for file_path in file_path_list:
        if not os.path.exists(file_path):
            continue
        if os.path.isfile(file_path):
            with EXTRACTION_SEMAPHORE:
                extracted_files_for_current_path = process_single_file_path(file_path,
                                                                            destination_dir,
                                                                            delete_compressed_file,
                                                                            unblob_depth)
                extracted_files_path_list.extend(extracted_files_for_current_path)
    return extracted_files_path_list


def process_directory(current_path, queue, failed_extractions, processed_files):
    for filename in os.listdir(current_path):
        next_path = os.path.join(current_path, filename)
        if next_path not in failed_extractions and next_path not in processed_files:
            queue.append(next_path)


def process_file(current_path,
                 destination_dir,
                 unblob_depth,
                 delete_compressed_file):
    file_extension = os.path.splitext(current_path.lower())[1]
    is_success = False
    if file_extension in EXTRACT_FUNCTION_MAP_DICT.keys():
        is_success = EXTRACT_FUNCTION_MAP_DICT[file_extension](current_path, destination_dir)
    is_unblob_success = False
    if not is_success:
        is_unblob_success = unblob_extract(current_path, destination_dir, unblob_depth)

    if delete_compressed_file and (is_success or is_unblob_success):
        delete_file_safely(current_path)


def process_single_file_path(file_path,
                             destination_dir,
                             delete_compressed_file,
                             unblob_depth=1):
    logging.info(f"Extracting: {file_path}, destination: {destination_dir}, delete: {delete_compressed_file}")
    process_file(file_path, destination_dir, unblob_depth, delete_compressed_file)
    logging.info(f"Extraction finished for: {file_path}")
    return get_file_list(destination_dir)
