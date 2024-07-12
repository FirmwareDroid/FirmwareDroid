# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import collections
import logging
import os
import tempfile
import json
from model.Interfaces.ScanJob import ScanJob
from model import QarkReport, QarkIssue, AndroidApp
from context.context_creator import create_db_context, create_log_context
from utils.mulitprocessing_util.mp_util import start_python_interpreter

@create_log_context
@create_db_context
def qark_worker_multiprocessing(android_app_id):
    """
    Starts the analysis with quark.

    :param android_app_id: str: the id of the app to be scanned.

    """
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"Qark scans: {android_app.filename} {android_app.id} ")
        report_path = start_qark_app_analysis(android_app)
        create_qark_report(report_path, android_app)
    except Exception as err:
        logging.error(f"Could not analyze app {android_app_id} with qark: {err}")


def start_qark_app_analysis(android_app):
    """
    Runs qark apk analysis.
    :param android_app: class:'AndroidApp' the app to be scanned.
    """
    from qark.decompiler.decompiler import Decompiler
    from qark.report import Report
    from qark.scanner.scanner import Scanner

    with tempfile.TemporaryDirectory() as build_path:
        source = android_app.absolute_store_path

        try:
            logging.info("Decompiling...")
            decompiler = Decompiler(path_to_source=source, build_directory=build_path)
            decompiler.run()

            logging.info("Running scans...")
            path_to_source = decompiler.path_to_source if decompiler.source_code else decompiler.build_directory

            scanner = Scanner(manifest_path=decompiler.manifest_path, path_to_source=path_to_source)
            scanner.run()
            logging.info("Finish scans...")

            report = Report(issues=set(scanner.issues))
            report_type = "json"
            report_path = report.generate(file_type=report_type)
        except SystemExit as err:
            logging.error(err)
            raise SystemExit(f"Qark could not scan {android_app.filename} because: {err}")

    return report_path


def create_qark_report(report_file_path, android_app):
    """
    Creates a qark report db object (class:'QarkReport')
    :param report_file_path: the path to the json file to be stored in the database.
    :param android_app: class:'AndroidApp'.
    """
    logging.info("Create qark report for " + report_file_path)
    with open(report_file_path, 'rb') as report_file:
        qark_report = QarkReport(report_file_json=report_file,
                                 android_app_id_reference=android_app.id,
                                 scanner_name="Qark",
                                 scanner_version="4.0.0")
        create_qark_issue_list(qark_report, report_file_path, android_app)
        qark_report.save()
    android_app.qark_report_reference = qark_report.id
    android_app.save()
    return qark_report


def create_qark_issue_list(qark_report, report_file_path, android_app):
    """
    Parses all issues from the qark report and creates a class:'QarkIssue' list.
    :param qark_report: class:'QarkReport' the report to which the qark issues will be added.
    :param report_file_path: the path to the qark report.json file.
    :param android_app: class:'AndroidApp'
    """
    qark_report.issue_list = []
    with open(report_file_path, 'r') as report_file:
        data = json.load(report_file)
        if data:
            for issue in data:
                category = issue.get("category")
                severity = issue.get("severity")
                description = issue.get("description")
                name = issue.get("name")
                line_number = issue.get("line_number")
                line_number_list = []
                if not isinstance(line_number, collections.Iterable):
                    line_number_list.append(line_number)
                else:
                    line_number_list.extend(line_number)
                file_object = issue.get("file_object")
                apk_exploit_dict = issue.get("apk_exploit_dict")
                if not apk_exploit_dict:
                    apk_exploit_dict = {}

                qark_issue = QarkIssue(qark_report_reference=qark_report.id,
                                       android_app_id_reference=android_app.id,
                                       category=category,
                                       severity=severity,
                                       description=description,
                                       name=name,
                                       line_number_list=line_number_list,
                                       file_object=file_object,
                                       apk_exploit_dict=apk_exploit_dict)
                qark_issue.save()
                qark_report.issue_list.append(qark_issue.id)


class QarkScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.Qark.qark_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/qark/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of AndroGuard to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Qark analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=qark_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="qark_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
