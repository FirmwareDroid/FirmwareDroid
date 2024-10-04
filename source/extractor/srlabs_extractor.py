import logging
import shlex
import subprocess

PYTHON_INTERPRETER_PATH = "/opt/firmwaredroid/srlabs_extractor/venv/bin/python3"
SRLABS_EXTRACTOR_PATH = "/opt/firmwaredroid/srlabs_extractor/extractor.py"


def ssrlabs_extractor(source_file_path, destination_dir, output_as_tar=True):
    """
    Start the SRLabs extractor to extract the firmware.

    Info:  https://github.com/srlabs/extractor

    :param output_as_tar: boolean - True in case the output should be a tar file.
    :param source_file_path: str - path to the file.
    :param destination_dir: str - path where the file is extracted to.

    :return: boolean - True in case it was successfully extracted.
    """
    is_success = True
    try:
        source_file_path = shlex.quote(source_file_path)
        destination_dir = shlex.quote(destination_dir)
        if output_as_tar:
            srlabs_args = [source_file_path, "--system-dir-output", destination_dir, "--tar-output"]
        else:
            srlabs_args = [source_file_path, "--system-dir-output", destination_dir]
        command = [PYTHON_INTERPRETER_PATH, SRLABS_EXTRACTOR_PATH] + srlabs_args
        response = subprocess.run(command, timeout=3600)
        response.check_returncode()
    except subprocess.CalledProcessError as err:
        logging.warning(err)
        is_success = False
    return is_success

