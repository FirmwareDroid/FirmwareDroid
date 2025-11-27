# -*- coding: utf-8 -*-
# This file is part of FirmwareDroid - https://github.com/FirmwareDroid/FirmwareDroid/blob/main/LICENSE.md
# See the file 'LICENSE' for copying permission.
import json
import os
import logging
import tempfile
import traceback
from model.Interfaces.ScanJob import ScanJob
from model import ApkidReport, AndroidApp
from context.context_creator import create_db_context, create_log_context, setup_apk_scanner_logger
from processing.standalone_python_worker import start_python_interpreter
from typing import List, Optional


def find_files(root_dir: str, target_filename: str, max_results: Optional[int] = None) -> List[str]:
    """
    Walk `root_dir` and return a list of full paths to files named `target_filename`.
    Set `max_results` to stop early (useful for large trees).
    """
    matches: List[str] = []
    for dirpath, _, files in os.walk(root_dir):
        if target_filename in files:
            matches.append(os.path.join(dirpath, target_filename))
            if max_results is not None and len(matches) >= max_results:
                break
    return matches


def process_android_app(android_app):
    """
    Scans an Android app with the APKiD scanner and stores the results in the database.

    :param android_app: class:'AndroidApp'

    """
    LOGGER = setup_apk_scanner_logger()
    logging.info(f"Processing Android app with APKiD: {android_app.id}")
    try:
        from apkid.apkid import Options, Scanner
        LOGGER.info(f"APKid Scans app: {android_app.filename} id: {android_app.id}", extra={'ip': '127.0.0.1'})
        with tempfile.TemporaryDirectory() as output_dir:
            if not os.path.exists(output_dir):
                raise OSError(f"Could not create temp dir for apkid: {output_dir}")
            options = Options(
                timeout=600,
                verbose=True,
                json=True,
                output_dir=output_dir,
                typing='magic',
                entry_max_scan_size=0,
                scan_depth=20,
                recursive=False,
                include_types=True
            )
            rules = options.rules_manager.load()
            scanner = Scanner(rules, options)
            scanner.scan(android_app.absolute_store_path)
            matches = find_files(output_dir, android_app.filename)
            if matches and len(matches) == 1:
                report_file_path = matches[0]
            else:
                raise FileNotFoundError(
                    f"APKid ERROR: Could not find report: "
                    f"{android_app.filename} id: {android_app.id}"
                )
            with open(report_file_path, 'r') as json_file:
                results = json.load(json_file)
                store_result(android_app, results=results, scan_status="completed")
        LOGGER.info(f"APKid completed for app: {android_app.filename} id: {android_app.id}")
    except Exception as err:
        LOGGER.error(f"APKid Scan failed. ERROR: {err}")
        if android_app:
            LOGGER.error(f"APKid Scan failed. ERROR for app: {android_app.filename} id: {android_app.id} - {err}")
            try:
                store_result(android_app, results={"error": f"{err}"}, scan_status="failed")
            except Exception as err2:
                pass


@create_db_context
def apkid_worker_multiprocessing(android_app_id):
    """
    Starts to analyze the given android apps with apkid tool.

    :param android_app_id: str - object-id for document of  class:'AndroidApp'

    """
    logging.debug(f"APKiD sub-process worker started for app id: {android_app_id}")
    try:
        android_app = AndroidApp.objects.get(pk=android_app_id)
        process_android_app(android_app)
    except Exception as err:
        logging.error(err)
        traceback.print_exc()


def store_result(android_app, results, scan_status):
    """
    Creates and APKiD report.

    :param android_app: class:'AndroidApp'
    :param results: dict - results from the apkid scan
    :param scan_status: str - status of the scan (completed, failed)

    :return: class:'ApkidReport'

    """
    import apkid
    apkid_report = ApkidReport(android_app_id_reference=android_app.id,
                               scanner_version=apkid.__version__,
                               scanner_name="APKiD",
                               scan_status=scan_status,
                               results=results)
    apkid_report.save()
    android_app.apk_scanner_report_reference_list.append(apkid_report)
    android_app.save()
    return apkid_report


class APKiDScanJob(ScanJob):
    object_id_list = []
    SOURCE_DIR = "/var/www/source"
    MODULE_NAME = "static_analysis.APKiD.apkid_wrapper"
    INTERPRETER_PATH = "/opt/firmwaredroid/python/apkid/bin/python"

    def __init__(self, object_id_list, **kwargs):
        self.object_id_list = object_id_list
        os.chdir(self.SOURCE_DIR)

    @create_log_context
    @create_db_context
    def start_scan(self):
        """
        Starts multiple instances of the scanner to analyse a list of Android apps on multiple processors.
        """
        android_app_id_list = self.object_id_list
        logging.info(f"APKiD analysis started! With {str(len(android_app_id_list))} apps. ID List: {android_app_id_list}")
        if len(android_app_id_list) > 0:
            python_process = start_python_interpreter(item_list=android_app_id_list,
                                                      worker_function=apkid_worker_multiprocessing,
                                                      number_of_processes=os.cpu_count(),
                                                      use_id_list=True,
                                                      module_name=self.MODULE_NAME,
                                                      interpreter_path=self.INTERPRETER_PATH
                                                      )
            python_process.wait()
        else:
            logging.warning("No Android apps to analyse with APKiD.")
        logging.info("APKiD analysis completed.")