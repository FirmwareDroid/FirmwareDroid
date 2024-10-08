import logging
import subprocess
import tempfile


def copy_files_and_unmount(source_file_path, destination_dir):
    is_success = False
    with tempfile.TemporaryDirectory(dir=destination_dir) as mount_point:
        logging.debug(f"Mount point: {mount_point}")
        logging.debug(f"Destination directory: {destination_dir}")
        try:
            extract_dir = tempfile.mkdtemp(prefix="fmd_extract_", dir=destination_dir)
            cmd = ["sudo",
                   "/var/www/source/extractor/mount_copy.sh",
                   source_file_path,
                   mount_point,
                   extract_dir]
            logging.info(f"Run command: {cmd}")
            process = subprocess.run(cmd, capture_output=True, check=True)
            logging.info(f"stdout: {process.stdout}")
            logging.warning(f"stderr: {process.stderr.decode('utf-8')}")
            process.check_returncode()
            if process.returncode == 0:
                is_success = True
                logging.info(f"Successfully copied files from {source_file_path} to {extract_dir}")
        except subprocess.CalledProcessError as e:
            logging.warning(f"Output: {e.cmd} {e} {process.stderr}")


    return is_success
