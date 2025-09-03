import logging
import os
import subprocess
import threading
import time

UNBLOB_SEMAPHORE = threading.Semaphore(10)

SKIP_EXTENSION_DEFAULT = [".apk", ".apex", ".capex", ".dex", ".odex", ".oat", ".so", ".jar", ".class", ".java", ".png",
                          ".jpg", ".jpeg",
                          ".gif", ".ebp", ".bmp", ".tiff", ".tif", ".wav", ".mp3", ".ogg", ".mp4", ".3gp", ".webm",
                          ".mkv", ".flac", ".aac", ".m4a", ".flv", ".avi", ".mov", ".wmv", ".mpg", ".mpeg", ".pdf",
                          ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".xml", ".json", ".html", ".htm",
                          ".css", ".js", ".ts", ".tsx", ".svg", ".ttf", ".otf", ".woff", ".woff2", ".eot", ".md",
                          ".log", ".odt", ".ods", ".odp", ".odg", ".odf", ".odb", ".odc", ".odm", ".pak", ".rlib",
                          ".mtz", ".vdex", ".arsc", ".pb", ".aab", ".list", ".config", ".elf",
                          ".mbn", ".1", ".2", ".3", ".4", ".prop", ".conf", ".cfg", ".ini", ".sh", ".bat", ".cmd",
                          ".pem", ".pk8", ".url", ".elf32", ".elf64", "._lost+found", ".art"]


def remove_unblob_log():
    """
    Remove the unblob log file.
    """
    try:
        if os.path.exists("unblob.log"):
            os.remove("unblob.log")
    except Exception as err:
        logging.warning(err)


def unblob_extract(compressed_file_path,
                   destination_dir,
                   depth=1,
                   worker_count=5,
                   skip_extensions_list=None,
                   allow_extension_list=None,
                   cwd=None):
    """
    Extract a file recursively with the unblob extraction suite.

    :param allow_extension_list: list(str) - list of extensions to allow during extraction.
    Overwrites the skip extensions list.
    :param skip_extensions_list: list(str) - list of extensions to skip during extraction.
    :param worker_count: int - number of workers to use.
    :param depth: int - depth of unblob extraction.
    :param destination_dir: str - path to the folder where the data is extracted to.
    :param compressed_file_path: str - path to the file to extract.

    :return: boolean - True in case it was successfully extracted.
    """
    is_success = True
    response = None
    try:
        UNBLOB_SEMAPHORE.acquire()

        input_file = compressed_file_path
        output_dir = destination_dir
        filename = os.path.basename(compressed_file_path)
        file_extension = os.path.splitext(filename)[1]

        if skip_extensions_list is None:
            skip_extensions_list = SKIP_EXTENSION_DEFAULT

        if allow_extension_list is None:
            allow_extension_list = []

        for item in allow_extension_list:
            if item in skip_extensions_list:
                skip_extensions_list.remove(item)

        if file_extension in SKIP_EXTENSION_DEFAULT or os.path.islink(input_file):
            logging.info(f"Skipping {filename} for unblob extraction. Extension: {file_extension} or symlink.")
            return True
        logging.info(f"Unblob {input_file} to {output_dir}")
        #time_now = time.time()
        command_array = ["unblob",
                         "-e", output_dir,
                         "-d", str(depth),  # Recursion depth
                         "-p", str(worker_count),  # Number of workers
                         "-v",  # Verbose
                         #"--report", output_dir + f"/unblob_{time_now}.json",
                         ]

        for extension in skip_extensions_list:
            command_array.append("--skip-extension")
            command_array.append(extension)
        command_array.append(input_file)
        response = subprocess.run(command_array, timeout=60 * 60 * 3, cwd=cwd)
        response.check_returncode()
    except subprocess.CalledProcessError as err:
        if response and response.returncode > 1:
            logging.warning(err)
            is_success = False
        else:
            logging.warning(err)
    except subprocess.TimeoutExpired as err:
        logging.error(f"Unblob Timeout expired: {err}")
        is_success = False
    finally:
        UNBLOB_SEMAPHORE.release()
        remove_unblob_log()
    return is_success
