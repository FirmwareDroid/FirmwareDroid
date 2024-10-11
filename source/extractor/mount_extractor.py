import logging
import os
from extractor.mount_commands import copy_files_and_unmount


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
            for item in os.listdir(destination_dir):
                if os.path.isfile(os.path.join(destination_dir, item)):
                    logging.info(f"Extracted files to {destination_dir}")
                    is_success = True
                    break
    except Exception as e:
        logging.error(f"Error while extracting f2fs file: {e}")
        is_success = False
    return is_success




