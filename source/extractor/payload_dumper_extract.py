



def payload_dumper_extract(source_file_path, destination_dir):
    """
    Extracts .bin formatted files. Wrapper for extract android ota.

    :param source_file_path: str - path to the .bin file.
    :param destination_dir: str - path where the file is extracted to.

    """
    is_success = True
    try:

    except Exception as err:
        logging.warning(err)
        is_success = False
    return is_success


