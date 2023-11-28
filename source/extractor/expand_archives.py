# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import re
from extractor.ext4_extractor import extract_dat_ext4
from extractor.bin_extractor.bin_extractor import extract_bin
from extractor.nb0_extractor import extract_nb0
from extractor.pac_extractor import unpack_pac
from extractor.unblob_extractor import unblob_extract
from extractor.unzipper import extract_tar_file, unzip_file
from extractor.lz4_extractor import extract_lz4
from extractor.brotli_extractor import extract_brotli


def extract_all_nested(compressed_file_path, destination_dir, delete_compressed_file):
    """
    Decompress a zip/tar/lz4/pac/nb0 file and its contents recursively, including nested zip/tar/lz4 files.

    :param compressed_file_path: str - path to the compressed file.
    :param destination_dir: str - path to extract to.
    :param delete_compressed_file: boolean - if true, deletes the archive after it is extracted.

    """
    supported_file_types_regex = r'\.zip$|\.tar$|\.tar\.md5$|\.lz4$|\.pac$|\.nb0$|\.bin$|\.br$|\.dat$'
    # TODO enhance security! Make this function more secure - set maximal recursion depth!
    try:
        is_success = True
        if compressed_file_path.lower().endswith(".zip"):
            logging.info(f"Attempt to extract .zip file: {compressed_file_path}")
            is_success = unzip_file(compressed_file_path, destination_dir)
        elif compressed_file_path.lower().endswith(".tar") or compressed_file_path.endswith(".tar.md5"):
            logging.info(f"Attempt to extract .tar file: {compressed_file_path}")
            is_success = extract_tar_file(compressed_file_path, destination_dir)
        elif compressed_file_path.lower().endswith(".lz4"):
            logging.info(f"Attempt to extract lz4 file: {compressed_file_path}")
            is_success = extract_lz4(compressed_file_path, destination_dir)
        elif compressed_file_path.lower().endswith(".pac"):
            logging.info(f"Attempt to extract pac file: {compressed_file_path}")
            is_success = unpack_pac(compressed_file_path)
        elif compressed_file_path.lower().endswith(".nb0"):
            logging.info(f"Attempt to extract nb0 file: {compressed_file_path}")
            is_success = extract_nb0(compressed_file_path)
        elif compressed_file_path.lower().endswith(".bin"):
            logging.info(f"Attempt to extract bin file: {compressed_file_path}")
            is_success = extract_bin(compressed_file_path, destination_dir)
        elif compressed_file_path.lower().endswith(".br"):
            logging.info(f"Attempt to extract brotli file: {compressed_file_path}")
            is_success = extract_brotli(compressed_file_path, destination_dir)
        elif compressed_file_path.lower().endswith(".dat"):
            logging.info(f"Attempt to extract dat file: {compressed_file_path}")
            is_success = extract_dat_ext4(compressed_file_path, destination_dir)
        else:
            unblob_extract(compressed_file_path, destination_dir)

        if not is_success:
            logging.info(f"First extraction attempt failed. Try again using unblob now: {compressed_file_path}")
            unblob_extract(compressed_file_path, destination_dir)
    except Exception as err:
        logging.warning(f"Skip file due to decompression error: {err}")

    try:
        if delete_compressed_file:
            os.remove(compressed_file_path)
    except FileNotFoundError:
        pass
    for root, dirs, files in os.walk(destination_dir):
        for filename in files:
            if re.search(supported_file_types_regex, filename.lower()):
                nested_file_path = os.path.join(root, filename)
                if not os.path.exists(nested_file_path) \
                        and not nested_file_path.startswith("/")\
                        and not nested_file_path.startswith("./"):
                    logging.info(f"Attempt to fix path: {nested_file_path}")
                    nested_file_path = "./" + nested_file_path
                if os.path.exists(nested_file_path):
                    extract_all_nested(nested_file_path, root, True)
                else:
                    logging.info(f"Expand: Skip file {nested_file_path}")



