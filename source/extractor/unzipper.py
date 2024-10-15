# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import os
import zipfile
import tarfile
import logging
import gzip
import shutil


def extract_zip(zip_file_path, destination_dir):
    """
    Extract the file from a *.zip file.

    :param zip_file_path: str - path to the *.zip file to extract.
    :param destination_dir: str - path to extract to.

    :return: boolean - True in case it was successfully extracted.

    """
    logging.info(f"Zip Extractor: Extracting {zip_file_path} to {destination_dir}")
    is_success = True
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(destination_dir)

        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            extracted_files = zip_ref.namelist()
            for file in extracted_files:
                if not os.path.exists(os.path.join(destination_dir, file)):
                    raise Exception(f"Zip Extractor: File {file} was not extracted from {zip_file_path}")
        logging.info(f"Zip Extractor: Extracted {len(extracted_files)} files from {zip_file_path} to {destination_dir}")
    except Exception as e:
        is_success = False
        logging.warning(str(e))
    return is_success


def extract_tar(file_path, destination_dir):
    """
    Extracts a tar file to the given folder.

    :param file_path: str - path to the *.tar file to extract.
    :param destination_dir: str - path to extract to.

    :return: boolean - True in case it was successfully extracted.

    """
    logging.info(f"Tar Extractor: Extracting {file_path} to {destination_dir}")
    is_success = True
    try:
        if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
            tar_file = tarfile.open(file_path)
            tar_file.extractall(destination_dir)
            tar_file.close()
    except Exception as e:
        is_success = False
        logging.warning(str(e))
    return is_success


def extract_gz(file_path, destination_dir):
    """
    Extracts a gzip file to the given folder.

    :param file_path: str - path to the *.gz file to extract.
    :param destination_dir: str - path to extract to.

    :return: boolean - True in case it was successfully extracted.

    """
    is_success = True
    try:
        if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
            with gzip.open(file_path, 'rb') as f_in:
                new_filename = file_path[:-3]
                dst_path = os.path.join(destination_dir, new_filename)
                with open(dst_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
    except Exception as e:
        is_success = False
        logging.warning(str(e))
    return is_success
