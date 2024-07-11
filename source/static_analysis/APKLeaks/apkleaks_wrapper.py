# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import tempfile
import traceback
from Interfaces.ScanJob import ScanJob
from model import AndroidApp, ApkleaksReport
from context.context_creator import create_db_context, create_log_context
from utils.mulitprocessing_util.mp_util import start_python_interpreter


@create_log_context
@create_db_context
def apkleaks_worker_multiprocessing(android_app_id_queue):
    """
    Start the analysis on a multiprocessor queue.

    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.

    """
    while True:
        try:
            android_app_id = android_app_id_queue.get(timeout=.5)
        except Exception as err:
            break
        try:
            android_app = AndroidApp.objects.get(pk=android_app_id)
            logging.info(f"APKLeaks scans: {android_app.filename} {android_app.id} "
                         f"estimated queue-size: {android_app_id_queue.qsize()}")
            tempdir = tempfile.TemporaryDirectory()
            json_results = get_apkleaks_analysis(android_app.absolute_store_path, tempdir.name)
            create_report(android_app, json_results)
            android_app_id_queue.task_done()
        except Exception as err:
            traceback.print_exc()
            logging.error(f"APKleaks could not scan app id: {android_app_id} - "
                          f"error: {err}")


def get_apkleaks_analysis(apk_file_path, result_folder_path):
    """
    Scans an apk with APKLeaks.

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
    Create a class:'ApkleaksReport' and save the scan results in the database.

    :param android_app: class:'AndroidApp' - app that was scanned.
    :param json_results: str - scanning results in json format.

    """
    # TODO change static tool version to dynamic one
    apkleaks_report = ApkleaksReport(android_app_id_reference=android_app.id,
                                     scanner_version="2.6.1",
                                     scanner_name="APKLeaks",
                                     results=json_results).save()
    android_app.apkleaks_report_reference = apkleaks_report.id
    android_app.save()


class APKLeaksScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.APKLeaks.apkleaks_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/apkleaks/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of the scanner to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"APKLeaks analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=apkleaks_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="apkleaks_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
