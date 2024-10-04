import logging
import os.path
import shlex
import subprocess

PATH_PAYLOAD_DUMPER_GO = "/opt/firmwaredroid/payload_dumper-go/payload-dumper-go"

def payload_dumper_go_extractor(source_file_path, destination_dir):
    """
    Start the payload dumper to extract .bin firmware.

    Info: https://github.com/ssut/payload-dumper-go

    :param destination_dir: str - path where the file is extracted to.
    :param source_file_path: str - path to the file.

    :return: boolean - True in case it was successfully extracted.
    """
    logging.info("Extracting firmware with payload dumper go.")
    is_success = True
    try:
        source_file_path = shlex.quote(source_file_path)
        destination_dir = shlex.quote(destination_dir)
        if not os.path.exists(PATH_PAYLOAD_DUMPER_GO):
            logging.error(f"Path to payload dumper go not found: {PATH_PAYLOAD_DUMPER_GO}")
            return False
        command = [PATH_PAYLOAD_DUMPER_GO, source_file_path, "-output", destination_dir]
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
