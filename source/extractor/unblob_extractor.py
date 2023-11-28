import logging
import os
import shlex
import subprocess

# TODO Wait for https://github.com/onekey-sec/unblob/issues/647 and then refactor
SKIP_MAGIC_DEFAULT = ["BFLT",
                      "JPEG",
                      "JFIF",
                      "JPG",
                      "GIF",
                      "TTF",
                      "PNG",
                      "SQLite",
                      "compiled Java class",
                      "TrueType Font data",
                      "PDF document",
                      "magic binary file",
                      "MS Windows icon resource",
                      "PE32",
                      "Web Open Font Format",
                      "GNU message catalog",
                      "Xilinx BIT data",
                      "Microsoft Excel",
                      "Microsoft Word",
                      "Microsoft PowerPoint",
                      "Microsoft OOXML",
                      "OpenDocument",
                      "Macromedia Flash data",
                      "MPEG",
                      "HP Printer Job Language",
                      "Erlang BEAM file",
                      "python",  # (e.g. python 2.7 byte-compiled)
                      "Composite Document File V2 Document",
                      "Windows Embedded CE binary image"]
SKIP_MAGIC_ANDROID = ["Android", "Java", "Font"]
SKIP_MAGIC_FIRMWAREDROID_STRING = ','.join(SKIP_MAGIC_DEFAULT + SKIP_MAGIC_ANDROID)


def unblob_extract(compressed_file_path, destination_dir, delete_compressed_file=False):
    """
    Extract files with the unblob extraction suite.

    :return: boolean - True in case it was successfully extracted.

    """
    is_success = True
    response = None
    try:
        input_file = shlex.quote(compressed_file_path)
        output_dir = shlex.quote(destination_dir)
        logging.info(f"Unblob {input_file} to {output_dir}")
        output_file = os.path.join(output_dir, "unblob_report.json")
        response = subprocess.run(
            ["unblob", "-e", output_dir,
             "--report", output_file,
             "-d", "5",
             "--skip-magic", SKIP_MAGIC_FIRMWAREDROID_STRING,
             input_file],
            timeout=60 * 180)
        response.check_returncode()
    except subprocess.CalledProcessError as err:
        if response and response.returncode > 1:
            logging.warning(err)
            is_success = False

    return is_success
