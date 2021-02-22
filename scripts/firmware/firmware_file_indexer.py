import logging
import os
from multiprocessing import Lock
from scripts.firmware.system_partition_util import expand_and_mount
from scripts.firmware.ext4_mount_util import is_path_mounted, exec_umount
from scripts.hashing.fuzzy_hash_creator import hash_firmware_files
from model import FirmwareFile, AndroidFirmware
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool, start_threads
from scripts.rq_tasks.task_util import create_app_context
from scripts.hashing import md5_from_file
from scripts.utils.file_utils.file_util import  create_temp_directories

lock = Lock()


def start_firmware_indexer(firmware_id_list):
    """
    Starts the firmware file indexer, which generates a list of all files in the firmware. Function for rq-worker.
    :param firmware_id_list: list(str) - id's of class:'AndroidFirmware'
    """
    create_app_context()
    #firmware_list = filter_firmware(firmware_id_list)
    start_parallel_file_index(firmware_id_list)


def filter_firmware(firmware_id_list):
    """
    Filter firmware files which are already indexed.
    :param firmware_id_list: list(str) - list of class:'AndroidFirmware' object-id's
    :return: list of class:'AndroidFirmware' - filtered by hasFileIndex == False
    """
    filtered_firmware_list = []
    for firmware_id in firmware_id_list:
        firmware = AndroidFirmware.objects.get(pk=firmware_id)
        if len(firmware.firmware_file_id_list) > 300:   # TODO remove this Bug fix
            firmware.hasFileIndex = True
            firmware.save()
        if not firmware.hasFileIndex:
            filtered_firmware_list.append(firmware)
    return filtered_firmware_list


def start_parallel_file_index(firmware_id_list):
    """
    Starts the file indexer with multiple processes.
    :param firmware_id_list: list(object-id's) of class:'AndroidFirmware'
    """
    logging.info(f"Start to index firmware files: {len(firmware_id_list)}")
    start_threads(firmware_id_list, index_image_files, number_of_threads=10)
    #start_process_pool(firmware_id_list, index_image_files, number_of_processes=os.cpu_count(), use_id_list=False)


def index_image_files(firmware_id_queue):
    """
    Creates a file list of the given firmware and save it to the database. Create an index only if it not exists yet.
    :type firmware_id_queue: multiprocessor queue(str)
    """
    create_app_context()
    while True:
    #while not firmware_id_queue.empty():
        firmware_id = firmware_id_queue.get()
        firmware = AndroidFirmware.objects.get(pk=firmware_id)
        cache_temp_file_dir, cache_temp_mount_dir = create_temp_directories()
        cache_temp_file_dir = cache_temp_file_dir.name
        cache_temp_mount_dir = cache_temp_mount_dir.name
        #cache_temp_file_dir = create_permanent_cache_directory(str(uuid.uuid4()))
        #cache_temp_mount_dir = create_permanent_cache_directory(str(uuid.uuid4()))
        logging.info(f"{cache_temp_file_dir} {cache_temp_mount_dir}")
        try:
            logging.info(f"Firmware indexer: {firmware.id} estimated queue-size: {firmware_id_queue.qsize()}")
            if not firmware.hasFileIndex:
                logging.info(f"START firmware file indexing for: {firmware.id}")
                expand_and_mount(firmware, cache_temp_file_dir, cache_temp_mount_dir)
                firmware_file_list = create_firmware_file_list(scan_directory=cache_temp_mount_dir,
                                                               partition_name="system")
                add_firmware_file_references(firmware, firmware_file_list)
                hash_firmware_files(firmware, cache_temp_mount_dir)    # Todo remove this line after indexing all files.
        except Exception as err:
            logging.error(err)
        finally:
            if is_path_mounted(cache_temp_mount_dir):
                exec_umount(cache_temp_mount_dir)
            #delete_folder(cache_temp_file_dir)
            #delete_folder(cache_temp_mount_dir)
        firmware_id_queue.task_done()


def create_firmware_file_list(scan_directory, partition_name):
    """
    Creates a File list from the given directory.
    :param partition_name: str - name of the partition.
    :param scan_directory: str - path to the directory to scan
    :return: Array class:'FirmwareFile'
    """
    result_files = []
    logging.info(f"Start scanning through directory for files: {scan_directory}")
    for root, dirs, files in os.walk(scan_directory):
        parent_name = os.path.basename(root) if os.path.basename(root) else "/"
        if parent_name == os.path.basename(scan_directory):
            parent_name = "/"
        for directory in dirs:
            relative_dir_path = root.replace(scan_directory, "")
            relative_dir_path = os.path.join(relative_dir_path, directory)
            firmware_file = create_firmware_file(name=directory,
                                                 parent_name=parent_name,
                                                 isDirectory=True,
                                                 relative_file_path=relative_dir_path,
                                                 partition_name=partition_name,
                                                 md5=None)
            result_files.append(firmware_file)
        for filename in files:
            relative_file_path = root.replace(scan_directory, "")
            relative_file_path = os.path.join(relative_file_path, filename)
            filename_path = os.path.join(root, filename)
            if os.path.isfile(filename_path):
                md5_file = md5_from_file(filename_path)
                file_size_bytes = os.path.getsize(filename_path)
                firmware_file = create_firmware_file(name=filename,
                                                     parent_name=parent_name,
                                                     isDirectory=False,
                                                     file_size_bytes=file_size_bytes,
                                                     relative_file_path=relative_file_path,
                                                     partition_name=partition_name,
                                                     md5=md5_file)
                result_files.append(firmware_file)
    return result_files


def create_firmware_file(name, parent_name, isDirectory, relative_file_path, partition_name, md5, file_size_bytes=None):
    """
    Creates a class:'FirmwareFile' document. Does not save the document to the database.
    :param file_size_bytes: int - file size in bytes
    :param partition_name: str - name of the partition.
    :param name: str - name of file or directory
    :param parent_name: str - name of the parent directory
    :param isDirectory: bool - true if it is a directory
    :param relative_file_path: str - relative path within the firmware
    :param md5: str - md5 digest of the file.
    :return: class:'FirmwareFile'
    """
    return FirmwareFile(name=name,
                        parent_dir=parent_name,
                        isDirectory=isDirectory,
                        file_size_bytes=file_size_bytes,
                        absolute_store_path=os.path.abspath(relative_file_path),
                        relative_path=relative_file_path,
                        partition_name=partition_name,
                        md5=md5)


def add_firmware_file_references(firmware, firmware_file_list):
    """
    Add the firmware references for the given files. Saves the reference in the database.
    :param firmware: class:'AndroidFirmware'
    :param firmware_file_list: list of class:'FirmwareFile'
    """
    if len(firmware_file_list) > 0:
        logging.info(f"Add file references for: {firmware.id}")
        firmware_file_ids = []
        for firmware_file in firmware_file_list:
            firmware_file.firmware_id_reference = firmware.id
            firmware_file.save()
            firmware_file_ids.append(firmware_file.id)
        firmware.firmware_file_id_list = firmware_file_ids
        firmware.hasFileIndex = True
        firmware.save()
        logging.info(f"Successfully added firmware file references: {firmware.id} {len(firmware_file_list)}")
    else:
        raise ValueError(f"No firmware file references added: firmware-id {firmware.id} {len(firmware_file_list)}")


