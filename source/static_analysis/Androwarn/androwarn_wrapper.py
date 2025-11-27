# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import logging
import os
import sys
import tempfile
from multiprocessing import Lock

from model.Interfaces.ScanJob import ScanJob
from model import AndrowarnReport, AndroidApp
from context.context_creator import create_db_context, create_apk_scanner_log_context
from processing.standalone_python_worker import start_python_interpreter

lock = Lock()


@create_apk_scanner_log_context
@create_db_context
def androwarn_worker_multiprocessing(android_app_id):
    """
    Start the analysis with androwarn. Wrapper function taken and modified from androwarn.py.

    :param android_app_id: str - Android app id

    """
    from androguard.misc import AnalyzeAPK
    from androwarn.warn.analysis.analysis import perform_analysis
    from androwarn.warn.report.report import dump_analysis_results, generate_report
    from androwarn.warn.search.application.application import grab_application_package_name

    android_app = None
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"Androwarn scan: {android_app.filename} {android_app.id} ")
        with_playstore_lookup = False
        display_report = False
        report_type = 'json'
        verbose = 3
        with lock:
            output = tempfile.NamedTemporaryFile()
        a, d, x = AnalyzeAPK(android_app.absolute_store_path)
        package_name = grab_application_package_name(a)
        data = perform_analysis(android_app.absolute_store_path, a, d, x, with_playstore_lookup)
        if display_report:
            dump_analysis_results(data, sys.stdout)
        generate_report(package_name, data, verbose, report_type, output.name)
        report_file_path = output.name + "." + report_type
        results = parse_json_report(report_file_path)
        store_result(android_app, results=results, scan_status="completed")
    except Exception as err:
        if android_app:
            store_result(android_app, results={"error": f"{err}"}, scan_status="failed")
        logging.error(f"Androwarn could not scan app {android_app.filename} id: {android_app.id} - "
                      f"error: {str(err)}")
        raise RuntimeError(f"Androwarn could not scan app {android_app.filename}")


def store_result(android_app, results, scan_status):
    """
    Create an androwarn report object class:'AndrowarnReport'.

    :param android_app: str - Android app object
    :param results: str - androwarn report file path
    :param scan_status: str - scan status

    :return class:'AndrowarnReport'

    """
    from androwarn import androwarn
    logging.error(f"Storing androwarn {android_app.id} report")
    androwarn_report = AndrowarnReport(scanner_version=androwarn.VERSION,
                                       scanner_name="Androwarn",
                                       android_app_id_reference=android_app.id,
                                       results=results,
                                       scan_status=scan_status,
                                       )
    androwarn_report.save()
    android_app.apk_scanner_report_reference_list.append(androwarn_report)
    android_app.save()


def parse_json_report(report_file_path):
    """
    Parse androwarn report and return analysis result.

    :param report_file_path: str file path to androwarn report json file.
    :return: str - androwarn report object

    """
    with open(report_file_path, 'r') as json_file:
        data = json.load(json_file)
        if data and len(data) > 0:
            analysis_result = data[1].get("analysis_results")
            if not analysis_result and len(analysis_result) != 9:
                raise ValueError("Could not parse androwarn json: analysis_results empty or len not == 9.")
        else:
            raise ValueError("Could not parse androwarn json")
    return analysis_result


class AndrowarnScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.Androwarn.androwarn_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/androwarn/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_db_context
    @create_apk_scanner_log_context
    def start_scan(self):
        """
        Starts multiple instances of the scanner to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Androwarn analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=androwarn_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
