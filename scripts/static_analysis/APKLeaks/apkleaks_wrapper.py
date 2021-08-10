# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import tempfile
import traceback

from model import AndroidApp, ApkLeaksReport
from scripts.database.query_document import get_filtered_list
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool


def start_apkleaks_scan(android_app_id_list):
    """
    Analysis all apps from the given list with APKLeaks.
    :param android_app_id_list: list of class:'AndroidApp' object-ids.
    """
    create_app_context()
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "apkleaks_report_reference")
    logging.info(f"APKLeaks after filter: {str(len(android_app_list))}")
    if len(android_app_list) > 0:
        start_process_pool(android_app_list, apkleaks_worker, os.cpu_count())


def apkleaks_worker(android_app_id_queue):
    """
    Start the analysis on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while not android_app_id_queue.empty():
        android_app_id = android_app_id_queue.get()
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"APKLeaks scans: {android_app.id}")
        try:
            tempdir = tempfile.TemporaryDirectory()
            json_results = get_apkleaks_analysis(android_app.absolute_store_path, tempdir.name)
            create_report(android_app, json_results)
        except Exception as err:
            traceback.print_exc()
            logging.error(f"APKleaks could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")


def get_apkleaks_analysis(apk_file_path, result_folder_path):
    """
    Scans an apk with the apkleaks.
    :param apk_file_path: str - path to the apk file.
    :param result_folder_path: str - path to the folder where the result report is saved.
    :return: str - scan result as json.
    """
    from apkleaks.apkleaks import APKLeaks
    result_file = tempfile.TemporaryFile(dir=result_folder_path)

    class ApkleakArguments(object):
        def __init__(self, json, apk_path, output_file_path, jadx_args):
            self.json = json
            self.file = apk_path
            self.output = output_file_path
            self.args = jadx_args
            self.pattern = None
    apkleaks_args = ApkleakArguments(True, apk_file_path, result_file.name, "--deobf")
    apkleaks_scanner = APKLeaks(apkleaks_args)
    try:
        apkleaks_scanner.integrity()
        apkleaks_scanner.decompile()
        apkleaks_scanner.scanning()
        json_result = apkleaks_scanner.out_json
    finally:
        apkleaks_scanner.cleanup()
    if not json_result:
        raise RuntimeError(f"Apkleaks could not scan {apk_file_path}")
    return json_result


def create_report(android_app, json_results):
    """
    Create a class:'APKLeaksReport' and save the scan results in the database.
    :param android_app: class:'AndroidApp' - app that was scanned.
    :param json_results: str - scanning results in json format.
    """
    # TODO change static tool version to dynamic one
    apkleaks_report = ApkLeaksReport(android_app_id_reference=android_app.id,
                                     apkleaks_version="2.6.0",
                                     results=json_results).save()
    android_app.apkleaks_report_reference = apkleaks_report.id
    android_app.save()
