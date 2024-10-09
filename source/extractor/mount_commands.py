import logging
import subprocess
import tempfile
import os


def mount_filesystem(source_file_path, destination_dir, filesystem_type, mount_options=None):
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
            if filesystem_type:
                cmd = ["sudo", "mount", "-t", filesystem_type]
            else:
                cmd = ["sudo", "mount"]

            if mount_options:
                cmd.extend(["-o", mount_options])

            cmd += [source_file_path, tmp_mount_dir]
            logging.debug(f"Mounting {source_file_path} to {tmp_mount_dir}: {cmd}")
            result = subprocess.run(cmd, capture_output=True, check=True)
            result.check_returncode()
            if result.returncode == 0:
                is_success = True
        else:
            raise ValueError(f"Could not create temporary mount directory: {tmp_mount_dir}")
    except subprocess.CalledProcessError as err:
        logging.warning(f"Error while mounting {filesystem_type} file: {err}")
        logging.warning(f"Error output: {err.stderr.decode()}")
    return is_success, tmp_mount_dir


def copy_files_and_unmount(mount_point, destination_dir):
    is_success = False

    if os.path.isdir(mount_point) and os.path.isdir(destination_dir):
        try:
            if os.listdir(mount_point):
                extract_dir = tempfile.mkdtemp(dir=destination_dir)
                copy_result = subprocess.run(["sudo", "/bin/cp", "-Ra",
                                              mount_point,
                                              extract_dir],
                                             capture_output=True,
                                             check=True)
                copy_result.check_returncode()
                if copy_result.returncode == 0:
                    chown_result = subprocess.run(["sudo", "chown", "-R", "www:www", extract_dir],
                                                  capture_output=True, check=True)
                    chown_result.check_returncode()
                    if chown_result.returncode == 0:
                        logging.debug(f"Successfully copied files from {mount_point} to {extract_dir}")

                        cmd = ["sudo", "umount", mount_point]
                        result = subprocess.run(cmd, capture_output=True, check=True)
                        result.check_returncode()
                        if result.returncode == 0:
                            logging.debug(f"Successfully unmounted {mount_point}")
                            is_success = True
        except subprocess.CalledProcessError as e:
            logging.error(f"Error while copying files and unmounting: {e}")
            logging.error(f"Error output: {e.stderr.decode()}")
    else:
        if not os.path.isdir(mount_point):
            logging.error(f"Mount point does not exist: {mount_point}")
        if not os.path.isdir(destination_dir):
            logging.error(f"Destination directory does not exist: {destination_dir}")

    return is_success
