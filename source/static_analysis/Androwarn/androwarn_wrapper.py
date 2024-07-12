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
from context.context_creator import create_db_context, create_log_context
from processing.standalone_python_worker import start_python_interpreter

lock = Lock()


@create_log_context
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

    android_app = AndroidApp.objects.get(pk=android_app_id)
    logging.info(f"Androwarn scan: {android_app.filename} {android_app.id} ")
    try:
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
        create_androwarn_report(report_file_path, android_app)
    except Exception as err:
        logging.error(f"Androwarn could not scan app {android_app.filename} id: {android_app.id} - "
                      f"error: {str(err)}")


def create_androwarn_report(report_file_path, android_app):
    """
    Create an androwarn report object class:'AndrowarnReport'.

    :param report_file_path: str file path to Androwarn report json file.
    :param android_app: class:'AndroidApp'
    :return class:'AndrowarnReport'

    """
    from androwarn import androwarn
    analysis_result = parse_json_report(report_file_path)
    with open(report_file_path, 'rb') as report_file:
        androwarn_report = AndrowarnReport(report_file_json=report_file,
                                           scanner_version=androwarn.VERSION,
                                           scanner_name="Androwarn",
                                           android_app_id_reference=android_app.id,
                                           telephony_identifiers_leakage=analysis_result[0][1],
                                           device_settings_harvesting=analysis_result[1][1],
                                           location_lookup=analysis_result[2][1],
                                           connection_interfaces_exfiltration=analysis_result[3][1],
                                           telephony_services_abuse=analysis_result[4][1],
                                           audio_video_eavesdropping=analysis_result[5][1],
                                           suspicious_connection_establishment=analysis_result[6][1],
                                           PIM_data_leakage=analysis_result[7][1],
                                           code_execution=analysis_result[8][1])
        androwarn_report.save()
        android_app.androwarn_report_reference = androwarn_report.id
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

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_db_context
    @create_log_context
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
                                                      report_reference_name="androwarn_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
