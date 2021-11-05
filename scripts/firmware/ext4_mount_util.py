# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import shlex
import subprocess
import tempfile
import time
import traceback
import flask
from scripts.firmware.image_repair import attempt_repair, attempt_repair_and_resize


def mount_android_image(android_ext4_path, mount_folder_path):
    """
    Attempts to mount the given android image (only *.img) to the file system. Uses different mounting strategies to
    find a working configuration.

    :param android_ext4_path: str path to the image file to convert or mount.
    :param mount_folder_path: str path to the folder in which the partition will be mounted.

    """
    logging.info("Attempt to extract ext with mounting.")
    if is_path_mounted(android_ext4_path):
        exec_umount(android_ext4_path)

    is_mounted = False
    mount_option_list = ["ro,force,allow_other",
                         "ro,allow_other,default_permissions",
                         "ro,force,allow_other,defer_permissions",
                         "ro,allow_other,defer_permissions",
                         "ro,force,allow_other,default_permissions"]
    for mount_option in mount_option_list:
        if is_mounted:
            break
        if attempt_simg2img_mount(android_ext4_path, mount_folder_path, mount_option) \
                or attempt_ext4_mount(android_ext4_path, mount_folder_path, mount_option) \
                or attempt_fuse_ext4_mount(android_ext4_path, mount_folder_path, mount_option) \
                or attempt_repair_and_mount(android_ext4_path, mount_folder_path, mount_option) \
                or attempt_resize_and_mount(android_ext4_path, mount_folder_path, mount_option):
            if not has_files_in_folder(mount_folder_path):
                logging.warning("Overwrite chown of mount folders.")
                execute_chown(mount_folder_path)
                if has_files_in_folder(mount_folder_path):
                    is_mounted = True
                else:
                    logging.error(f"Mount error: Cannot access mounted files in {mount_folder_path}")
            else:
                is_mounted = True
                logging.info(f"Mount success: {android_ext4_path} to {mount_folder_path}")
        else:
            logging.warning(f"All mount attempts failed. Could not mount {android_ext4_path}")
    logging.info(f"Was file mounted? {is_mounted}")
    return is_mounted


def execute_chown(path):
    """
    Overtakes the ownership of a directory.

    :param path: str - path to the folder.

    """
    try:
        target_path = shlex.quote(str(path))
        for root, dir_list, file_list in os.walk(target_path):
            for directory in dir_list:
                os.chown(os.path.join(root, directory), os.geteuid(), os.getegid())
            for filename in file_list:
                os.chown(os.path.join(root, filename), os.geteuid(), os.getegid())
    except Exception as err:
        logging.warning(err)


def attempt_ext4_mount(source, target, mount_options):
    """
    Mounts an android ext4 image. If the image is not a raw ex SYSTEM IMAGE PATH ABSt4 it is converted with sim2img.

    :param mount_options: str - mount options flags.
    :param source: str - the file-path to be mounted.
    :param target: str - the destination path where the file will be mounted to.
    :return: bool - true if mount was successful.

    """
    logging.info(f"Attempt ext4 mount {source}")
    is_mounted = False
    try:
        exec_mount(source, target, mount_options)
        is_mounted = True
    except Exception as err:
        logging.info(err)
        # traceback.print_exc()
        if is_path_mounted(target):
            exec_umount(target)
    return is_mounted


def attempt_fuse_ext4_mount(source, target, mount_options):
    """
    Mount image with fuse kernel extension

    :param source: str - the file-path to be mounted.
    :param target: str - the destination path where the file will be mounted to.
    :param mount_options: str - mount options flags.
    :return: bool - true if mount was successful.

    """
    logging.info(f"Attempt fuse ext4 mount {source}")
    is_mounted = False
    try:
        exec_fuse_mount(source, target, mount_options)
        is_mounted = True
    except Exception as err:
        logging.info(err)
        # traceback.print_exc()
        if is_path_mounted(target):
            exec_umount(target)
    return is_mounted


def attempt_simg2img_mount(source, target, mount_options):
    """
    Converts the given image with simg2img and attempts to mount it.

    :param source: str - the file-path to be mounted.
    :param target: str - the destination path where the file will be mounted to.
    :param mount_options: str - mount options flags.
    :return: bool - true if mount was successful.

    """
    logging.info(f"Attempt simg2img mount {source}")
    is_mounted = False
    try:
        tempdir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
        ext4_raw_image_path = simg2img_convert_ext4(source, tempdir.name)
        if ext4_raw_image_path:
            try:
                exec_fuse_mount(ext4_raw_image_path, target, mount_options)
            except OSError:
                exec_mount(ext4_raw_image_path, target, mount_options)
            is_mounted = True
    except Exception as err:
        logging.info(err)
        if is_path_mounted(target):
            exec_umount(target)
    return is_mounted


def attempt_repair_and_mount(source, target, mount_options):
    """
    Attempts to repair the given source file.

    :param source: str - the file-path to be mounted.
    :param target: str - the destination path where the file will be mounted to.
    :param mount_options: str - mount options flags.
    :return: bool - true if mount was successful.

    """
    logging.info(f"Attempt repair and mount {source}")
    is_mounted = False
    try:
        temp_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
        repaired_source = attempt_repair(source, temp_dir.name)
        exec_mount(repaired_source, target, mount_options)
        is_mounted = True
    except Exception as err:
        logging.info(err)
        # traceback.print_exc()
        if is_path_mounted(target):
            exec_umount(target)
    return is_mounted


def attempt_resize_and_mount(source, target, mount_options):
    """
    Attempts to repair and resize the given source file.

    :param source: str - the file-path to be mounted.
    :param target: str - the destination path where the file will be mounted to.
    :param mount_options: str - mount options flags.
    :return: bool - true if mount was successful.

    """
    logging.info(f"Attempt repair, resize and mount {source}")
    is_mounted = False
    try:
        temp_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
        repaired_source = attempt_repair_and_resize(source, temp_dir.name)
        exec_mount(repaired_source, target, mount_options)
        is_mounted = True
    except Exception as err:
        logging.info(err)
        # traceback.print_exc()
        if is_path_mounted(target):
            exec_umount(target)
    return is_mounted


def simg2img_convert_ext4(android_ext4_path, destination_folder):
    """
    Unwrap Android's custom ext4 to a standard ext4 format with simg2img.

    :param android_ext4_path: the ext4 image-path which will be converted. For example, './somedir/system.img'
    :param destination_folder: the path to which the outputfile will be written.

    """
    try:
        output_file_name = "raw" + str(os.path.basename(android_ext4_path))
        output_file_name = shlex.quote(output_file_name)
        output_file_path = os.path.join(destination_folder, output_file_name)
        output_file_path = shlex.quote(output_file_path)
        response = subprocess.run(["simg2img", android_ext4_path, output_file_path], timeout=600)
        response.check_returncode()
        return output_file_path
    except subprocess.CalledProcessError as err:
        raise OSError(err)


def exec_mount(source, target, mount_options):
    """
    Executes mount command on the host with the given source to the target with read-only.

    :param mount_options: str - mount options flags.
    :param source: the file-path to be mounted.
    :param target: the destination path where the file will be mounted to.

    """
    try:
        source_path = shlex.quote(str(source))
        target_path = shlex.quote(str(target))
        response = subprocess.run(["mount", "-o", mount_options, source_path, target_path], timeout=600)
        response.check_returncode()
    except subprocess.CalledProcessError as err:
        raise OSError(err)


def exec_fuse_mount(source, target, mount_options):
    """
    Mount read-only with fuseext2.

    :param source: the file-path to be mounted.
    :param mount_options: str - mount options flags.
    :param target: the destination path where the file will be mounted to.

    """
    try:
        source_path = shlex.quote(str(source))
        target_path = shlex.quote(str(target))
        response = subprocess.run(["fuseext2", source_path, target_path, "-o", mount_options], timeout=600)
        response.check_returncode()
    except subprocess.CalledProcessError as err:
        raise OSError(err)


def exec_umount(mount_path):
    """
    Execute the linux umount command on the given path.

    :param mount_path: path of the folder to umount.

    """
    logging.info(f"Umount {mount_path}")
    try:
        mount_path = shlex.quote(str(mount_path))
        response = subprocess.run(["umount", "-f", mount_path], timeout=600)
        response.check_returncode()
        time.sleep(10)  # Let the filesystem process the umount
    except Exception as err:
        logging.info(err)
        traceback.print_exc()


def is_path_mounted(mount_path):
    """
    Checks if the path is already mounted.

    :param mount_path: str the directory path.

    """
    return os.path.ismount(mount_path)


def has_files_in_folder(mount_path):
    """
    Check if a folder contains any files.

    :param mount_path: str - path to check for readable files.
    :return: bool
    """
    return bool(os.listdir(mount_path))



