# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import sys
import concurrent.futures
sys.path.append("/var/www/source/")
from database.query_document import fetch_document_by_id_list
from model import AndroidApp
import importlib
import os
import queue
import subprocess
import sys
import threading
import time
from threading import Thread
from context.context_creator import create_app_context, setup_logging
import multiprocessing
from logging.handlers import QueueHandler, QueueListener

MAX_PROCESS_TIME = 60 * 60 * 24


def create_multi_threading_queue(document_list):
    """
    Creates a queue for multi threading.

    :param document_list: document - list of object to put into the queue.
    :return: queue

    """
    doc_queue = queue.Queue(maxsize=0)
    for doc in document_list:
        doc_queue.put(doc)
    time.sleep(5)
    return doc_queue


def start_threads(item_list, target_function, number_of_threads):
    """
    Starts a number of threads within the process.

    :param number_of_threads: int - number of treads to start.
    :param target_function: function - the thread function that will be started.
    :param item_list: list(object) - argument that will be converted to queue.

    """
    threading_queue = create_multi_threading_queue(item_list)
    worker_list = []
    while threading.active_count() > 150:
        time.sleep(5)
    for i in range(number_of_threads):
        worker = Thread(target=target_function, args=(threading_queue,))
        worker.setDaemon(True)
        worker.start()
        worker_list.append(worker)
    for worker in worker_list:
        worker.join()
    threading_queue.join()


def start_python_interpreter(item_list,
                             worker_function,
                             number_of_processes=os.cpu_count(),
                             use_id_list=True,
                             module_name=None,
                             interpreter_path=None,
                             worker_args_list=None):
    """
    Starts this script file in a new process with the given python interpreter. Executes the main function of this
    file and passes the given arguments to the new process.

    :param worker_args_list: list - list of arguments to pass to the worker function.
    :param module_name: str - Name of the fmd module to use.
    :param interpreter_path: string - Path to the python interpreter used for spawning the processes.
    :param use_id_list: boolean - if true: list of object-ids instead of object instances is used to create a queue
    for processing. Set to false in case you provide an instance list of documents that have an id attribute.
    :param number_of_processes: int - number of processes to start.
    :param worker_function: function - which will be executed by the pool of worker processes.
    :param item_list: list(documents or str) - list of object instances or list of object-id (strings) to process.

    """
    if worker_args_list is None:
        worker_args_list = []
    serialized_list_str = ",".join(map(str, item_list))
    current_file = os.path.abspath(__file__)
    # Starting the python interpreter with the given script and arguments
    command = [interpreter_path,
               current_file,
               serialized_list_str,
               worker_function.__name__,
               str(number_of_processes),
               str(use_id_list),
               module_name,
               *worker_args_list
               ]
    process = subprocess.Popen(command,
                               cwd="/var/www/source/",
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True,
                               bufsize=1
                               )

    def log_stream(stream, log_level):
        logger = logging.getLogger("subprocess_logger")
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(processName)s/%(process)d - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.propagate = False
        for line in iter(stream.readline, ''):
            if line:
                logger.log(log_level, line.strip())
        stream.close()

    stdout_thread = threading.Thread(target=log_stream, args=(process.stdout, logging.INFO), daemon=True)
    stderr_thread = threading.Thread(target=log_stream, args=(process.stderr, logging.ERROR), daemon=True)
    stdout_thread.start()
    stderr_thread.start()
    return process


def split_into_batches(item_list, batch_size):
    """
    Splits the item list into smaller batches.

    :param item_list: list - list of items to be processed.
    :param batch_size: int - size of each batch.

    :return: list of lists - list containing batches of items.
    """
    for i in range(0, len(item_list), batch_size):
        yield item_list[i:i + batch_size]


def worker_init(log_queue):
    # Each worker sends logs to the queue
    queue_handler = QueueHandler(log_queue)
    logger = logging.getLogger()
    logger.handlers = []
    logger.addHandler(queue_handler)
    logger.setLevel(logging.DEBUG)


def start_mp_process_pool_executor(item_list,
                                   worker_function,
                                   number_of_processes=os.cpu_count() * 2,
                                   create_id_list=True,
                                   worker_args_list=None):
    """
    Creates a multiprocessor pool and starts the processing the items with the given function.

    :param worker_args_list: list - list of arguments to pass to the worker function.
    :param create_id_list: boolean - if true, object-id list instead of the item list is used for the queue.
        Use this only if you provide an item list of documents with an id attribute.
    :param number_of_processes: int - number of processes to start.
    :param worker_function: function - which will be executed by the pool.
    :param item_list: list(object) - items to work on.

    :return: list - list of results from the worker function.
    """
    if len(item_list) < number_of_processes:
        number_of_processes = len(item_list)

    worker_task_list = [obj.id for obj in item_list] if create_id_list else item_list
    result_list = []

    # # Set up logging queue and listener in the main process
    log_queue = multiprocessing.Queue(-1)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(processName)s/%(process)d - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    listener = QueueListener(log_queue, handler)
    listener.start()

    logging.info(f"Starting multiprocessing pool with {number_of_processes} processes for function {worker_function}.")
    with concurrent.futures.ProcessPoolExecutor(max_workers=number_of_processes, initializer=worker_init, initargs=(log_queue,)) as executor:
        future_to_task = {executor.submit(worker_function, task, *(worker_args_list or [])): task for task in worker_task_list}
        for future in concurrent.futures.as_completed(future_to_task):
            result = future.result()
            result_list.append(result)

    listener.stop()
    return result_list


def multiprocess_initializer():
    create_app_context()
    setup_logging()


def main():
    """
    Main function that is executed when the script is started with a new python interpreter.
    The function starts the worker function in a new process and passes the given arguments to the new process.
    """
    pid = os.getpid()
    setup_logging()
    create_app_context()
    logging.info(f"Starting standalone python worker - PID: {pid}")
    id_list = sys.argv[1].split(",")
    if len(id_list) <= 0:
        sys.exit(-1)
    module_name = sys.argv[5]
    item_list = fetch_document_by_id_list(id_list, AndroidApp)
    if len(item_list) <= 0:
        logging.info("No items to process. Exiting.")
        sys.exit(0)

    worker_function_name = sys.argv[2]
    scanner_module = importlib.import_module(module_name)
    worker_function = getattr(scanner_module, worker_function_name)
    number_of_processes = int(sys.argv[3])
    use_id_list = bool(sys.argv[4])
    if len(sys.argv) > 7:
        worker_args_list = sys.argv[7:]
    else:
        worker_args_list = []
    start_mp_process_pool_executor(item_list, worker_function, number_of_processes, use_id_list, worker_args_list)


if __name__ == "__main__":
    main()
