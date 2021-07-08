# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import os
import logging
import tempfile
import flask
from scripts.database.query_document import get_filtered_list
from model import ApkidReport, AndroidApp
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool


def start_apkid_scan(android_app_id_list):
    """
    RQ-Task wrapper for apkid tool.
    :param android_app_id_list: list of class:'AndroidApp' object-ids
    """
    create_app_context()
    logging.info(f"APKid before filtering: {str(len(android_app_id_list))} app id's")
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "apkid_report_reference")
    logging.info(f"APKid Analysis started! With {str(len(android_app_list))} apps")
    if len(android_app_list) > 0:
        start_process_pool(android_app_list, apkid_scan, number_of_processes=os.cpu_count(), use_id_list=True)
    else:
        logging.warning("No Android apps to scan with apkid!")


def apkid_scan(android_app_id_queue):
    """
    Starts to analyze the given android apps with apkid tool.
    :param android_app_id_queue: multiprocessor queue with object-id's of class:'AndroidApp'.
    """
    from apkid.apkid import Options, Scanner
    while not android_app_id_queue.empty():
        android_app_id = android_app_id_queue.get()
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"APKid scans app: {android_app.filename} "
                     f"id: {android_app.id} "
                     f"queue estimate: {str(android_app_id_queue.qsize())}")

        try:
            output_dir = tempfile.TemporaryDirectory(dir=flask.current_app.config["FIRMWARE_FOLDER_CACHE"],
                                                     suffix="_apkid")
            if not os.path.exists(output_dir.name):
                raise OSError(f"Could not create temp dir for apkid: {str(output_dir.name)}")
            options = Options(timeout=600,
                              verbose=True,
                              json=True,
                              output_dir=output_dir.name,
                              typing='magic',
                              entry_max_scan_size=0,
                              scan_depth=20,
                              recursive=False,
                              include_types=True)
            rules = options.rules_manager.load()
            scanner = Scanner(rules, options)

            scanner.scan(android_app.absolute_store_path)
            is_report_saved = False
            for dirpath, dirnames, filenames in os.walk(output_dir.name):
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
                                   apkid_version=apkid.__version__,
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
    :return:
    """
    with open(report_file_path, 'r') as json_file:
        data = json.load(json_file)
        if data and len(data) > 0:
            apkid_report.apkid_version = data.get("apkid_version")
            apkid_report.rules_sha256 = data.get("rules_sha256")
            apkid_report.files = data.get("files")
