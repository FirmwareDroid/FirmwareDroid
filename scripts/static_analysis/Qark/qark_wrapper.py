# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import collections
import logging
import os
import tempfile
import json
import flask
from scripts.database.query_document import get_filtered_list
from model import QarkReport, QarkIssue, AndroidApp
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool


def qark_analyse_apps(android_app_id_list):
    """
    Analysis all apps from the given firmware list with qark.
    :param android_app_id_list: list of class:'AndroidApp' object-id's
    """
    create_app_context()
    logging.info(f"Qark analysis started! With {str(len(android_app_id_list))} apps")
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "qark_report_reference")
    logging.info(f"Qark after filter: {str(len(android_app_list))}")
    if len(android_app_list) > 0:
        start_process_pool(android_app_list, qark_worker, os.cpu_count())


def qark_worker(android_app_id_queue):
    """
    Starts the analysis with quark.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while not android_app_id_queue.empty():
        android_app_id = android_app_id_queue.get()
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"Qark scans: {android_app.filename} {android_app.id} "
                     f"estimated queue-size: {android_app_id_queue.qsize()}")
        try:
            report_path = start_qark_app_analysis(android_app)
            create_qark_report(report_path, android_app)
        except Exception as err:
            logging.error(f"Could not analyze app {android_app.id} {android_app.filename} with qark: {err}")


def start_qark_app_analysis(android_app):
    """
    Runs qark apk analysis.
    :param android_app: class:'AndroidApp' the app to be scanned.
    """
    from qark.decompiler.decompiler import Decompiler
    from qark.report import Report
    from qark.scanner.scanner import Scanner

    build_path = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"])
    source = android_app.absolute_store_path
    report_type = "json"

    logging.info("Decompiling...")
    decompiler = Decompiler(path_to_source=source, build_directory=build_path.name)
    decompiler.run()

    logging.info("Running scans...")
    path_to_source = decompiler.path_to_source if decompiler.source_code else decompiler.build_directory

    scanner = Scanner(manifest_path=decompiler.manifest_path, path_to_source=path_to_source)
    scanner.run()
    logging.info("Finish scans...")

    report = Report(issues=set(scanner.issues))
    report_path = report.generate(file_type=report_type)
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
                                 android_app_id_reference=android_app.id)
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
