# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import os
import logging
import tempfile
import traceback

from model.Interfaces.ScanJob import ScanJob
from model import ApkidReport, AndroidApp
from context.context_creator import create_db_context, create_log_context
from processing.standalone_python_worker import start_python_interpreter


def process_android_app(android_app_id):
    """
    Scans an Android app with the APKiD scanner and stores the results in the database.

    :param android_app_id: str - object-id for document of  class:'AndroidApp'

    """
    from apkid.apkid import Options, Scanner
    android_app = None
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"APKid scans app: {android_app.filename} id: {android_app.id}")

        with tempfile.TemporaryDirectory() as output_dir:
            if not os.path.exists(output_dir):
                raise OSError(f"Could not create temp dir for apkid: {output_dir}")

            options = Options(
                timeout=600,
                verbose=True,
                json=True,
                output_dir=output_dir,
                typing='magic',
                entry_max_scan_size=0,
                scan_depth=20,
                recursive=False,
                include_types=True
            )
            rules = options.rules_manager.load()
            scanner = Scanner(rules, options)
            scanner.scan(android_app.absolute_store_path)

            report_file_path = os.path.join(output_dir, android_app.filename)
            if not os.path.exists(report_file_path):
                raise FileNotFoundError(
                    f"APKid ERROR: Could not find report: {android_app.filename} id: {android_app.id}"
                )

            with open(report_file_path, 'r') as json_file:
                results = json.load(json_file)
                store_result(android_app, results=results, scan_status="completed")

    except Exception as err:
        if android_app:
            store_result(android_app, results={}, scan_status="failed")
        logging.error(err)


@create_log_context
@create_db_context
def apkid_worker_multiprocessing(android_app_id):
    """
    Starts to analyze the given android apps with apkid tool.

    :param android_app_id: str - object-id for document of  class:'AndroidApp'

    """
    try:
        process_android_app(android_app_id)
    except Exception as err:
        logging.error(err)
        traceback.print_exc()


def store_result(android_app, results, scan_status):
    """
    Creates and APKiD report.

    :param android_app: class:'AndroidApp'
    :param results: dict - results from the apkid scan
    :param scan_status: str - status of the scan (completed, failed)

    :return: class:'ApkidReport'

    """
    import apkid
    apkid_report = ApkidReport(android_app_id_reference=android_app.id,
                               scanner_version=apkid.__version__,
                               scanner_name="APKiD",
                               scan_status=scan_status,
                               results=results)
    apkid_report.save()
    android_app.apkid_report_reference = apkid_report.id
    android_app.save()
    return apkid_report


class APKiDScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.APKiD.apkid_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/apkid/bin/python"

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
        logging.info(f"APKiD analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=apkid_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="apkid_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
