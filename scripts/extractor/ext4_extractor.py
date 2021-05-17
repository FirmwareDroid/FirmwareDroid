import logging
import tempfile
import flask
import sys
from scripts.firmware.ext4_mount_util import simg2img_convert_ext4


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
        temp_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
        ext4_image_path = simg2img_convert_ext4(simg_ext4_file_path, temp_dir.name)
        if extract_ext4(ext4_image_path, extract_destination_folder):
            could_extract_data = True
    except Exception as err:
        logging.error(err)
    return could_extract_data


def extract_ext4(ext4_file_path, extract_destination_folder):
    """
    Extract an ext image to the file system.
    :param ext4_file_path: str - path to the ext image.
    :param extract_destination_folder: str - path where the data is extracted to.
    """
    from .ext_extraction.app_ext4_extract import Application as ext4extractApp
    logging.info(f"Attempt to extract ext with ext4extract application: {ext4_file_path} to "
                 f"{extract_destination_folder}")
    could_extract_data = False
    try:
        argument_dict = {
            "filename": ext4_file_path,
            "directory": extract_destination_folder,
            "symlinks": None,
            "metadata": None,
        }
        ext4extractApp(args=argument_dict).run()
        could_extract_data = True
    except Exception as err:
        logging.error(err)
    return could_extract_data
