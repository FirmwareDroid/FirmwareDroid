# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import shlex
import subprocess
from pathlib import Path
from firmware_handler.const_regex_patterns import SYSTEM_TRANSFER_PATTERN_LIST, VENDOR_TRANSFER_PATTERN_LIST, \
    OEM_TRANSFER_PATTERN_LIST, USERDATA_TRANSFER_PATTERN_LIST, PRODUCT_TRANSFER_PATTERN_LIST, \
    SYSTEM_EXT_TRANSFER_PATTERN_LIST, SYSTEM_OTHER_TRANSFER_PATTERN_LIST, VENDOR_DAT_PATCH_PATTERN_LIST, \
    OEM_DAT_PATCH_PATTERN_LIST, USERDATA_DAT_PATCH_PATTERN_LIST, PRODUCT_DAT_PATCH_PATTERN_LIST, \
    SYSTEM_EXT_DAT_PATCH_PATTERN_LIST, SYSTEM_OTHER_DAT_PATCH_PATTERN_LIST, SYSTEM_DAT_PATCH_PATTERN_LIST
from firmware_handler.firmware_file_search import find_file_path_by_regex


PATCH_TOOL_PATH_V03 = "./tools/imgpatchtool/IMG_Patch_Tools_0.3/BlockImageUpdate"
PATCH_TOOL_PATH_2022 = "./tools/imgpatchtool/2022_16_06/BlockImageUpdate"


def convert_dat2img(dat_file_path, destination_path):
    """
    Convert .dat file to an .img file and store it in the destination path.

    :param dat_file_path: str - path to the .dat file
    :param destination_path: str - path where the .img file will be stored

    :return: str - path to the converted .img file.

    """
    if not dat_file_path.endswith("dat"):
        raise AssertionError(f"Only .dat file-type supported. {dat_file_path}")

    path = Path(dat_file_path)
    filename = os.path.basename(dat_file_path)
    if "patch" not in filename and not filename.startswith("._"):
        search_folder_path = path.parent.absolute()
        transfer_file_path, patch_file_path = search_transfer_list(search_folder_path, filename)
        if transfer_file_path is not None:
            out_filename = filename.replace(".dat", "dat.conv.img")
            img_file_path = os.path.join(destination_path, out_filename)
            start_dat_conversion(dat_file_path, transfer_file_path, img_file_path)
            logging.info(f"Converted dat: {dat_file_path} to img: {img_file_path}")
            if patch_file_path is not None:
                patch_dat_image(dat_file_path, img_file_path, transfer_file_path, patch_file_path)
        else:
            raise AssertionError("Could not find system.file.list")
    else:
        raise AssertionError("Skip and continue. Ignore specific dat file.")
    return img_file_path


def search_transfer_list(search_path, filename):
    """
    Searches in the directory for a system transfer file and patch file.
    :return: str - path of the system.transfer.list if found
    """
    transfer_pattern_list = None
    patch_pattern_list = None

    if "vendor" in filename:
        transfer_pattern_list = VENDOR_TRANSFER_PATTERN_LIST
        patch_pattern_list = VENDOR_DAT_PATCH_PATTERN_LIST
    elif "oem" in filename:
        transfer_pattern_list = OEM_TRANSFER_PATTERN_LIST
        patch_pattern_list = OEM_DAT_PATCH_PATTERN_LIST
    elif "userdata" in filename:
        transfer_pattern_list = USERDATA_TRANSFER_PATTERN_LIST
        patch_pattern_list = USERDATA_DAT_PATCH_PATTERN_LIST
    elif "product" in filename:
        transfer_pattern_list = PRODUCT_TRANSFER_PATTERN_LIST
        patch_pattern_list = PRODUCT_DAT_PATCH_PATTERN_LIST
    elif "system_ext" in filename:
        transfer_pattern_list = SYSTEM_EXT_TRANSFER_PATTERN_LIST
        patch_pattern_list = SYSTEM_EXT_DAT_PATCH_PATTERN_LIST
    elif "system_other" in filename:
        transfer_pattern_list = SYSTEM_OTHER_TRANSFER_PATTERN_LIST
        patch_pattern_list = SYSTEM_OTHER_DAT_PATCH_PATTERN_LIST
    elif "system" in filename:
        transfer_pattern_list = SYSTEM_TRANSFER_PATTERN_LIST
        patch_pattern_list = SYSTEM_DAT_PATCH_PATTERN_LIST

    if transfer_pattern_list is None:
        raise RuntimeError(f"Unknown transfer list for partition: {filename}")
    return find_file_path_by_regex(search_path, transfer_pattern_list), find_file_path_by_regex(search_path,
                                                                                                patch_pattern_list)


def patch_dat_image(dat_file_path, img_file_path, transfer_file_path, patch_file_path):
    """
    Patch an .img file from .dat image in place for OTA images.

    :param patch_file_path: str - file path of the *.patch.dat file.
    :param transfer_file_path: str - file path of the *.transfer.list file.
    :param img_file_path: str - file path of the .img file to modify inplace.
    :param dat_file_path: str - file path of the .dat file.


    """
    logging.info(f"Patch file {img_file_path} \nwith {dat_file_path} \nand {transfer_file_path} \nand "
                 f"{patch_file_path}")
    try:
        transfer_file_path = shlex.quote(str(transfer_file_path))
        patch_file_path = shlex.quote(str(patch_file_path))
        dat_file_path = shlex.quote(str(dat_file_path))
        img_file_path = shlex.quote(str(img_file_path))
        # TODO Remove constant path and tool
        response = subprocess.run([PATCH_TOOL_PATH_2022,
                                   img_file_path,
                                   transfer_file_path,
                                   dat_file_path,
                                   patch_file_path], timeout=900)
        response.check_returncode()
        logging.info(f"BlockImageUpdate Patch successful: {img_file_path}")
    except subprocess.CalledProcessError as err:
        raise OSError(err)


def rangeset(src):
    """
    Creates a range tuple for the given source list.
    :param src: list(str) - command list
    :return: ([int], [int])
    """
    src_set = src.split(',')
    num_set = [int(item) for item in src_set]
    if len(num_set) != num_set[0] + 1:
        logging.error(f"Error on parsing following data to rangeset:\n{src}")

    return tuple([(num_set[i], num_set[i + 1]) for i in range(1, len(num_set), 2)])


def parse_transfer_list_file(transfer_list_file_path):
    """
    Parse system.transfer.file content.
    :param transfer_list_file_path:
    :return: int, int, list(str) - version, number of new blocks, list of commands
    """
    trans_list = open(transfer_list_file_path, 'r')

    # First line in transfer list is the version number
    version = int(trans_list.readline())

    # Second line in transfer list is the total number of blocks we expect to write
    new_blocks = int(trans_list.readline())

    if version >= 2:
        # Third line is how many stash entries are needed simultaneously
        trans_list.readline()
        # Fourth line is the maximum number of blocks that will be stashed simultaneously
        trans_list.readline()

    # Subsequent lines are all individual transfer command_list
    command_list = []
    for line in trans_list:
        line = line.split(' ')
        cmd = line[0]
        if cmd in ['erase', 'new', 'zero']:
            command_list.append([cmd, rangeset(line[1])])
        else:
            # Skip lines starting with numbers, they are not command_list anyway
            if not cmd[0].isdigit():
                logging.error(f"Command {cmd} is invalid.")
                break

    trans_list.close()
    return version, new_blocks, command_list


def start_dat_conversion(input_dat_file_path, system_transfer_list_file_path, output_img_file_path):
    """
    Converts .dat to .img file.

    :param input_dat_file_path: str - path to the .dat to convert.
    :param system_transfer_list_file_path: str - path to the transfer file list.
    :param output_img_file_path: str - path where the .img will be created.


    """
    block_size = 4096
    version, new_blocks, commands = parse_transfer_list_file(system_transfer_list_file_path)
    try:
        output_img = open(output_img_file_path, 'wb')
    except IOError as e:
        logging.error(e)
        raise

    new_data_file = open(input_dat_file_path, 'rb')
    all_block_sets = [i for command in commands for i in command[1]]
    max_file_size = int(max(pair[1] for pair in all_block_sets) * block_size)

    for command in commands:
        if command[0] == 'new':
            for block in command[1]:
                begin = int(block[0])
                end = int(block[1])
                block_count = end - begin
                logging.info(f"Copying {block_count} blocks into position {begin}...")

                # Position output file
                output_img.seek(begin * block_size)

                # Copy one block at a time
                while block_count > 0:
                    output_img.write(new_data_file.read(block_size))
                    block_count -= 1
        else:
            logging.info(f"Skipping command {command[0]}...")

    # Make file larger if necessary
    if output_img.tell() < max_file_size:
        output_img.truncate(max_file_size)

    output_img.close()
    new_data_file.close()
