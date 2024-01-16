# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import shlex
import subprocess
from pathlib import Path


def extract_brotli(source_file_path, destination_dir):
    """
    Extract brotli (.br) compressed files.

    :param source_file_path: str - path to the .bin file.
    :param destination_dir: str - path where the file is extracted to.

    :return: boolean - True in case it was successfully extracted.
    """
    is_success = True
    try:
        source_file_path = shlex.quote(source_file_path)
        filename = Path(source_file_path)
        filename = os.path.basename(filename)
        filename = filename.replace(".br", "")
        destination_dir = shlex.quote(destination_dir)
        output_file = os.path.join(destination_dir, filename)
        response = subprocess.run(["brotli", "--decompress", source_file_path, "-o", output_file], timeout=600)
        response.check_returncode()
        if os.path.exists(output_file):
            logging.info(f"Brotli successfully decompressed: {output_file}")
        else:
            raise FileNotFoundError(f"Could not decompress brotli: {source_file_path} - missing file: {output_file}")
    except subprocess.CalledProcessError as err:
        logging.warning(err)
        is_success = False
    return is_success
