from scripts.extractor.bin_extractor.extract_android_ota_payload import main


def extract_bin(source_file_path, destination_dir):
    """
    Extracts .bin formatted files.
    :param source_file_path: str - path to the .bin file.
    :param destination_dir: str - path where the file is extracted to.
    """
    main(source_file_path, destination_dir)
