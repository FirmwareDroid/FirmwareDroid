# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import os
import shlex
import subprocess
import tempfile
from pathlib import Path
from model.Interfaces.ScanJob import ScanJob
from model import AndroidApp, SuperReport
from context.context_creator import create_db_context, setup_apk_scanner_logger, \
    create_log_context
from processing.standalone_python_worker import start_python_interpreter


DB_LOGGER = setup_apk_scanner_logger(tag="super")


@create_db_context
def super_android_analyzer_multiprocessing(android_app_id):
    """
    Start the analysis with super on a multiprocessor queue.

    :param android_app_id: str - id of the android app.

    """
    android_app = AndroidApp.objects.get(pk=android_app_id)
    DB_LOGGER.info(f"SUPER Android Analyzer scans: {android_app.filename} {android_app.id}")
    try:
        tempdir = tempfile.TemporaryDirectory()
        super_json_results = get_super_android_analyzer_analysis(android_app.absolute_store_path, tempdir.name)
        store_result(android_app, results=super_json_results, scan_status="completed")
        DB_LOGGER.info(f"SUCCESS: SUPER Android Analyzer completed scan: {android_app.filename} {android_app.id}")
    except Exception as err:
        DB_LOGGER.error(f"ERROR: SUPER Android Analyzer failed to scan: {android_app.filename} {android_app.id}")
        store_result(android_app, results={"error": f"{err}"}, scan_status="failed")
        logging.error(f"Super could not scan app {android_app.filename} id: {android_app.id} - "
                      f"error: {err}")


def get_super_android_analyzer_analysis(apk_file_path, result_folder_path):
    """
    Scans an apk with the super android analyzer.
    :param apk_file_path: str - path to the apk file.
    :param result_folder_path: str - path to the folder where the result report is saved.
    :return: str - scan result as json.
    """
    apk_file_path = shlex.quote(str(apk_file_path))
    result_folder_path = shlex.quote(str(result_folder_path))
    parent_dir = Path(apk_file_path).parent
    response = subprocess.run(["super-analyzer", "--json",
                               "--results", result_folder_path,
                               "--downloads", parent_dir,
                               str(apk_file_path)],
                              timeout=1200,
                              cwd=result_folder_path)
    response.check_returncode()
    result_file_path = ""
    for root, dirs, files in os.walk(result_folder_path):
        for file in files:
            if file == "results.json":
                result_file_path = os.path.join(root, file)
    if not result_file_path:
        raise ValueError("Could not find scanning result json.")
    return json.loads(open(result_file_path).read())


def store_result(android_app, results, scan_status):
    """
    Create a class:'SuperReport' and save the super android analyzer scan results in the database.
    :param android_app: class:'AndroidApp' - app that was scanned with super.
    :param results: str - super scanning result in json format.
    :return: class:'SuperReport'
    """
    # TODO remove static version and replace with dynamic one
    super_report = SuperReport(android_app_id_reference=android_app.id,
                               super_version="0.5.1",
                               scan_status=scan_status,
                               results=results).save()
    android_app.apk_scanner_report_reference_list.append(super_report.id)
    android_app.save()
    return super_report


class SuperAndroidAnalyzerScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.SuperAndroidAnalyzer.super_android_analyzer_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/qark/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of AndroGuard to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Super Android Analyzer analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=super_android_analyzer_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
