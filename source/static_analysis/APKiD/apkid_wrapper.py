# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import os
import logging
import tempfile

from Interfaces.ScanJob import ScanJob
from model import ApkidReport, AndroidApp
from context.context_creator import create_db_context
from utils.mulitprocessing_util.mp_util import start_python_interpreter


def process_android_app(android_app_id):
    """
    Scans an Android app with the APKiD scanner and stores the results in the database.

    :param android_app_id: str - object-id for document of  class:'AndroidApp'

    """
    from apkid.apkid import Options, Scanner
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

            is_report_saved = False
            for dirpath, dirnames, filenames in os.walk(output_dir):
                for filename in filenames:
                    if filename == android_app.filename:
                        report_file_path = os.path.join(dirpath, filename)
                        store_apkid_result(android_app, report_file_path)
                        is_report_saved = True
                        break

            if not is_report_saved:
                raise ValueError(f"APKid ERROR: Could not save report: {android_app.filename} id: {android_app.id}")

    except Exception as err:
        logging.error(err)


def apkid_worker_multiprocessing(android_app_id_queue):
    """
    Starts to analyze the given android apps with apkid tool.

    :param android_app_id_queue: multiprocessor queue with object-id's of class:'AndroidApp'.

    """
    while True:
        logging.info(f"APKiD Queue size estimate: {android_app_id_queue.qsize()}")
        android_app_id = android_app_id_queue.get(timeout=.5)
        process_android_app(android_app_id)
        android_app_id_queue.task_done()


def store_apkid_result(android_app, report_file_path):
    """
    Creates and APKiD report.

    :param android_app: class:'AndroidApp'
    :param report_file_path: path to the apkid report (json).
    :return: class:'ApkidReport'

    """
    import apkid
    with open(report_file_path, 'rb') as report_file:
        apkid_report = ApkidReport(android_app_id_reference=android_app.id,
                                   scanner_version=apkid.__version__,
                                   scanner_name="APKiD",
                                   report_file_json=report_file)
    parse_apkid_report(report_file_path, apkid_report)
    apkid_report.save()
    android_app.apkid_report_reference = apkid_report.id
    android_app.save()
    return apkid_report


def parse_apkid_report(report_file_path, apkid_report):
    """
    Parses an apkid report.

    :param apkid_report: class:'ApkidReport'
    :param report_file_path: path to the apkid report (json).


    """
    with open(report_file_path, 'r') as json_file:
        data = json.load(json_file)
        if data and len(data) > 0:
            apkid_report.apkid_version = data.get("apkid_version")
            apkid_report.rules_sha256 = data.get("rules_sha256")
            apkid_report.files = data.get("files")


class APKiDScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.APKiD.apkid_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/apkid/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of the scanner to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"APKiD analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            start_python_interpreter(item_list=android_app_id_list,
                                     worker_function=apkid_worker_multiprocessing,
                                     number_of_processes=os.cpu_count(),
                                     use_id_list=True,
                                     module_name=self.MODULE_NAME,
                                     report_reference_name="apkid_report_reference",
                                     interpreter_path=self.INTERPRETER_PATH)
