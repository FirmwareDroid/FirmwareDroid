import logging
import os.path
import subprocess

PATH_LPUNPACK = "/opt/firmwaredroid/lpunpack/lpunpack.py"


def lpunpack_extractor(source_file_path, destination_dir):
    """
    Start the lpunpack extractor to convert a super.img into a directory with the extracted image files.

    Info: https://github.com/unix3dgforce/lpunpack

    :param destination_dir: str - path where the file is extracted to.
    :param source_file_path: str - path to the file.

    :return: boolean - True in case it was successfully extracted.
    """
    logging.info(f"Extracting with lpunpack: {source_file_path} to {destination_dir}")
    is_success = True
    try:
        if not os.path.exists(PATH_LPUNPACK):
            logging.error(f"Path to lpunpack not found: {PATH_LPUNPACK}")
            return False
        command = ["python3", PATH_LPUNPACK, source_file_path, destination_dir]
        response = subprocess.run(command,
                                  capture_output=True,
                                  text=True,
                                  timeout=3600,
                                  cwd=os.path.dirname(destination_dir))
        response.check_returncode()
    except subprocess.CalledProcessError as err:
        logging.warning(f"Command '{err.cmd}' returned non-zero exit status {err.returncode}.")
        logging.warning(f"Error output: {err.stderr}")
        is_success = False
    return is_success
