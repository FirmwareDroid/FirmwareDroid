import json
import logging
import os
import shlex
import subprocess
import tempfile
from pathlib import Path

from model import AndroidApp, SuperReport
from scripts.database.query_document import get_filtered_list
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool


def start_super_android_analyzer_scan(android_app_id_list):
    """
    Analysis all apps from the given list with super android analyzer.
    :param android_app_id_list: list of class:'AndroidApp' object-ids.
    """
    create_app_context()
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "super_report_reference")
    logging.info(f"Super after filter: {str(len(android_app_list))}")
    if len(android_app_list) > 0:
        start_process_pool(android_app_list, super_android_analyzer_worker, os.cpu_count())


def super_android_analyzer_worker(android_app_id_queue):
    """
    Start the analysis with super on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while not android_app_id_queue.empty():
        android_app_id = android_app_id_queue.get()
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"SUPER Android Analyzer scans: {android_app.id}")
        try:
            tempdir = tempfile.TemporaryDirectory()
            super_json_results = get_super_android_analyzer_analysis(android_app.absolute_store_path, tempdir.name)
            create_report(android_app, super_json_results)
        except Exception as err:
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
        ValueError("Could not find scanning result json.")
    return json.loads(open(result_file_path).read())


def create_report(android_app, super_json_results):
    """
    Create a class:'SuperReport' and save the super android analyzer scan results in the database.
    :param android_app: class:'AndroidApp' - app that was scanned with super.
    :param super_json_results: str - super scanning result in json format.
    :return: class:'SuperReport'
    """
    super_report = SuperReport(android_app_id_reference=android_app.id,
                               results=super_json_results).save()
    return super_report