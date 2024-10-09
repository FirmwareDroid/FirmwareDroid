import logging
from extractor.mount_commands import mount_filesystem, copy_files_and_unmount


def erofs_extract(source_file_path, destination_dir):
    """
    Extract f2fs image from the given file. Checks first if the file contains the f2fs magic bytes.

    :param source_file_path: str - path to the .bin file.
    :param destination_dir: str - path where the file is extracted to.

    :return: boolean - True in case it was successfully extracted.
    """
    is_success = False
    try:
        is_mount_success, mount_point = mount_filesystem(source_file_path,
                                                         destination_dir,
                                                         filesystem_type="erofs")
        if is_mount_success:
            logging.debug(f"Successfully mounted {source_file_path} to {mount_point}")
            is_copy_success = copy_files_and_unmount(mount_point, destination_dir)
            if is_copy_success:
                is_success = True
    except Exception as e:
        logging.error(f"Error while extracting erofs file: {e}")
    return is_success






