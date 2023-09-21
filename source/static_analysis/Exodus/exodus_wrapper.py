# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
from database.query_document import get_filtered_list
from model import ExodusReport, AndroidApp
from context.context_creator import create_db_context
from utils.mulitprocessing_util.mp_util import start_python_interpreter

EXODUS_VERSION = "1.3.8"


@create_db_context
def start_exodus_scan(android_app_id_list):
    """
    Analysis all apps from the given list with exodus-core.

    :param android_app_id_list: list of class:'AndroidApp' object-ids.

    """
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "exodus_report_reference")
    logging.info(f"Exodus after filter: {str(len(android_app_list))}")
    if len(android_app_list) > 0:
        start_python_interpreter(android_app_list, exodus_worker, os.cpu_count())


def exodus_worker(android_app_id_queue):
    """
    Start the analysis with exodus on a multiprocessor queue.

    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.

    """
    while True:
        android_app_id = android_app_id_queue.get(timeout=.5)
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"Exodus scans: {android_app.id}")
        try:
            exodus_json_report = get_exodus_analysis(android_app.absolute_store_path)
            create_report(android_app, exodus_json_report)
        except Exception as err:
            logging.error(f"Exodus could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")
        android_app_id_queue.task_done()


def get_exodus_analysis(apk_file_path):
    """
    Analyses one apk with exodus and creates a json report.

    :param apk_file_path: str - path to the apk file.
    :return: dict - exodus results as json.

    """
    from exodus_core.analysis.static_analysis import StaticAnalysis

    class AnalysisHelper(StaticAnalysis):
        def create_json_report(self):
            return {
                'application': {
                    'handle': self.get_package(),
                    'version_name': self.get_version(),
                    'version_code': self.get_version_code(),
                    'uaid': self.get_application_universal_id(),
                    'name': self.get_app_name(),
                    'permissions': self.get_permissions(),
                    'libraries': [l for l in self.get_libraries()],
                },
                'apk': {
                    'path': self.apk_path,
                    'checksum': self.get_sha256(),
                },
                'trackers': [
                    {'name': t.name, 'id': t.id} for t in self.detect_trackers()
                ],
            }

    analysis = AnalysisHelper(apk_file_path)
    analysis.load_trackers_signatures()
    return analysis.create_json_report()


def create_report(android_app, exodus_results):
    """
    Create a exodus report in the database.

    :param android_app: class:'AndroidApp'
    :param exodus_results: dict - results of the exodus scan.

    """
    #TODO add dynamic usage for version
    #from exodus_core import __version__
    exodus_report = ExodusReport(
        android_app_id_reference=android_app.id,
        exodus_version=EXODUS_VERSION,
        results=exodus_results
    ).save()
    android_app.exodus_report_reference = exodus_report.id
    android_app.save()
