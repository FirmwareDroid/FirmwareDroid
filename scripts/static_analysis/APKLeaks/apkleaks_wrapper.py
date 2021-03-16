import logging
import os
import tempfile

from model import AndroidApp, ApkLeaksReport
from scripts.database.query_document import get_filtered_list
from scripts.rq_tasks.flask_context_creator import create_app_context
from scripts.utils.mulitprocessing_util.mp_util import start_process_pool


def start_apkleaks_scan(android_app_id_list):
    """
    Analysis all apps from the given list with APKLeaks.
    :param android_app_id_list: list of class:'AndroidApp' object-ids.
    """
    create_app_context()
    android_app_list = get_filtered_list(android_app_id_list, AndroidApp, "apkleaks_report_reference")
    logging.info(f"APKLeaks after filter: {str(len(android_app_list))}")
    if len(android_app_list) > 0:
        start_process_pool(android_app_list, apkleaks_worker, os.cpu_count())


def apkleaks_worker(android_app_id_queue):
    """
    Start the analysis with super on a multiprocessor queue.
    :param android_app_id_queue: multiprocessor queue with object-ids of class:'AndroidApp'.
    """
    while not android_app_id_queue.empty():
        android_app_id = android_app_id_queue.get()
        android_app = AndroidApp.objects.get(pk=android_app_id)
        logging.info(f"APKLeaks scans: {android_app.id}")
        try:
            tempdir = tempfile.TemporaryDirectory()
            json_results = get_apkleaks_analysis(android_app.absolute_store_path, tempdir.name)
            create_report(android_app, json_results)
        except Exception as err:
            logging.error(f"Super could not scan app {android_app.filename} id: {android_app.id} - "
                          f"error: {err}")


def get_apkleaks_analysis(apk_file_path, result_folder_path):
    """
    Scans an apk with the apkleaks.
    :param apk_file_path: str - path to the apk file.
    :param result_folder_path: str - path to the folder where the result report is saved.
    :return: str - scan result as json.
    """
    # TODO IMPLEMENT METHOD - SCAN WITH APKLEAKS
    raise NotImplemented
    return


def create_report(android_app, json_results):
    """
    Create a class:'APKLeaksReport' and save the super android analyzer scan results in the database.
    :param android_app: class:'AndroidApp' - app that was scanned with super.
    :param json_results: str - super scanning result in json format.
    :return: class:'SuperReport'
    """
    apkleaks_report = ApkLeaksReport(android_app_id_reference=android_app.id,
                                     apkleaks_version="",
                                     results=json_results).save()
    return apkleaks_report
