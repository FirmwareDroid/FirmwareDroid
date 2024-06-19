# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
import magic
from extractor.ext4_extractor import extract_dat
from extractor.bin_extractor.bin_extractor import extract_bin
from extractor.nb0_extractor import extract_nb0
from extractor.pac_extractor import extract_pac
from extractor.unblob_extractor import unblob_extract
from extractor.unzipper import extract_tar, extract_zip, extract_gz
from extractor.lz4_extractor import extract_lz4
from extractor.brotli_extractor import extract_brotli

EXTRACTION_SIZE_THRESHOLD_MB = 100


def normalize_file_path(file_path):
    if not os.path.exists(file_path) and not file_path.startswith("/") and not file_path.startswith("./"):
        file_path = "./" + file_path
    return file_path


def process_file(root, filename, supported_file_types_regex):
    if re.search(supported_file_types_regex, filename.lower()):
        nested_file_path = os.path.join(root, filename)
        nested_file_path = normalize_file_path(nested_file_path)

        if os.path.exists(nested_file_path):
            extract_archive_layer(nested_file_path, root, True)
        else:
            logging.debug(f"Skipped file cause it no longer exists on disk: {nested_file_path}")


def process_directory(destination_dir, supported_file_types_regex):
    for root, dirs, files in os.walk(destination_dir):
        for filename in files:
            process_file(root, filename, supported_file_types_regex)


def delete_file_safely(file_path):
    try:
        os.remove(file_path)
    except FileNotFoundError:
        pass


def get_file_size_mb(file_path):
    size_in_bytes = os.path.getsize(file_path)
    size_in_mb = size_in_bytes / (1024 * 1024)
    return size_in_mb


def get_file_type(file_path):
    mime = magic.Magic(mime=True)
    file_type = mime.from_file(file_path)
    return file_type


def extract_archive_layer(compressed_file_path, destination_dir, delete_compressed_file, depth=2):
    """
    Decompress supported archive file type and its contents recursively, including nested archives files.
    Files smaller than EXTRACTION_SIZE_THRESHOLD_MB are not extracted.

    :param depth: int - depth of the unblob extraction.
    :param compressed_file_path: str - path to the compressed file.
    :param destination_dir: str - path to extract to.
    :param delete_compressed_file: boolean - if true, deletes the archive after it is extracted.

    """
    supported_file_types_regex = r".(zip|tar|md5|lz4|pac|nb0|bin|br|dat|tgz|gz)$"
    extract_function_dict = {
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

    is_success = False
    file_extension = os.path.splitext(compressed_file_path.lower())[1]
    if file_extension is None:
        try:
            file_extension = get_file_type(compressed_file_path)
        except Exception as e:
            pass

    if file_extension in extract_function_dict:
        extraction_function = extract_function_dict[file_extension]
        logging.info(f"Attempt to extract: {compressed_file_path}")
        is_success = extraction_function(compressed_file_path, destination_dir)
    else:
        logging.info(f"Skip file due file extension: {compressed_file_path}")

    if not is_success:
        file_size_mb = get_file_size_mb(compressed_file_path)
        if file_size_mb > EXTRACTION_SIZE_THRESHOLD_MB:
            logging.info(f"Changing to unblob to extract: {compressed_file_path}")
            unblob_extract(compressed_file_path, destination_dir, depth)
        else:
            logging.info(f"Skip file due small size: {compressed_file_path}")

    if delete_compressed_file:
        delete_file_safely(compressed_file_path)

    process_directory(destination_dir, supported_file_types_regex)



