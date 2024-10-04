# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import tempfile
from extractor.dat2img_converter import convert_dat2img
from firmware_handler.ext4_mount_util import run_simg2img_convert


def extract_dat(dat_file_path, extract_destination_folder):
    """
    Converts a .dat file to .img file and attempts to extract the data.

    :param dat_file_path: str - path to the .dat image
    :param extract_destination_folder: str - path to the folder where the data is extracted to.

    :return: True - if extraction was successful, false if not.
    """
    logging.info("Attempt to extract ext with dat2img")
    ext4_image_path = None
    try:
        ext4_image_path = convert_dat2img(dat_file_path, extract_destination_folder)
    except Exception as err:
        logging.warning(f"Abort: Extract_dat_ext4 failed to extract: {dat_file_path} - warning: {err}")
    return ext4_image_path


def extract_simg_ext4(simg_ext4_file_path, extract_destination_folder):
    """
    Converts a simg to ext4 and attempts to extract the data from the ext4.

    :param simg_ext4_file_path: str - path to the simg image
    :param extract_destination_folder: str - path to the folder where the data is extracted to.

    :return: True - if extraction was successful, false if not.
    """
    logging.info("Attempt to extract ext with ext4extract and simg2img")
    could_extract_data = False
    try:
        temp_dir = tempfile.TemporaryDirectory(dir=extract_destination_folder)
        ext4_image_path = run_simg2img_convert(simg_ext4_file_path, temp_dir.name)
        if extract_ext4(ext4_image_path, extract_destination_folder):
            could_extract_data = True
    except Exception as err:
        logging.warning(err)
    return could_extract_data


def extract_ext4(ext4_file_path, extract_destination_folder):
    """
    Extract an ext image to the file system.

    :param ext4_file_path: str - path to the ext image.
    :param extract_destination_folder: str - path where the data is extracted to.

    :return boolean - True: if the data was extract successfully
    """
    from .ext_extraction.app_ext4_extract import Application as ext4extractApp
    logging.info(f"Attempt to extract ext with ext4extract application: {ext4_file_path} to "
                 f"{extract_destination_folder}")
    is_extracted = False
    try:
        argument_dict = {"filename": ext4_file_path,
                         "directory": extract_destination_folder,
                         "metadata": None,
                         "skip_symlinks": True,
                         "text_symlinks": None,
                         "empty_symlinks": None,
                         "symlinks": None}
        ext4extractApp(args=argument_dict).run()
        is_extracted = True
    except Exception as err:
        logging.warning(err)
    return is_extracted
