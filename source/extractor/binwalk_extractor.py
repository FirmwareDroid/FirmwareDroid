import os
import subprocess
import logging
from extractor.unblob_extractor import SKIP_EXTENSION_DEFAULT

def binwalk_extract(compressed_file_path,
                    destination_dir,
                    recursive_extraction=False,
                    skip_extensions_list=None):
    os.makedirs(destination_dir, exist_ok=True)
    if skip_extensions_list is None:
        skip_extensions_list = SKIP_EXTENSION_DEFAULT
    try:
        command = ['binwalk', '-C', destination_dir]
        if recursive_extraction:
            command += ['-M']
        command += ['-e', compressed_file_path]
        for ext in skip_extensions_list:
            command += ['--exclude', ext]
        logging.debug(f"Running Binwalk with command: {command}")
        response = subprocess.run(command, timeout=60 * 60 * 3)
        response.check_returncode()
        is_success = True
    except Exception as e:
        is_success = False
        logging.debug(f"An error occurred while running binwalk: {e}")
    logging.debug(f"Binwalk extraction is_success: {is_success} for file {compressed_file_path}")
    return is_success
