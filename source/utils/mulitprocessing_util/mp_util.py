# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import sys

sys.path.append("/var/www/source/")
from database.query_document import get_filtered_list
from model import AndroidApp
import importlib
import os
import queue
import subprocess
import sys
import threading
import time
from multiprocessing import Manager, get_context
from threading import Thread
from database.connector import multiprocess_disconnect_all
from context.context_creator import create_app_context


def create_managed_queue(document_obj_list, manager):
    """
    Creates a closed managed multiprocessing queue.

    :param document_obj_list: list of elements to add to the queue.
    :param manager: multiprocessor manager which handles the queue.
    :return: multiprocessing manager.Queue()

    """
    queue_docs = manager.Queue()
    for report in document_obj_list:
        queue_docs.put(report)
    time.sleep(0.1)
    return queue_docs


def create_id_queue(document_list, manager):
    """
    Creates a multiprocessor-queue from the given list to a queue.

    :param manager: multiprocessor manager.
    :param document_list: list of objects to put into the queue
    :return: Queue(objectID)

    """
    mp_queue = manager.Queue()
    for obj in document_list:
        mp_queue.put(obj.id)
    time.sleep(0.1)
    return mp_queue


def create_multi_threading_queue(document_list):
    """
    Creates a queue for multi threading.

    :param document_list: document - list of object to put into the queue.
    :return: queue

    """
    doc_queue = queue.Queue(maxsize=0)
    for doc in document_list:
        doc_queue.put(doc)
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
                             report_reference_name=None,
                             interpreter_path=None):
    """
    Starts this script file in a new process with the given python interpreter. Executes the main function of this
    file and passes the given arguments to the new process.

    :param module_name: str -
    :param report_reference_name: str - Class:'AndroidApp' attribute name to store the result report.
    :param interpreter_path: string - Path to the python interpreter used for spawning the processes.
    :param use_id_list: boolean - if true: list of object-ids instead of object instances is used to create a queue
    for processing. Set to false in case you provide an instance list of documents that have an id attribute.
    :param number_of_processes: int - number of processes to start.
    :param worker_function: function - which will be executed by the pool of worker processes.
    :param item_list: list(documents or str) - list of object instances or list of object-id (strings) to process.

    """
    serialized_list_str = ",".join(map(str, item_list))
    current_file = os.path.abspath(__file__)
    return subprocess.Popen([interpreter_path,
                             current_file,
                             serialized_list_str,
                             worker_function.__name__,
                             str(os.cpu_count()),
                             str(use_id_list),
                             module_name,
                             report_reference_name
                             ],
                            cwd="/var/www/source/")


def start_process_pool_new(item_list, worker_function, number_of_processes=os.cpu_count(), use_id_list=True):
    """
    Creates a multiprocessor pool and starts the given function in parallel.

    :param use_id_list: boolean - if true, object-id list instead of the item list is used for the queue.
        Use this only if you provide an item list of documents with an id attribute.
    :param number_of_processes: int - number of processes to start.
    :param worker_function: function - which will be executed by the pool.
    :param item_list: list(object) - items to work on.

    """
    multiprocess_disconnect_all()
    with Manager() as manager:
        if use_id_list:
            item_id_queue = create_id_queue(item_list, manager)
        else:
            item_id_queue = create_managed_queue(item_list, manager)
        with get_context("fork").Pool(processes=number_of_processes,
                                      maxtasksperchild=3,
                                      initializer=multiprocess_initializer) as pool:

            pool.starmap_async(worker_function, [(item_id_queue,)])
            pool.close()
            pool.join()


def multiprocess_initializer():
    create_app_context()


def main():
    create_app_context()
    id_list = sys.argv[1].split(",")
    if len(id_list) <= 0:
        sys.exit(-1)
    module_name = sys.argv[5]
    report_reference_name = sys.argv[6]
    item_list = get_filtered_list(id_list, AndroidApp, report_reference_name)
    worker_function_name = sys.argv[2]
    scanner_module = importlib.import_module(module_name)
    worker_function = getattr(scanner_module, worker_function_name)
    number_of_processes = int(sys.argv[3])
    use_id_list = bool(sys.argv[4])
    start_process_pool_new(item_list, worker_function, number_of_processes, use_id_list)


if __name__ == "__main__":
    main()
