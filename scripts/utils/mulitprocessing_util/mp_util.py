# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import os
import queue
import threading
import time
import flask
from multiprocessing import Manager, get_context
from threading import Thread
from scripts.database.database import multiprocess_disconnect_all
from scripts.rq_tasks.flask_context_creator import create_app_context


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
    :param target_function: the thread function that will be started.
    :type item_list: argument that will be converted to queue.
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


def start_process_pool(item_list, worker_function, number_of_processes=os.cpu_count(), use_id_list=True):
    """
    Creates a multiprocessor pool and starts the given function in parallel.
    :param use_id_list: boolean - if true, object-id list instead of the item list is used for the queue.
    Use this only if you provide an item list of documents with an id attribute.
    :param number_of_processes: number of processes to start.
    :param worker_function: function which will be executed by the pool
    :param item_list: list - items on work on.
    """
    multiprocess_disconnect_all(flask.current_app)
    with Manager() as manager:
        if use_id_list:
            item_id_queue = create_id_queue(item_list, manager)
        else:
            item_id_queue = create_managed_queue(item_list, manager)
        with get_context("fork").Pool(processes=number_of_processes,
                                      maxtasksperchild=3,
                                      initializer=multiprocess_initializer) as pool:
            #pool.starmap(worker_function, [(item_id_queue,)])
            pool.starmap_async(worker_function, [(item_id_queue,)])
            #pool.terminate()
            pool.close()
            pool.join()
        #item_id_queue.join()


def multiprocess_initializer():
    create_app_context()
