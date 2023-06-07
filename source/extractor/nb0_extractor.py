import io
import logging
import os
from pathlib import Path
from struct import unpack


def extract_nb0(source):
    """
    Extracts .nb0 files.

    :param source: str - path to the file to extract.

    """
    logging.info(f"Extract .nb0 file: {str(source)}")
    with open(source, mode='rb') as file:
        file_entry_dict = {}
        data = file.read(4)
        file_count = unpack('<i', data)[0]
        data_offset = 4 + file_count * 64
        for _ in range(file_count):
            data = file.read(64)
            (offset, size, unknown1, unknown2, filename) = unpack("<4I48s", data)
            filename = filename.decode('ascii').rstrip('\0')
            if filename not in file_entry_dict:
                file_entry_dict[filename] = {'offset': offset, 'size': size}

        for filename, info in file_entry_dict.items():
            source_parent = Path(source).parent
            output_file_path = os.path.join(source_parent, filename)
            logging.info(f'Extract to disk "{output_file_path}"')
            with open(output_file_path, mode='xb') as output:
                file.seek(data_offset + info['offset'], 0)
                remaining_bytes = info['size']
                while remaining_bytes > 0:
                    chunk_size = min(io.DEFAULT_BUFFER_SIZE, remaining_bytes)
                    output.write(file.read(chunk_size))
                    remaining_bytes -= chunk_size
