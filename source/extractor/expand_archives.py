# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
from extractor.ext4_extractor import extract_dat
from extractor.bin_extractor.bin_extractor import extract_bin
from extractor.nb0_extractor import extract_nb0
from extractor.pac_extractor import extract_pac
from extractor.unblob_extractor import unblob_extract
from extractor.unzipper import extract_tar, extract_zip, extract_gz
from extractor.lz4_extractor import extract_lz4
from extractor.brotli_extractor import extract_brotli
from collections import deque

from firmware_handler.const_regex_patterns import EXT_IMAGE_PATTERNS_DICT

EXTRACTION_SIZE_THRESHOLD_MB = 100
MAX_EXTRACTION_DEPTH = 20
SUPPORTED_FILE_TYPE_REGEX = r".(zip|tar|md5|lz4|pac|nb0|bin|br|dat|tgz|gz)$"
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


def normalize_file_path(file_path):
    if not os.path.exists(file_path) and not file_path.startswith("/") and not file_path.startswith("./"):
        file_path = "./" + file_path
    return file_path


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
            file_path = os.path.join(root, file)
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


def extract_first_layer(firmware_archive_file_path, destination_dir):
    """
    Extract the first layer of the firmware archive. Stops extracting when an Android partition (.img file) is found.

    :param firmware_archive_file_path: str - path to the firmware archive.
    :param destination_dir: str - path to the folder where the data is extracted to.

    :return: list(str) - list of paths to the extracted files.

    """
    file_list = extract_archive_layer([firmware_archive_file_path],
                                      destination_dir,
                                      delete_compressed_file=False,
                                      unblob_depth=1,
                                      max_rec_depth=1)
    while is_partition_found(file_list) is False:
        file_list = extract_archive_layer(file_list,
                                          destination_dir,
                                          delete_compressed_file=True,
                                          unblob_depth=1,
                                          max_rec_depth=1)
    return file_list


def extract_archive_layer(compressed_file_path_list,
                          destination_dir,
                          delete_compressed_file,
                          unblob_depth=1,
                          max_rec_depth=MAX_EXTRACTION_DEPTH):
    """
    Extract the compressed file to the destination directory.

    :param compressed_file_path_list: list(str) - paths to the compressed files.
    :param destination_dir: str - path to the folder where the data is extracted to.
    :param delete_compressed_file: bool - delete the compressed file after extraction.
    :param unblob_depth: int - depth of unblob extraction.
    :param max_rec_depth: int - maximum extraction depth.

    :return: list(str) - list of paths to the extracted files.
    """
    extracted_files_path_list = []
    for file_path in compressed_file_path_list:
        if not os.path.isfile(file_path):
            logging.warning(f"Invalid file path: {file_path}")
            continue
        extracted_files_for_current_path = process_single_file_path(
            file_path, destination_dir, delete_compressed_file, unblob_depth, max_rec_depth)
        extracted_files_path_list.extend(extracted_files_for_current_path)
    return extracted_files_path_list


def process_single_file_path(file_path,
                             destination_dir,
                             delete_compressed_file,
                             unblob_depth=1,
                             max_rec_depth=MAX_EXTRACTION_DEPTH):
    """
    Extract the compressed file to the destination directory.
    If the file is not supported, it will be extracted with a python function otherwise with unblob.

    :param file_path: str - path to the compressed file.
    :param destination_dir: str - path to the folder where the data is extracted to.
    :param delete_compressed_file: bool - delete the compressed file after extraction.
    :param unblob_depth: int - depth of unblob extraction.
    :param max_rec_depth: int - maximum extraction depth.

    :return: list(str) - list of paths to the extracted files.
    """
    logging.info(f"Extracting: {file_path}")
    queue = deque([(file_path, 0)])  # Each item is a tuple of (path, current depth)
    while queue:
        current_path, current_depth = queue.popleft()
        logging.debug(f"Current path: {current_path}")
        if current_depth >= max_rec_depth:
            logging.warning(f"Max recursion depth reached: {max_rec_depth}")
            continue

        if os.path.isdir(current_path):
            for filename in os.listdir(current_path):
                file_path = os.path.join(current_path, filename)
                logging.debug(f"Adding to queue: {file_path}")
                queue.append((file_path, current_depth + 1))
        else:
            file_extension = os.path.splitext(current_path.lower())[1]
            logging.debug(f"Extracting: {current_path}, extension: {file_extension}")
            if file_extension in EXTRACT_FUNCTION_MAP_DICT.keys():
                logging.info(f"Attempt to extract: {current_path}")
                is_success = EXTRACT_FUNCTION_MAP_DICT[file_extension](current_path, destination_dir)
                if not is_success:
                    unblob_extract(current_path, destination_dir, unblob_depth)
            else:
                unblob_extract(current_path, destination_dir, unblob_depth)

            if delete_compressed_file:
                delete_file_safely(current_path)
    return get_file_list(destination_dir)
