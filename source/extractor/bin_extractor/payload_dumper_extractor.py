import logging
import shlex
import subprocess

PYTHON_INTERPRETER_PATH = "/opt/firmwaredroid/payload_dumper/venv/bin/python3"
PAYLOAD_DUMPER_EXTRACTOR_PATH = "/opt/firmwaredroid/payload_dumper/payload_dumper.py"


def payload_dumper_extractor(source_file_path, destination_dir):
    """
    Start the payload dumper to extract .bin firmware.

    Info:  ttps://github.com/vm03/payload_dumper/tree/master

    :param destination_dir: str - path where the file is extracted to.
    :param source_file_path: str - path to the file.

    :return: boolean - True in case it was successfully extracted.
    """
    logging.info("Extracting firmware with payload dumper.")
    is_success = True
    try:
        source_file_path = shlex.quote(source_file_path)
        destination_dir = shlex.quote(destination_dir)
        command = [PYTHON_INTERPRETER_PATH, PAYLOAD_DUMPER_EXTRACTOR_PATH, source_file_path, "--out", destination_dir]
        response = subprocess.run(command, timeout=3600)
        response.check_returncode()
        if response.returncode != 0:
            is_success = False
    except subprocess.CalledProcessError as err:
        logging.warning(f"Command '{err.cmd}' returned non-zero exit status {err.returncode}.")
        logging.warning(f"Error output: {err.stderr}")
        is_success = False
    return is_success
