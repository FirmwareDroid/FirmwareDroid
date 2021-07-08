# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import os
import zipfile
import tarfile
import logging


def unzip_file(zip_file_path, destination_dir):
    """
    Extract the file from a *.zip file.
    :param zip_file_path: str - path to the *.zip file to extract.
    :param destination_dir: str - path to extract to.
    """
    try:
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(destination_dir)
    except Exception as e:
        logging.exception(str(e))


def extract_tar_file(file_path, destination_dir):
    """
    Extracts a tar file to the given folder.
    :param file_path: str - path to the *.tar file to extract.
    :param destination_dir: str - path to extract to.
    :return:
    """
    try:
        if os.path.isfile(file_path) and os.access(file_path, os.R_OK):
            tar_file = tarfile.open(file_path)
            tar_file.extractall(destination_dir)
            tar_file.close()
    except Exception as e:
        logging.exception(str(e))


