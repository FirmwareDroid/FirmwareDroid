import logging
import shlex
import subprocess

SKIP_EXTENSION_DEFAULT = [".apk", ".dex", ".odex", ".oat", ".so", ".jar", ".class", ".java", ".png", ".jpg", ".jpeg",
                          ".gif", "w.ebp", ".bmp", ".tiff", ".tif", ".wav", ".mp3", ".ogg", ".mp4", ".3gp", ".webm",
                          ".mkv", ".flac", ".aac", ".m4a", ".flv", ".avi", ".mov", ".wmv", ".mpg", ".mpeg", ".pdf",
                          ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", "txt", ".xml", ".json", ".html", ".htm",
                          ".css", ".js", ".ts", ".tsx", ".svg", ".ttf", ".otf", ".woff", ".woff2", ".eot", ".md",
                          ".log", ".odt", ".ods", ".odp", ".odg", ".odf", ".odb", ".odc", ".odm", ".pak", ".rlib"]
SKIP_MAGIC_ANDROID = ["Android", "Java", "Font"]


def unblob_extract(compressed_file_path, destination_dir):
    """
    Extract a file recursively with the unblob extraction suite.

    :param destination_dir: str - path to the folder where the data is extracted to.
    :param compressed_file_path: str - path to the file to extract.

    :return: boolean - True in case it was successfully extracted.
    """
    is_success = True
    response = None
    try:
        input_file = shlex.quote(compressed_file_path)
        output_dir = shlex.quote(destination_dir)
        logging.info(f"Unblob {input_file} to {output_dir}")

        command_array = ["unblob",
                         "-e", output_dir,
                         "-d", "5",  # Recursion depth
                         "-p", "50",  # Number of workers
                         "-v",  # Verbose
                         ]
        for extension in SKIP_EXTENSION_DEFAULT:
            command_array.append("--skip-extension")
            command_array.append(extension)
        command_array.append(input_file)
        response = subprocess.run(command_array, timeout=60 * 180)
        response.check_returncode()
    except subprocess.CalledProcessError as err:
        if response and response.returncode > 1:
            logging.warning(err)
            is_success = False
        else:
            logging.warning(err)

    return is_success
