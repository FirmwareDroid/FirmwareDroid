# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import logging
import os
from model.Interfaces.ScanJob import ScanJob
from model import ExodusReport, AndroidApp
from context.context_creator import create_db_context, create_log_context
from processing.standalone_python_worker import start_python_interpreter


@create_log_context
@create_db_context
def exodus_worker_multiprocessing(android_app_id):
    """
    Start the analysis with exodus on a multiprocessor queue.

    :param android_app_id: str - id of the android app to be analysed.

    """
    android_app = AndroidApp.objects.get(pk=android_app_id)
    logging.info(f"Exodus scans: {android_app.id}")
    try:
        exodus_json_report = get_exodus_analysis(android_app.absolute_store_path)
        create_report(android_app, exodus_json_report)
    except Exception as err:
        logging.error(f"Exodus could not scan app {android_app.filename} id: {android_app.id} - "
                      f"error: {err}")


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
    # TODO add dynamic usage for version
    # from exodus_core import __version__
    exodus_report = ExodusReport(
        android_app_id_reference=android_app.id,
        scanner_version="1.3.9",
        scanner_name="Exodus",
        results=exodus_results
    ).save()
    android_app.exodus_report_reference = exodus_report.id
    android_app.save()


class ExodusScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.Exodus.exodus_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/exodus/bin/python"

    def __init__(self, object_id_list):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of the scanner to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"Exodus analysis started! With {str(len(android_app_id_list))} apps.")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=exodus_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      report_reference_name="exodus_report_reference",
                                                      interpreter_path=self.INTERPRETER_PATH)
            python_process.wait()
