# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import os
import traceback

from scripts.database.query_document import get_filtered_list
from model import AndroidApp, LibRadarReport
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool


def start_libradar_scan(android_app_id_list):
    """
    Analysis all apps from the given list with libRadar.
    :param android_app_id_list: list of class:'AndroidApp' object-ids.
    """
    create_app_context()
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "libradar_report_reference")
    logging.info(f"LibRadar after filter: {str(len(android_app_list))}")
    if len(android_app_list) > 0:
        start_process_pool(android_app_list, libradar_worker, os.cpu_count())


def libradar_worker(android_app_id_queue):
    """
    Start the analysis with libradar on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while not android_app_id_queue.empty():
        android_app_id = android_app_id_queue.get()
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"Libradar scans: {android_app.id}")
        try:
            json_report = get_libradar_analysis(android_app.absolute_store_path)
            create_report(android_app, json_report)
        except Exception as err:
            logging.error(f"Libradar could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")
            traceback.print_exc()


def get_libradar_analysis(apk_file_path):
    """

    :param apk_file_path: str - path to the apk file.
    :return: dict - Libradar results as json.
    """
    from LibRadar import LibRadar
    lrd = LibRadar(apk_file_path)
    res = lrd.compare()
    return json.dumps(res, indent=4, sort_keys=True)


def create_report(android_app, libradar_results):
    """

    :param android_app: class:'AndroidApp'
    :param libradar_results: dict - results of the Libradar scan.
    :return:
    """
    libradar_report = LibRadarReport(
        android_app_id_reference=android_app.id,
        libradar_version="1.5.0",
        results=libradar_results
    ).save()
    android_app.libradar_report_reference = libradar_report.id
    android_app.save()
