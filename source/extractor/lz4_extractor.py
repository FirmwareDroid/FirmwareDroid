# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os


def extract_lz4(lz4_file_path, destination_dir):
    """
    Extracts the given Lz4 files to the destination dir.
    Name of the output file is the input file without the .lz4 extension.

    :param lz4_file_path: str - path to the *.lz4 file.
    :param destination_dir: str - path to extract the *.lz4 to.

    :return: boolean - True in case it was successfully extracted.
    """
    import lz4framed
    from _lz4framed import Lz4FramedNoDataError
    is_success = True
    logging.info(f"Extracting lz4 file: {lz4_file_path} to {destination_dir}")
    try:
        with open(lz4_file_path, 'rb') as lz4_file_bytes:
            decoded = []
            try:
                for chunk in lz4framed.Decompressor(lz4_file_bytes):
                    decoded.append(chunk)
            except Lz4FramedNoDataError as error:
                logging.exception(str(error))
        output_file_name = os.path.basename(lz4_file_path).replace(".lz4", "")
        output_file_path = str(os.path.join(str(destination_dir), str(output_file_name)))
        with open(output_file_path, "wb") as output_file:
            for chunk in decoded:
                output_file.write(chunk)
        logging.info("Extraction of lz4 file finished: " + output_file_path)
    except Exception as err:
        is_success = False
        logging.warning(str(err))
    return is_success
