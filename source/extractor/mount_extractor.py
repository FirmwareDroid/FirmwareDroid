import logging
from extractor.mount_commands import copy_files_and_unmount
from firmware_handler.ext4_mount_util import run_simg2img_convert


def mount_extract(source_file_path, destination_dir):
    """
    Extract image from the given image file.

    :param source_file_path: str - path to the .bin file.
    :param destination_dir: str - path where the file is extracted to.

    :return: boolean - True in case it was successfully extracted.
    """
    is_success = False
    try:
        is_copy_success = copy_files_and_unmount(source_file_path, destination_dir)
        if is_copy_success:
            is_success = True
    except Exception as e:
        logging.error(f"Error while extracting f2fs file: {e}")
        is_success = False
    return is_success


def simg2img_and_mount_extract(source_file_path, destination_dir):
    """
    Extract image from the given image file.

    :param source_file_path: str - path to the .bin file.
    :param destination_dir: str - path where the file is extracted to.

    :return: boolean - True in case it was successfully extracted.
    """
    is_success = False
    try:
        img_raw_file_path = run_simg2img_convert(source_file_path, destination_dir)
        logging.info(f"Converted image with simg2img successfully to {img_raw_file_path}")
        mount_extract(img_raw_file_path, destination_dir)
    except Exception as e:
        logging.error(f"Error while extracting f2fs file: {e}")
        is_success = False
    return is_success

