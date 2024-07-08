# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
from extractor.ext4_extractor import extract_dat
from extractor.bin_extractor.bin_extractor import extract_bin
from extractor.nb0_extractor import extract_nb0
from extractor.pac_extractor import extract_pac
from extractor.unblob_extractor import unblob_extract
from extractor.unzipper import extract_tar, extract_zip, extract_gz
from extractor.lz4_extractor import extract_lz4
from extractor.brotli_extractor import extract_brotli
from collections import deque

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


def extract_archive_layer(compressed_file_path,
                          destination_dir,
                          delete_compressed_file,
                          unblob_depth=1,
                          max_rec_depth=MAX_EXTRACTION_DEPTH):
    """
    Extract the compressed file to the destination directory.
    If the file is not supported, it will be extracted with a python function otherwise with unblob.

    :param compressed_file_path: str - path to the compressed file.
    :param destination_dir: str - path to the folder where the data is extracted to.
    :param delete_compressed_file: bool - delete the compressed file after extraction.
    :param unblob_depth: int - depth of unblob extraction.
    :param max_rec_depth: int - maximum extraction depth.

    :return:
    """
    queue = deque([(compressed_file_path, 0)])  # Each item is a tuple of (path, current depth)
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
            logging.debug(f"Extracting: {current_path}")
            file_extension = os.path.splitext(current_path.lower())[1]
            if file_extension in EXTRACT_FUNCTION_MAP_DICT:
                logging.info(f"Attempt to extract: {current_path}")
                is_success = EXTRACT_FUNCTION_MAP_DICT[file_extension](current_path, destination_dir)
                if not is_success:
                    unblob_extract(current_path, destination_dir, unblob_depth)
            else:
                unblob_extract(current_path, destination_dir, unblob_depth)

            if delete_compressed_file:
                delete_file_safely(current_path)
