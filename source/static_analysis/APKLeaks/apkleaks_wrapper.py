# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
import tempfile
import traceback
import pkg_resources
from model import AndroidApp, ApkleaksReport
from context.context_creator import create_db_context, create_log_context, setup_apk_scanner_logger
from model.Interfaces.ScanJob import ScanJob
from processing.standalone_python_worker import start_python_interpreter

DB_LOGGER = setup_apk_scanner_logger(tags=["apkleaks"])


@create_log_context
@create_db_context
def apkleaks_worker_multiprocessing(android_app_id):
    """
    Start the analysis on a multiprocessor queue.

    :param android_app_id: str - id of the AndroidApp to be scanned.

    """
    android_app = None
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        DB_LOGGER.info(f"APKLeaks scans: {android_app.filename} {android_app.id} ")
        tempdir = tempfile.TemporaryDirectory()
        json_results = get_apkleaks_analysis(android_app.absolute_store_path, tempdir.name)
        store_result(android_app, results=json_results, scan_status="completed")
        DB_LOGGER.info(f"SUCCESS: APKLeaks completed scan: {android_app.filename} {android_app.id} ")
    except Exception as err:
        DB_LOGGER.error(f"ERROR: APKLeaks could not scan app id: {android_app_id} - filename: {android_app.filename}")
        if android_app:
            store_result(android_app, results={"error": f"{err}"}, scan_status="failed")
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


def store_result(android_app, results, scan_status):
    """
    Create a class:'ApkleaksReport' and save the scan results in the database.

    :param android_app: class:'AndroidApp' - app that was scanned.
    :param results: str - scanning results in json format.
    :param scan_status: str - status of the scan.

    """
    version = pkg_resources.get_distribution("apkleaks").version
    apkleaks_report = ApkleaksReport(android_app_id_reference=android_app.id,
                                     scanner_version=version,
                                     scanner_name="APKLeaks",
                                     scan_status=scan_status,
                                     results=results).save()
    android_app.apk_scanner_report_reference_list.append(apkleaks_report.id)
    android_app.save()


class APKLeaksScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.APKLeaks.apkleaks_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/apkleaks/bin/python"

    def __init__(self, object_id_list, **kwargs):
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
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
