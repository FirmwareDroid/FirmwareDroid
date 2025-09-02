import os
import subprocess
import logging


def binwalk_extract(compressed_file_path,
                    destination_dir):
    os.makedirs(destination_dir, exist_ok=True)
    try:
        command = ['binwalk', '-C', destination_dir, '-M', '-e', compressed_file_path]
        logging.debug(f"Running Binwalk with command: {command}")
        response = subprocess.run(command, timeout=60 * 60 * 3)
        response.check_returncode()
        is_success = True
    except Exception as e:
        is_success = False
        logging.debug(f"An error occurred while running binwalk: {e}")
    logging.debug(f"Binwalk extraction is_success: {is_success} for file {compressed_file_path}")
    return is_success
