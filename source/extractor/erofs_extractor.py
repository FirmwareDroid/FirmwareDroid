import logging

from extractor.mount_commands import copy_files_and_unmount


def erofs_extract(source_file_path, destination_dir):
    """
    Extract f2fs image from the given file. Checks first if the file contains the f2fs magic bytes.

    :param source_file_path: str - path to the .bin file.
    :param destination_dir: str - path where the file is extracted to.

    :return: boolean - True in case it was successfully extracted.
    """
    is_success = False
    try:
        is_copy_success = copy_files_and_unmount(source_file_path, destination_dir)
        if is_copy_success:
            logging.info(f"Extracted erofs file to {destination_dir}")
            is_success = True
    except Exception as e:
        logging.error(f"Error while extracting erofs file: {e}")
    return is_success






