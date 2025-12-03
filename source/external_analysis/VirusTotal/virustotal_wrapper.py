# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
from model.Interfaces.ScanJob import ScanJob
from model import AndroidApp
from model import VirusTotalReport
from context.context_creator import create_db_context, create_log_context, setup_apk_scanner_logger
from processing.standalone_python_worker import start_python_interpreter

DB_LOGGER = setup_apk_scanner_logger(tags=["virustotal"])


def scan_apk_files(android_app, vt_api_key):
    import vt
    DB_LOGGER.info(f"Scanning APK file with VirusTotal: {android_app.id} file: {android_app.filename}")
    client = vt.Client(vt_api_key)
    if not os.path.exists(android_app.absolute_store_path):
        raise ValueError(f"File does not exist: {android_app.absolute_store_path}")
    analysis = scan_file(client, android_app.absolute_store_path)
    DB_LOGGER.info(f"VirusTotal scan completed for {android_app.id} storing Result: {analysis}...")
    store_virustotal_result(android_app, analysis)
    DB_LOGGER.info(f"VirusTotal result stored for {android_app.id}.")


def store_virustotal_result(android_app, analysis):
    logging.info(f"Storing VirusTotal result for {android_app.id} with Result:{analysis}")
    report = VirusTotalReport(file_info=analysis, android_app_id_reference=android_app.id)
    report.save()
    android_app.apk_scanner_report_reference_list.append(report.id)
    android_app.save()


def scan_file(client, file_path):
    DB_LOGGER.info(f"Invoking VirusTotal")
    with open(file_path, "rb") as f:
        analysis = client.scan_file(f, wait_for_completion=True)
    return analysis


@create_db_context
def start_virustotal_multiprocessing(android_app_id, vt_api_key):
    logging.info(f"Scanning APK file with VirusTotal: {android_app_id}")
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        scan_apk_files(android_app, vt_api_key)
    except Exception as e:
        logging.error(f"Error scanning APK file with VirusTotal: {android_app_id}")
        logging.error(e)


class VirusTotalScanJob(ScanJob):
    object_id_list = []
    vt_api_key = ""
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "external_analysis.VirusTotal.virustotal_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/virustotal/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self, vt_api_key):
        android_app_id_list = self.object_id_list
        logging.info(f"Virustotal analysis started! With {str(len(android_app_id_list))} apps.")
        worker_args_list = [vt_api_key]
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=start_virustotal_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      interpreter_path=self.INTERPRETER_PATH,
                                                      worker_args_list=worker_args_list)
            python_process.wait()
