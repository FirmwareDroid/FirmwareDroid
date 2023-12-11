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
from Interfaces.ScanJob import ScanJob
from model import AndroidApp, SuperReport
from context.context_creator import create_db_context
from utils.mulitprocessing_util.mp_util import start_python_interpreter


def super_android_analyzer_multiprocessing(android_app_id_queue):
    """
    Start the analysis with super on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while True:
        android_app_id = android_app_id_queue.get(timeout=.5)
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"SUPER Android Analyzer scans: {android_app.filename} {android_app.id} "
                     f"estimated queue-size: {android_app_id_queue.qsize()}")
        try:
            tempdir = tempfile.TemporaryDirectory()
            super_json_results = get_super_android_analyzer_analysis(android_app.absolute_store_path, tempdir.name)
            create_report(android_app, super_json_results)
        except Exception as err:
            logging.error(f"Super could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")
        android_app_id_queue.task_done()


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


def create_report(android_app, super_json_results):
    """
    Create a class:'SuperReport' and save the super android analyzer scan results in the database.
    :param android_app: class:'AndroidApp' - app that was scanned with super.
    :param super_json_results: str - super scanning result in json format.
    :return: class:'SuperReport'
    """
    # TODO remove static version and replace with dynamic one
    super_report = SuperReport(android_app_id_reference=android_app.id,
                               super_version="0.5.1",
                               results=super_json_results).save()
    android_app.super_report_reference = super_report.id
    android_app.save()
    return super_report


class SuperAndroidAnalyzerScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.SuperAndroidAnalyzer.super_android_analyzer_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/qark/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of AndroGuard to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Super Android Analyzer analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            start_python_interpreter(item_list=android_app_id_list,
                                     worker_function=super_android_analyzer_multiprocessing,
                                     number_of_processes=os.cpu_count(),
                                     use_id_list=True,
                                     module_name=self.MODULE_NAME,
                                     report_reference_name="super_report_reference",
                                     interpreter_path=self.INTERPRETER_PATH)
