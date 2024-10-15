import logging
import os
import string
import struct


def app_extractor(source_file_path, destination_dir):
    """
    Attempt to split .app files into img files.

    Info: https://github.com/stze/splituapp/blob/986612c507d5d428774b6fdb470527993895fd42/splituapp

    :param source_file_path: str - path to the .app file.
    :param destination_dir: str - path where the file is extracted to.

    :return: boolean - True in case it was successfully extracted.
    """
    logging.info(f"Extracting firmware with splituapp: {source_file_path} to {destination_dir}")
    is_success = False
    try:
        split_app_files(source_file_path, destination_dir)
        is_success = True
    except Exception as e:
        logging.error(e)
    return is_success


def split_app_files(source_file_path, destination_dir):
    bytenum = 4
    with open(source_file_path, 'rb') as input_file:
        while True:
            i = input_file.read(bytenum)
            if not i:
                break
            if i != b'\x55\xAA\x5A\xA5':
                continue
            else:
                header_size = input_file.read(bytenum)
                header_size = list(struct.unpack('<L', header_size))[0]
                input_file.seek(16, 1)
                filesize = input_file.read(bytenum)
                filesize = list(struct.unpack('<L', filesize))[0]
                input_file.seek(32, 1)
                filename = input_file.read(16)
                try:
                    filename = str(filename.decode())
                    filename = ''.join(f for f in filename if f in string.printable).lower()
                except:
                    filename = ''
                if "/" in filename:
                    raise ValueError(f"Potential directory traversal: {filename}")
                input_file.seek(22, 1)
                crc_byte_value = input_file.read(header_size - 98)

                output_filename = os.path.join(destination_dir, f"{filename}.img")
                while os.path.exists(output_filename):
                    output_filename += ".DUPLICATE"
                try:
                    with open(output_filename, 'wb') as o:
                        pending_size = filesize
                        while pending_size > 0:
                            current_read_size = min(pending_size, 1024 * 1024)
                            chunk_data = input_file.read(current_read_size)
                            assert len(chunk_data) == current_read_size
                            o.write(chunk_data)
                            pending_size -= current_read_size
                except:
                    raise RuntimeError('ERROR: Failed to create ' + filename + '.img\n')

                xbytes = bytenum - input_file.tell() % bytenum
                if xbytes < bytenum:
                    input_file.seek(xbytes, 1)