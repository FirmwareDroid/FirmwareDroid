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
    except OSError as err:
        logging.warning(err)
    return could_extract_data


def extract_ext4(ext4_file_path, extract_destination_folder):
    """
    Extract an ext image to the file system.
    :param ext4_file_path: str - path to the ext image.
    :param extract_destination_folder: str - path where the data is extracted to.
    """
    from ext4extract.app import Application as ext4extract_app
    logging.info("Attempt to extract ext with ext4extract")
    could_extract_data = False
    try:
        sys.argv.extend([ext4_file_path])
        sys.argv.extend(['-D', extract_destination_folder])
        ext4extract_app().run()
        could_extract_data = True
    except Exception as err:
        logging.warning(err)
    return could_extract_data
