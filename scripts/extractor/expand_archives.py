import logging
import os
import re
from scripts.firmware.const_regex_patterns import SYSTEM_IMG_PATTERN_LIST
from model import FirmwareFile
from scripts.firmware.ext4_mount_util import mount_android_image, is_path_mounted, exec_umount
from scripts.extractor.nb0_extractor import extract_nb0
from scripts.extractor.pac_extractor import unpack_pac
from scripts.extractor.unzipper import extract_tar_file, unzip_file
from scripts.extractor.lz4_extractor import extract_lz4


def extract_all_nested(compressed_file_path, destination_dir, delete_compressed_file):
    """
    Decompress a zip/tar/lz4/pac/nb0 file and its contents recursively, including nested zip/tar/lz4 files.
    :param compressed_file_path: str - path to the compressed file.
    :param destination_dir: str - path to extract to.
    :param delete_compressed_file: boolean - if true, deletes the archive after it is extracted.
    :return:
    """
    # TODO make this function more secure - set maximal recursion depth
    if compressed_file_path.lower().endswith(".zip"):
        logging.info(f"Attempt to extract .zip file: {compressed_file_path}")
        unzip_file(compressed_file_path, destination_dir)
    elif compressed_file_path.lower().endswith(".tar") or compressed_file_path.endswith(".tar.md5"):
        logging.info(f"Attempt to extract .tar file: {compressed_file_path}")
        extract_tar_file(compressed_file_path, destination_dir)
    elif compressed_file_path.lower().endswith(".lz4"):
        logging.info(f"Attempt to extract lz4 file: {compressed_file_path}")
        extract_lz4(compressed_file_path, destination_dir)
    elif compressed_file_path.lower().endswith(".pac"):
        logging.info(f"Attempt to extract pac file: {compressed_file_path}")
        unpack_pac(compressed_file_path)
    elif compressed_file_path.lower().endswith(".nb0"):
        logging.info(f"Attempt to extract nb0 file: {compressed_file_path}")
        extract_nb0(compressed_file_path)
    try:
        if delete_compressed_file:
            os.remove(compressed_file_path)
    except FileNotFoundError:
        pass
    for root, dirs, files in os.walk(destination_dir):
        for filename in files:
            if re.search(r'\.zip$|\.tar$|\.tar\.md5$|\.lz4|\.pac|\.nb0', filename.lower()):
                nested_file_path = os.path.join(root, filename)
                if not os.path.exists(nested_file_path) and not nested_file_path.startswith("/"):
                    nested_file_path = "./" + nested_file_path
                extract_all_nested(nested_file_path, root, True)


@DeprecationWarning
def extract_and_mount_all(firmware, cache_path, mount_path):
    """
    Extracts the given firmware to a temporary directory and attempts to mount system.img file.
    :param cache_path: str - path of the temporary directory to work in.
    :param firmware: class:'AndroidFirmware' firmware file to mount files from.
    """
    # TODO REMOVE THIS METHOD
    extract_all_nested(compressed_file_path=firmware.absolute_store_path,
                       destination_dir=cache_path,
                       delete_compressed_file=False)
    has_mounted = False
    for system_pattern in SYSTEM_IMG_PATTERN_LIST:
        if has_mounted:
            break
        pattern = re.compile(system_pattern)
        firmware_file_list = FirmwareFile.objects(firmware_id_reference=firmware.id, name=pattern)
        for firmware_file in firmware_file_list:
            try:
                img_file_absolute_path = cache_path + firmware_file.relative_path
                mount_android_image(android_ext4_path=img_file_absolute_path,
                                    mount_folder_path=mount_path)
                logging.info(f"Mounted success: {img_file_absolute_path}")
                has_mounted = True
                break
            except (OSError, ValueError) as err:
                if is_path_mounted(mount_path):
                    exec_umount(mount_path)
                logging.warning(err)
    return has_mounted
