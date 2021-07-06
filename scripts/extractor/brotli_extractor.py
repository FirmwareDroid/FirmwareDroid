import brotli


def extract_brotli(source_file_path, destination_dir):
    """
    Extract brotli (.br) compressed files.
    :param source_file_path: str - path to the .bin file.
    :param destination_dir: str - path where the file is extracted to.
    """
    brotli.decompress()