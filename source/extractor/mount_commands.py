import logging
import subprocess
import tempfile
import os


def mount_filesystem(source_file_path, destination_dir, filesystem_type):
    is_success = False
    tmp_mount_dir = None

    if not os.path.isfile(source_file_path):
        logging.error(f"Source file does not exist: {source_file_path}")
        return is_success

    if not os.path.isdir(destination_dir):
        logging.error(f"Destination directory does not exist: {destination_dir}")
        return is_success

    try:
        tmp_mount_dir = tempfile.mkdtemp(dir=destination_dir)
        if os.path.exists(tmp_mount_dir):
            cmd = ["mount", "-t", filesystem_type, "-o", "loop", source_file_path, tmp_mount_dir]
            result = subprocess.run(cmd, capture_output=True, check=True)
            result.check_returncode()
            is_success = True
        else:
            raise ValueError(f"Could not create temporary mount directory: {tmp_mount_dir}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while mounting {filesystem_type} file: {e}")
    return is_success, tmp_mount_dir


def copy_files_and_unmount(mount_point, destination_dir):
    is_success = False
    if not os.path.isdir(mount_point):
        logging.error(f"Mount point does not exist: {mount_point}")
        return is_success

    if not os.path.isdir(destination_dir):
        logging.error(f"Destination directory does not exist: {destination_dir}")
        return is_success

    try:
        cmd = ["cp", "-r", f"{mount_point}/.", destination_dir]
        subprocess.run(cmd, capture_output=True, check=True)
        cmd = ["umount", mount_point]
        subprocess.run(cmd, capture_output=True, check=True)
        is_success = True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error while copying files and unmounting: {e}")
    return is_success
