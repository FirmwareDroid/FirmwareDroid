import time
from io import BytesIO
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED


def create_zip_file(file_dict):
    """
    Creates a zip file from a dict with filenames and file objects.
    :param file_dict: dict(filename, file)
    :return: BytesIO - zip file in memory.
    """
    memory_file = BytesIO()
    with ZipFile(memory_file, 'w') as zf:
        for filename, file in file_dict.items():
            data = file.read()
            file_meta = ZipInfo(filename)
            file_meta.date_time = time.localtime(time.time())[:6]
            file_meta.compress_type = ZIP_DEFLATED
            zf.writestr(file_meta, data.decode("utf-8"))
    memory_file.seek(0)
    return memory_file
