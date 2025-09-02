# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import filecmp
import logging
import os
import re
import shutil
import tempfile
import threading
from extractor.app_extractor import app_extractor
from extractor.bin_extractor.payload_dumper_go import payload_dumper_go_extractor
from extractor.binwalk_extractor import binwalk_extract
from extractor.ext4_extractor import extract_dat, extract_simg_ext4, extract_ext4
from extractor.lpunpack_extractor import lpunpack_extractor
from extractor.mount_extractor import mount_extract, simg2img_and_mount_extract
from extractor.nb0_extractor import extract_nb0
from extractor.pac_extractor import extract_pac
from extractor.unblob_extractor import unblob_extract
from extractor.unzipper import extract_tar, extract_zip, extract_gz
from extractor.lz4_extractor import extract_lz4
from extractor.brotli_extractor import extract_brotli
from firmware_handler.const_regex_patterns import EXT_IMAGE_PATTERNS_DICT
from firmware_handler.ext4_mount_util import run_simg2img_convert
from firmware_handler.firmware_file_indexer import create_firmware_file_list

EXTRACTION_SEMAPHORE = threading.Semaphore(20)
MAX_EXTRACTION_DEPTH = 10
SUPPORTED_FILE_TYPE_REGEX = r"(zip|tar|md5|lz4|pac|nb0|bin|br|dat|tgz|gz|app|rar|ozip|APP)$"
THIRD_LAYER_SUPPORT_FILE_TYPES = [".apex", ".capex"]
SKIP_FILE_PATTERN_LIST = ["[.]new[.]dat$", "[.]patch[.]dat$"]

EXTRACT_FUNCTION_MAP_DICT = {
    ".zip": [extract_zip],
    ".tar": [extract_tar],
    ".tgz": [extract_tar],
    ".gz": [extract_gz],
    ".md5": [extract_tar],
    ".lz4": [extract_lz4],
    ".pac": [extract_pac],
    ".nb0": [extract_nb0],
    ".bin": [payload_dumper_go_extractor],
    ".br": [extract_brotli],
    ".dat": [extract_dat],
    ".app": [app_extractor]
}

GENERIC_EXTRACT_FUNC_DICT = {
    "unblob": unblob_extract,
    "binwalk": binwalk_extract
}


def delete_file_safely(file_path):
    try:
        file_path = os.path.abspath(file_path)
        os.remove(file_path)
    except FileNotFoundError:
        logging.error(f"Error deleting - File not found: {file_path}")
        pass


def get_file_size_mb(file_path):
    size_in_bytes = os.path.getsize(file_path)
    size_in_mb = size_in_bytes / (1024 * 1024)
    return size_in_mb


def get_file_list(destination_dir):
    logging.info(f"Checking files in directory: {destination_dir}")
    if not os.path.exists(destination_dir):
        logging.error(f"Directory does not exist: {destination_dir}")
        return []

    file_list = []
    for root, dirs, files in os.walk(destination_dir, followlinks=False):
        for file in files:
            file_path = str(os.path.join(root, file))
            file_path_abs = os.path.abspath(file_path)
            if os.path.exists(file_path_abs):
                file_list.append(file_path_abs)
    return file_list


def match_filename_against_patterns(filename, patterns_dict):
    """
    Matches a filename against a dictionary of patterns.

    :param filename: str - filename to match.
    :param patterns_dict: regex patterns to match against.

    :return: bool - flag if the filename matches the patterns.
    """
    for pattern_list in patterns_dict.values():
        for pattern in pattern_list:
            file_extension = os.path.splitext(filename)[1].lower()
            if re.search(pattern, filename) and not re.search(SUPPORTED_FILE_TYPE_REGEX, file_extension):
                logging.info(f"Matched pattern: {pattern} for file: {filename}")
                return True
    return False


def is_partition_found(file_list):
    """
    Check if a main partition was found in the extracted archive.

    :param file_list: list(str) - file paths to check for.

    :return: bool - flag if the main partition was found.

    """
    has_partition = False
    for file in file_list:
        if match_filename_against_patterns(file, EXT_IMAGE_PATTERNS_DICT):
            has_partition = True
            break
    return has_partition


def has_extracted_all_supported_files(file_list):
    """
    Check if all supported files were extracted.

    :param file_list: list(str) - file paths to check for.

    :return: bool - flag if all supported files were extracted.

    """
    has_all_files = True
    for file in file_list:
        if not os.path.isfile(file):
            continue
        if re.search(SUPPORTED_FILE_TYPE_REGEX, file):
            has_all_files = False
            break
    logging.info(f"Has all files extracted: {has_all_files}")
    return has_all_files


def filter_supported_files(file_list):
    pattern = re.compile(SUPPORTED_FILE_TYPE_REGEX)
    filtered_list = [file for file in file_list if os.path.isfile(file) and pattern.search(file)]
    return filtered_list


def extract_first_layer(firmware_archive_file_path, destination_dir):
    """
    Extract the first layer of the firmware archive. Stops extracting when an Android partition (.img file) is found.

    :param firmware_archive_file_path: str - path to the firmware archive.
    :param destination_dir: str - path to the folder where the data is extracted to.

    :return: list(str) - list of paths to the extracted files.

    """
    file_list = extract_list_of_files([firmware_archive_file_path],
                                      destination_dir,
                                      delete_compressed_file=False,
                                      unblob_depth=1)
    logging.info(f"Extracted files count: {len(file_list)}")
    file_list = extract_support_file_types_recursively(file_list, destination_dir)
    return file_list


def extract_support_file_types_recursively(file_path_list, destination_dir):
    """
    Extract all supported file types recursively.

    :param file_path_list: list(str) - paths to the files to extract.
    :param destination_dir: str - path to the folder where the data is extracted to.

    :return: list(str) - list of paths to the extracted files.
    """
    file_list = filter_supported_files(file_path_list)
    logging.info(f"Filtered files count: {len(file_list)}")
    max_depth = 0
    while max_depth < MAX_EXTRACTION_DEPTH and has_extracted_all_supported_files(file_list) is False:
        try:
            logging.info(f"Checking for Android partition in the first layer depth: {max_depth} | "
                         f"File count: {len(file_list)}")
            file_list = extract_list_of_files(file_list,
                                              destination_dir,
                                              delete_compressed_file=True,
                                              unblob_depth=1)
            logging.info(f"Extracted files count: {len(file_list)}")
            filtered_file_list = filter_supported_files(file_list)
            logging.info(f"Filtered files count: {len(filtered_file_list)}")
            if len(filtered_file_list) > 0:
                file_list = filtered_file_list
        except Exception as err:
            logging.warning(err)
        finally:
            max_depth = max_depth + 1
    logging.info(f"First layer processing done. Depth: {max_depth}")
    return file_list


def get_raw_image(file_path_list):
    raw_image_path = None
    for file_path in file_path_list:
        if os.path.basename(file_path) == "raw.image":
            raw_image_path = file_path
    return raw_image_path


def extract_second_layer(firmware_archive_file_path, destination_dir, extracted_archive_dir_path, partition_name):
    firmware_archive_file_path = os.path.abspath(firmware_archive_file_path)
    destination_dir = os.path.abspath(destination_dir)
    firmware_file_list = []
    logging.info(f"Extracting all layers of the firmware archive: {firmware_archive_file_path}")
    is_success = False
    if partition_name == "super":
        super_extract_dir = tempfile.mkdtemp(dir=extracted_archive_dir_path, prefix="fmd_extract_super_")
        super_extract_dir = os.path.abspath(super_extract_dir)
        is_success = lpunpack_extractor(firmware_archive_file_path, super_extract_dir)
        if is_success:
            logging.info("Successfully extracted super image.")
            shutil.copytree(super_extract_dir, extracted_archive_dir_path, dirs_exist_ok=True,
                            symlinks=True,
                            ignore_dangling_symlinks=True)
            dst_dir_path = os.path.join(extracted_archive_dir_path, os.path.basename(super_extract_dir))
            logging.info(f"Extracted super image to: {dst_dir_path}")
            firmware_file_list = create_firmware_file_list(dst_dir_path, partition_name)
    if not is_success:
        extract_image_file(firmware_archive_file_path, destination_dir)
        remove_fmd_temp_directories(destination_dir)
        firmware_file_list = create_firmware_file_list(destination_dir, partition_name)
    return firmware_file_list


def extract_third_layer(firmware_file_list, destination_dir, extracted_archive_dir_path, partition_name):
    """
    Extract firmware files within the firmware itself (third layer).

    :param destination_dir: str - path to the directory where the data is extracted to.
    :param firmware_file_list: list(class:"FirmwareFile") - list of firmware files to extract.
    :param extracted_archive_dir_path: str - path to the directory where the extracted files are stored.
    :param partition_name: str - name of the partition.

    :return: list(class:"FirmwareFile") - list of extracted firmware files.
    """
    logging.info(f"Extracting third layer of the firmware archive: {len(firmware_file_list)} files")
    all_firmware_files_extracted_list = []
    for firmware_file in firmware_file_list:
        if not firmware_file.is_directory and (any([firmware_file.name.endswith(file_extension)
                                                    for file_extension in THIRD_LAYER_SUPPORT_FILE_TYPES])):
            logging.info(f"Extracting third layer for: {firmware_file.name}")
            if (os.path.isfile(firmware_file.absolute_store_path)
                    and not os.path.islink(firmware_file.absolute_store_path)):
                apex_file_name_no_ext = os.path.basename(firmware_file.absolute_store_path).replace(".", "_")

                sub_extract_folder = str(os.path.join(str(destination_dir), str(apex_file_name_no_ext)))
                os.makedirs(sub_extract_folder, exist_ok=True)

                apex_extract_dir = tempfile.mkdtemp(dir=sub_extract_folder,
                                                    prefix=f"fmd_extract_{apex_file_name_no_ext}_")
                apex_extract_dir = os.path.abspath(apex_extract_dir)
                file_extension = os.path.splitext(firmware_file.absolute_store_path)[1].lower()
                if file_extension == ".capex":
                    is_success = unblob_extract(firmware_file.absolute_store_path,
                                                apex_extract_dir,
                                                depth=2,
                                                allow_extension_list=THIRD_LAYER_SUPPORT_FILE_TYPES)
                else:
                    is_success = unblob_extract(firmware_file.absolute_store_path,
                                                apex_extract_dir,
                                                depth=1,
                                                allow_extension_list=THIRD_LAYER_SUPPORT_FILE_TYPES)
                if is_success:
                    file_path_list = get_file_list(apex_extract_dir)
                    for file_path in file_path_list:
                        file_name = os.path.basename(file_path).lower().strip()
                        if file_name.endswith(".img"):
                            apex_payload_extract_dir = tempfile.mkdtemp(dir=sub_extract_folder,
                                                                        prefix=f"fmd_extract_apex_payload_{apex_file_name_no_ext}_")
                            subfolder_path = str(apex_file_name_no_ext) + "/"
                            apex_payload_extract_dir = os.path.abspath(apex_payload_extract_dir)
                            apex_payload_extract_dir = os.path.join(apex_payload_extract_dir, subfolder_path)
                            os.makedirs(apex_payload_extract_dir, exist_ok=True)
                            logging.info(f"Third layer extraction for: {file_name}, to: {apex_payload_extract_dir}")
                            unblob_extract(file_path,
                                           apex_payload_extract_dir,
                                           depth=1,
                                           )

                remove_fmd_temp_directories(destination_dir)
                firmware_file_list = create_firmware_file_list(destination_dir, partition_name)
                all_firmware_files_extracted_list.extend(firmware_file_list)
    return all_firmware_files_extracted_list


def attempt_sparse_img_convertion(android_sparse_img_path, destination_dir):
    is_success = False
    raw_image_path = None
    try:
        raw_image_path = run_simg2img_convert(android_sparse_img_path, destination_dir)
        is_success = True
    except Exception as err:
        logging.debug(err)
    return is_success, raw_image_path


def remove_fmd_temp_directories(search_path):
    """
    Deletes all temporary directories with a prefix of "fmd_extract_" and moves the files one level up.

    :param search_path: str - path to the directory to search in.

    """
    for root, dirs, files in os.walk(search_path, followlinks=False):
        for directory in dirs:
            if directory.startswith("fmd_extract_") \
                    and os.path.isdir(os.path.join(root, directory)) \
                    and os.path.isdir(root):
                temp_extract_dir = os.path.join(root, directory)
                move_all_files_and_folders(temp_extract_dir, root)
                logging.info(f"Removing temporary directory: {temp_extract_dir}")
                shutil.rmtree(temp_extract_dir, ignore_errors=True)


def extract_image_file(image_path, extract_dir_path):
    image_path = os.path.abspath(image_path)
    extract_dir_path = os.path.abspath(extract_dir_path)
    logging.info(f"Attempt to extract image: {image_path} to: {extract_dir_path}")
    if extract_simg_ext4(image_path, extract_dir_path):
        logging.debug("Image extraction successful with simg_ext4extractor")
    elif extract_ext4(image_path, extract_dir_path):
        logging.debug("Image extraction successful with ext4extractor")
    elif mount_extract(image_path, extract_dir_path):
        logging.debug("Image extraction successful with mount extractor")
    elif simg2img_and_mount_extract(image_path, extract_dir_path):
        logging.debug("Image extraction successful with simg2img and mount extractor")
    elif binwalk_extract(image_path, extract_dir_path):
        logging.debug("Image extraction successful with binwalk extraction suite")
    elif unblob_extract(image_path, extract_dir_path, depth=25):
        logging.debug("Image extraction successful with unblob extraction suite")
    else:
        raise RuntimeError(f"Could not extract data from image: {image_path} Maybe unknown format or mount error.")


def extract_list_of_files(file_path_list,
                          destination_dir,
                          delete_compressed_file,
                          unblob_depth=1):
    """
    Extract the compressed file to the destination directory.

    :param file_path_list: list(str) - paths to be processed.
    :param destination_dir: str - path to the folder where the data is extracted to.
    :param delete_compressed_file: bool - delete the compressed file after extraction.
    :param unblob_depth: int - depth of unblob extraction.

    :return: list(str) - list of paths to the extracted files.
    """
    extracted_files_path_list = []
    for file_path in file_path_list:
        if not os.path.exists(file_path):
            logging.warning(f"File does not exist: {file_path}")
            continue
        if os.path.isfile(file_path):
            with EXTRACTION_SEMAPHORE:
                extracted_files_for_current_path = process_single_file_path(file_path,
                                                                            destination_dir,
                                                                            delete_compressed_file,
                                                                            unblob_depth)
                for extract_file_path in extracted_files_for_current_path:
                    if os.path.exists(extract_file_path):
                        extracted_files_path_list.append(extract_file_path)

    return extracted_files_path_list


def process_directory(current_path, queue, failed_extractions, processed_files):
    for filename in os.listdir(current_path):
        next_path = os.path.join(current_path, filename)
        if next_path not in failed_extractions and next_path not in processed_files:
            queue.append(next_path)


def move_all_files_and_folders(src_dir, dest_dir):
    """
    Move all files and folders from src_dir to dest_dir.

    :param src_dir: str - path to the source directory.
    :param dest_dir: str - path to the destination directory.
    """
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir)

    if not os.path.isdir(dest_dir) or not os.path.isdir(src_dir):
        raise ValueError(f"Destination and source must be a directory. Src: {src_dir}, Dest: {dest_dir}")

    if not dest_dir.endswith(os.sep):
        dest_dir += os.sep

    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dest_item = os.path.join(dest_dir, item)
        logging.debug(f"Moving: {src_item} to {dest_item}")
        try:
            if os.path.exists(dest_item) and not filecmp.cmp(src_item, dest_item, shallow=False):
                dest_item = os.path.join(dest_dir, f"1_{item}")
            shutil.move(src_item, dest_item)
            if not os.path.exists(dest_item):
                logging.error(f"Move failed: {src_item} to {dest_item}")
        except Exception as err:
            logging.error(err)


def process_file(current_path,
                 destination_dir,
                 unblob_depth,
                 delete_compressed_file):
    filename = os.path.basename(current_path)
    file_extension = os.path.splitext(current_path.lower())[1].lower()
    is_success = False

    if file_extension is None or file_extension == "":
        logging.info(f"File extension is None for: {current_path}. Assuming zip file...")
        file_extension = ".zip"

    if file_extension in EXTRACT_FUNCTION_MAP_DICT.keys():
        for extraction_function in EXTRACT_FUNCTION_MAP_DICT[file_extension]:
            temp_extract_dir = tempfile.mkdtemp(dir=destination_dir,
                                                prefix=f"fmd_extract_{extraction_function.__name__}_")
            temp_extract_dir = os.path.abspath(temp_extract_dir)
            try:
                logging.info(f"Extracting with: {extraction_function.__name__} {current_path} {temp_extract_dir} ")
                is_success = extraction_function(current_path, temp_extract_dir)
                if is_success:
                    move_all_files_and_folders(temp_extract_dir, destination_dir)
                    break
            finally:
                shutil.rmtree(temp_extract_dir, ignore_errors=True)

    is_generic_extract_success = False
    if not is_success and any([filename.endswith(pattern) for pattern in SKIP_FILE_PATTERN_LIST]):
        temp_extract_dir = tempfile.mkdtemp(dir=destination_dir, prefix="fmd_extract_unblob_")
        temp_extract_dir = os.path.abspath(temp_extract_dir)
        for name, generic_extraction_function in GENERIC_EXTRACT_FUNC_DICT.items():
            if name == "binwalk":
                logging.info(f"Extracting with binwalk: {current_path} {temp_extract_dir} ")
                args = {"compressed_file_path": current_path,
                        "destination_dir": temp_extract_dir}
            else:
                logging.info(f"Extracting with unblob: {current_path} {temp_extract_dir} ")
                args = {"compressed_file_path": current_path,
                        "destination_dir": temp_extract_dir,
                        "depth": unblob_depth}
            is_generic_extract_success = generic_extraction_function(**args)
            if is_generic_extract_success:
                move_all_files_and_folders(temp_extract_dir, destination_dir)
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                break

    if delete_compressed_file and (is_success or is_generic_extract_success):
        logging.info(f"Success extracting. Deleting compressed file: {current_path}")
        delete_file_safely(current_path)
    elif is_success or is_generic_extract_success:
        logging.info(f"Extraction successful for: {current_path}")
    else:
        logging.warning(f"Expand Archive: Extraction failed for: {current_path}")
        if not current_path.endswith(".failed"):
            new_file_location = current_path + ".failed"
            shutil.move(current_path, new_file_location)
        else:
            logging.warning(f"File already marked as failed, likely some config error in "
                            f"the extensions allowed to extract: {current_path}")


def process_single_file_path(file_path,
                             destination_dir,
                             delete_compressed_file,
                             unblob_depth=1):
    file_path = os.path.abspath(file_path)
    destination_dir = os.path.abspath(destination_dir)
    logging.info(f"Extracting: {file_path}, destination: {destination_dir}, delete: {delete_compressed_file}")
    process_file(file_path, destination_dir, unblob_depth, delete_compressed_file)
    logging.info(f"Extraction finished for: {file_path}")

    extracted_file_list = get_file_list(destination_dir)
    logging.info(f"Extracted files: {len(extracted_file_list)}")
    return extracted_file_list
