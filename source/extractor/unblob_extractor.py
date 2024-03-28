import logging
import shlex
import subprocess

SKIP_EXTENSION_DEFAULT = [".apk", ".dex", ".odex", ".oat", ".so", ".jar", ".class", ".java", ".png", ".jpg", ".jpeg",
                          ".gif", "w.ebp", ".bmp", ".tiff", ".tif", ".wav", ".mp3", ".ogg", ".mp4", ".3gp", ".webm",
                          ".mkv", ".flac", ".aac", ".m4a", ".flv", ".avi", ".mov", ".wmv", ".mpg", ".mpeg", ".pdf",
                          ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", "txt", ".xml", ".json", ".html", ".htm",
                          ".css", ".js", ".ts", ".tsx", ".svg", ".ttf", ".otf", "w.off", ".woff2", ".eot", ".md",
                          ".log", ".odt", ".ods", ".odp", ".odg", ".odf", ".odb", ".odc", ".odm", ".pak"]
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
        response = subprocess.run(
            ["unblob",
             "-e", output_dir,
             "-d", "5",     # Recursion depth
             "-p", "50",    # Number of workers
             "-v",          # Verbose
             "--skip-extension", ','.join(SKIP_EXTENSION_DEFAULT),
             input_file],
            timeout=60 * 180)
        response.check_returncode()
    except subprocess.CalledProcessError as err:
        if response and response.returncode > 1:
            logging.warning(err)
            is_success = False
        else:
            logging.warning(err)

    return is_success
